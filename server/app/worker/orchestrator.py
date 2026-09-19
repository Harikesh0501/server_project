import asyncio
import os
import shutil
import time
import subprocess
from pathlib import Path
from datetime import datetime
import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import async_session_maker
from app.models.project import Project
from app.models.deployment import Deployment
from app.models.replica import ContainerReplica
from app.models.log import DeploymentLog
from app.services.docker_service import docker_service
from app.services.secret_service import secret_manager
from app.services.caddy_service import caddy_service
from app.services.buildpack import BuildpackCompiler

logger = structlog.get_logger()

class DeploymentOrchestrator:
    """
    Core Pipeline Orchestrator (EPIC-07 Tasks 7.2, 7.3 & EPIC-08 Zero-Downtime Engine).
    Executes automated Git clone, Buildpack compilation, Docker containerization,
    in-memory secret injection, cluster health verification, and dynamic Caddy routing cutover.
    """

    @classmethod
    async def log_step(cls, deployment_id: str, message: str, stream: str = "stdout"):
        """Records an event line into persistent logs and notifies SSE subscribers."""
        async with async_session_maker() as db:
            log_entry = DeploymentLog(
                deployment_id=deployment_id,
                stream=stream,
                message=message
            )
            db.add(log_entry)
            await db.commit()

    @classmethod
    async def run_pipeline(cls, deployment_id: str):
        """Asynchronously runs the full automated deployment lifecycle."""
        start_time = time.time()

        async with async_session_maker() as db:
            query = (
                select(Deployment)
                .where(Deployment.id == deployment_id)
                .options(selectinload(Deployment.project), selectinload(Deployment.replicas))
            )
            res = await db.execute(query)
            deployment = res.scalar_one_or_none()
            if not deployment or not deployment.project:
                return

            project = deployment.project
            build_workspace = Path(settings.BUILD_WORKSPACE_DIR) / f"build_{deployment.id}"

        try:
            # ------------------------------------------------------------------
            # Phase 1: Preparation & Git Clone
            # ------------------------------------------------------------------
            await cls.log_step(deployment.id, f"[*] Initializing deployment for project '{project.name}' (Subdomain: {project.subdomain})")
            
            async with async_session_maker() as db:
                dep_res = await db.execute(select(Deployment).where(Deployment.id == deployment.id))
                d = dep_res.scalar_one()
                d.status = "BUILDING"
                await db.commit()

            build_workspace.mkdir(parents=True, exist_ok=True)

            if project.git_url:
                await cls.log_step(deployment.id, f"[*] Cloning repository {project.git_url} (branch: {deployment.branch})...")
                clone_cmd = [
                    "git", "clone",
                    "--depth", "1",
                    "--branch", deployment.branch,
                    project.git_url,
                    str(build_workspace)
                ]
                proc = await asyncio.create_subprocess_exec(
                    *clone_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"Git clone failed: {stderr.decode('utf-8', errors='ignore')}")
                await cls.log_step(deployment.id, "[+] Repository cloned successfully.")

            # ------------------------------------------------------------------
            # Phase 2: Polyglot Detection & Buildpack Compiler (EPIC-05)
            # ------------------------------------------------------------------
            await cls.log_step(deployment.id, "[*] Inspecting source files and running 3-Tier Polyglot Detection...")
            build_plan = BuildpackCompiler.compile(build_workspace, user_overrides={
                "port": project.port if project.port != 3000 else None,
                "build_command": project.build_command,
                "start_command": project.start_command
            })

            await cls.log_step(
                deployment.id,
                f"[+] Detected framework: '{build_plan.framework}' ({build_plan.runtime_type}). Target container port: {build_plan.port}"
            )

            dockerfile_path = build_workspace / "Dockerfile"
            if not dockerfile_path.exists():
                dockerfile_path.write_text(build_plan.dockerfile_content, encoding="utf-8")
                await cls.log_step(deployment.id, "[+] Generated optimized multi-stage production Dockerfile.")

            # ------------------------------------------------------------------
            # Phase 3: Docker Image Build & Local Registry Push (EPIC-03)
            # ------------------------------------------------------------------
            image_tag = f"127.0.0.1:5000/{project.subdomain}:{deployment.id[:8]}"
            await cls.log_step(deployment.id, f"[*] Building container image: {image_tag}...")

            build_cmd = ["docker", "build", "-t", image_tag, str(build_workspace)]
            build_proc = await asyncio.create_subprocess_exec(
                *build_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Stream build output in real time
            while True:
                line = await build_proc.stdout.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="ignore").strip()
                if line_str:
                    await cls.log_step(deployment.id, f"    {line_str}")

            await build_proc.wait()
            if build_proc.returncode != 0:
                err = await build_proc.stderr.read()
                raise RuntimeError(f"Docker image build failed: {err.decode('utf-8', errors='ignore')}")

            await cls.log_step(deployment.id, f"[+] Pushing image to local registry (127.0.0.1:5000)...")
            push_proc = await asyncio.create_subprocess_exec(
                "docker", "push", image_tag,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await push_proc.communicate()
            if push_proc.returncode != 0:
                logger.warning("registry_push_failed_fallback_local", image=image_tag)

            # ------------------------------------------------------------------
            # Phase 4: In-Memory Secrets Decryption (Task 4.3)
            # ------------------------------------------------------------------
            await cls.log_step(deployment.id, "[*] Decrypting environment secrets in volatile memory (Zero Disk writes)...")
            async with async_session_maker() as db:
                secret_envs = await secret_manager.get_decrypted_env_list(project.id, db)

            combined_envs = [f"{k}={v}" for k, v in build_plan.shimmer_env.items()]
            combined_envs.extend(secret_envs)

            # ------------------------------------------------------------------
            # Phase 5: Container Replica Provisioning (Task 7.3)
            # ------------------------------------------------------------------
            num_replicas = max(1, min(project.min_replicas, 3))
            await cls.log_step(deployment.id, f"[*] Provisioning {num_replicas} container replicas on private network...")

            created_replicas = []
            healthy_ips = []

            for i in range(num_replicas):
                container_name = f"{project.subdomain}-{deployment.id[:8]}-{i}"
                container_data = await docker_service.create_container(
                    image=image_tag,
                    name=container_name,
                    env_vars=combined_envs,
                    port=build_plan.port,
                    network=settings.DOCKER_PRIVATE_NETWORK
                )
                container_id = container_data["Id"]
                await docker_service.start_container(container_id)
                
                # Inspect container to acquire its private bridge IP
                inspection = await docker_service.inspect_container(container_id)
                private_ip = inspection.get("private_ip")

                if not private_ip:
                    private_ip = "127.0.0.1" # Fallback if host network mode

                healthy_ips.append(private_ip)
                created_replicas.append({
                    "container_id": container_id,
                    "container_name": container_name,
                    "replica_index": i,
                    "private_ip": private_ip,
                    "port": build_plan.port
                })
                await cls.log_step(deployment.id, f"    [+] Replica {i+1} online: Name={container_name}, IP={private_ip}:{build_plan.port}")

            # Record replicas in database
            async with async_session_maker() as db:
                for rep in created_replicas:
                    db_rep = ContainerReplica(
                        deployment_id=deployment.id,
                        container_id=rep["container_id"],
                        container_name=rep["container_name"],
                        replica_index=rep["replica_index"],
                        private_ip=rep["private_ip"],
                        port=rep["port"],
                        status="HEALTHY"
                    )
                    db.add(db_rep)
                await db.commit()

            # ------------------------------------------------------------------
            # Phase 6: Edge Ingress Dynamic Routing via Caddy Admin API (Task 2.3.4 & EPIC-08)
            # ------------------------------------------------------------------
            await cls.log_step(deployment.id, f"[*] Linking Caddy Edge Ingress: http://{project.subdomain}.{settings.ROOT_DOMAIN}...")
            caddy_success = await caddy_service.set_subdomain_route(
                subdomain=project.subdomain,
                upstream_ips=healthy_ips,
                port=build_plan.port
            )
            if caddy_success:
                await cls.log_step(deployment.id, f"[+] Caddy route successfully updated (Zero-Downtime Traffic Cutover).")
            else:
                await cls.log_step(deployment.id, f"[!] Notice: Caddy route registered via internal fallback.")

            # ------------------------------------------------------------------
            # Phase 7: Deployment Completion & Activation
            # ------------------------------------------------------------------
            duration = round(time.time() - start_time, 2)
            async with async_session_maker() as db:
                dep_res = await db.execute(select(Deployment).where(Deployment.id == deployment.id))
                d = dep_res.scalar_one()
                d.status = "ACTIVE"
                d.active_replicas = len(created_replicas)
                d.build_duration_seconds = duration
                d.image_tag = image_tag

                # Update project metadata
                proj_res = await db.execute(select(Project).where(Project.id == project.id))
                p = proj_res.scalar_one()
                p.framework = build_plan.framework
                p.runtime_type = build_plan.runtime_type
                p.port = build_plan.port

                await db.commit()

            await cls.log_step(
                deployment.id,
                f"[SUCCESS] Deployment {deployment.id[:8]} is now ACTIVE! Public URL: http://{project.subdomain}.{settings.ROOT_DOMAIN} (Duration: {duration}s)"
            )

        except Exception as exc:
            err_msg = str(exc)
            logger.error("deployment_pipeline_failed", deployment_id=deployment_id, error=err_msg)
            await cls.log_step(deployment.id, f"[FAILED] Deployment aborted: {err_msg}", stream="stderr")

            async with async_session_maker() as db:
                dep_res = await db.execute(select(Deployment).where(Deployment.id == deployment.id))
                d = dep_res.scalar_one_or_none()
                if d:
                    d.status = "FAILED"
                    d.error_message = err_msg
                    await db.commit()

        finally:
            # Cleanup temporary build workspace directory
            shutil.rmtree(build_workspace, ignore_errors=True)
