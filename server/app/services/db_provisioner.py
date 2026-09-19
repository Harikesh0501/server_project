import os
import gzip
import shutil
import secrets
import asyncio
from pathlib import Path
from datetime import datetime, timezone
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.models.project import Project
from app.models.database import ManagedDatabase
from app.services.docker_service import docker_service
from app.services.secret_service import secret_manager

logger = structlog.get_logger()

class DatabaseProvisionerService:
    """
    Render-Style Managed Database Provisioning Engine (EPIC-10).
    Provisions isolated PostgreSQL 16 and Redis 7 containers on deploy-private-net,
    configures persistent volumes, generates AES-256-GCM encrypted secrets,
    and handles automated backups and restore workflows.
    """

    @classmethod
    def generate_secure_password(cls, length: int = 32) -> str:
        """Generates a cryptographically strong alphanumeric password (Mini-Task 10.1.2)."""
        return secrets.token_urlsafe(length)[:length]

    @classmethod
    async def provision_database(
        cls,
        name: str,
        engine: str,
        project_id: str,
        version: str = "16",
        db_session: AsyncSession | None = None
    ) -> ManagedDatabase:
        """
        Full lifecycle database provisioning workflow:
        1. Validates project existence.
        2. Sets up isolated persistent storage directory (chmod 700).
        3. Spawns isolated container attached to deploy-private-net.
        4. Verifies database operational readiness via pg_isready / redis-cli ping.
        5. Encrypts connection string and auto-injects into project environment secrets.
        """
        async def _run(db: AsyncSession):
            # 1. Verify project
            p_res = await db.execute(select(Project).where(Project.id == project_id))
            project = p_res.scalar_one_or_none()
            if not project:
                raise ValueError(f"Project {project_id} not found.")

            # 2. Initialize Database record
            clean_name = name.lower().strip().replace(" ", "-")
            db_record = ManagedDatabase(
                project_id=project_id,
                name=clean_name,
                engine=engine.lower(),
                version=version,
                port=5432 if engine.lower() == "postgres" else 6379,
                database_name=clean_name.replace("-", "_") if engine.lower() == "postgres" else "0",
                username="postgres" if engine.lower() == "postgres" else "default",
                status="PROVISIONING"
            )
            db.add(db_record)
            await db.commit()
            await db.refresh(db_record)

            db_id = db_record.id
            db_dir = Path(settings.DATA_DIR) / "databases" / db_id / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            if os.name != "nt":
                os.chmod(db_dir, 0o700)

            password = cls.generate_secure_password()
            container_name = f"{'pg' if engine.lower() == 'postgres' else 'redis'}-{db_record.name}-{db_id[:8]}"

            # 3. Provision target container engine
            try:
                if engine.lower() == "postgres":
                    # Task 10.2: PostgreSQL 16 Isolated Provisioning
                    image = f"postgres:{version}-alpine" if version else "postgres:16-alpine"
                    await docker_service.pull_image(image)
                    envs = [
                        f"POSTGRES_USER={db_record.username}",
                        f"POSTGRES_DB={db_record.database_name}",
                        f"POSTGRES_PASSWORD={password}",
                        "PGDATA=/var/lib/postgresql/data/pgdata"
                    ]
                    binds = [f"{db_dir}:/var/lib/postgresql/data:rw"]
                    
                    c_data = await docker_service.create_container(
                        image=image,
                        name=container_name,
                        env_vars=envs,
                        port=5432,
                        network=settings.DOCKER_PRIVATE_NETWORK,
                        binds=binds
                    )
                    container_id = c_data["Id"]
                    await docker_service.start_container(container_id)

                    # Probe readiness with pg_isready
                    ready = False
                    for _ in range(15):
                        await asyncio.sleep(1.5)
                        try:
                            code, out = await docker_service.exec_run(
                                container_id,
                                ["pg_isready", "-U", db_record.username, "-d", db_record.database_name]
                            )
                            if code == 0:
                                ready = True
                                break
                        except Exception:
                            pass

                    if not ready:
                        raise RuntimeError("PostgreSQL service failed health probe (pg_isready).")

                    connection_url = f"postgresql://{db_record.username}:{password}@{container_name}:5432/{db_record.database_name}"
                    secret_key = "DATABASE_URL"

                else:
                    # Task 10.3: Redis 7 Isolated Provisioning
                    image = f"redis:{version}-alpine" if version else "redis:7-alpine"
                    await docker_service.pull_image(image)
                    binds = [f"{db_dir}:/data:rw"]
                    cmd = ["redis-server", "--requirepass", password, "--appendonly", "yes"]


                    c_data = await docker_service.create_container(
                        image=image,
                        name=container_name,
                        env_vars=[],
                        port=6379,
                        network=settings.DOCKER_PRIVATE_NETWORK,
                        binds=binds,
                        cmd=cmd
                    )
                    container_id = c_data["Id"]
                    await docker_service.start_container(container_id)

                    # Probe readiness with redis-cli ping
                    ready = False
                    for _ in range(10):
                        await asyncio.sleep(1.0)
                        try:
                            code, out = await docker_service.exec_run(
                                container_id,
                                ["redis-cli", "-a", password, "ping"]
                            )
                            if "PONG" in out:
                                ready = True
                                break
                        except Exception:
                            pass

                    if not ready:
                        raise RuntimeError("Redis service failed health probe (redis-cli ping).")

                    connection_url = f"redis://:{password}@{container_name}:6379/0"
                    secret_key = "REDIS_URL"

                # 4. In-Memory Zero-Trust Secret Auto-Injection (Task 10.4.2 & 10.4.3)
                secret_record = await secret_manager.set_secret(
                    project_id=project_id,
                    key=secret_key,
                    value=connection_url,
                    db=db
                )

                # 5. Finalize database state
                db_record.container_id = container_id
                db_record.status = "RUNNING"
                db_record.connection_url_secret_id = secret_record.id
                await db.commit()
                await db.refresh(db_record)

                logger.info(
                    "database_provisioned_successfully",
                    id=db_id,
                    name=db_record.name,
                    engine=engine,
                    container=container_name
                )
                return db_record

            except Exception as e:
                db_record.status = "FAILED"
                await db.commit()
                logger.error("database_provisioning_failed", id=db_id, error=str(e))
                raise

        if db_session:
            return await _run(db_session)
        else:
            async with async_session_maker() as db:
                return await _run(db)

    @classmethod
    async def create_backup(cls, database_id: str) -> dict:
        """
        Executes an on-demand database backup and stores compressed dump (Task 10.4.4).
        """
        async with async_session_maker() as db:
            query = select(ManagedDatabase).where(ManagedDatabase.id == database_id)
            res = await db.execute(query)
            db_record = res.scalar_one_or_none()
            if not db_record:
                raise ValueError(f"Managed database {database_id} not found.")

            if db_record.engine != "postgres":
                raise ValueError("Automated backup is currently supported for PostgreSQL databases.")

            backup_dir = Path(settings.DATA_DIR) / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{db_record.name}_{timestamp}.sql.gz"
            backup_path = backup_dir / filename

            # Execute pg_dump inside container
            code, sql_dump = await docker_service.exec_run(
                db_record.container_id,
                ["pg_dump", "-U", db_record.username, "-d", db_record.database_name]
            )
            if code != 0:
                raise RuntimeError(f"pg_dump failed: {sql_dump}")

            # Compress and write to backup path
            with gzip.open(backup_path, "wb") as f:
                f.write(sql_dump.encode("utf-8"))

            size_bytes = backup_path.stat().st_size

            logger.info("database_backup_created", database_id=database_id, filename=filename, size=size_bytes)
            return {
                "database_id": database_id,
                "backup_filename": filename,
                "backup_path": str(backup_path),
                "size_bytes": size_bytes,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

    @classmethod
    async def restore_database(cls, database_id: str, backup_filename: str) -> bool:
        """
        Restores a PostgreSQL database instance from a compressed backup file (Task 10.4.5).
        """
        async with async_session_maker() as db:
            res = await db.execute(select(ManagedDatabase).where(ManagedDatabase.id == database_id))
            db_record = res.scalar_one_or_none()
            if not db_record or not db_record.container_id:
                raise ValueError(f"Active database {database_id} not found.")

            backup_path = Path(settings.DATA_DIR) / "backups" / backup_filename
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file {backup_filename} not found.")

            # Decompress SQL dump
            with gzip.open(backup_path, "rb") as f:
                sql_content = f.read().decode("utf-8")

            # Write temporary sql file into container /tmp and execute psql
            code, out = await docker_service.exec_run(
                db_record.container_id,
                ["psql", "-U", db_record.username, "-d", db_record.database_name, "-c", sql_content]
            )
            if code != 0:
                raise RuntimeError(f"psql restore failed: {out}")

            logger.info("database_restored_successfully", database_id=database_id, file=backup_filename)
            return True

    @classmethod
    async def delete_database(cls, database_id: str) -> None:
        """Terminates container and removes database instance."""
        async with async_session_maker() as db:
            res = await db.execute(select(ManagedDatabase).where(ManagedDatabase.id == database_id))
            db_record = res.scalar_one_or_none()
            if not db_record:
                return

            if db_record.container_id:
                try:
                    await docker_service.stop_container(db_record.container_id, timeout=10)
                    await docker_service.remove_container(db_record.container_id)
                except Exception:
                    pass

            await db.delete(db_record)
            await db.commit()
            logger.info("database_deleted", id=database_id)

db_provisioner = DatabaseProvisionerService()
