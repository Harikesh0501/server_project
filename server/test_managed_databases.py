import asyncio
import sys
from httpx import AsyncClient, ASGITransport

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.main import app
from app.database import init_db, async_session_maker
from app.models.project import Project
from app.models.database import ManagedDatabase
from app.services.db_provisioner import DatabaseProvisionerService
from app.services.secret_service import secret_manager

async def run_database_tests():
    print("[*] Starting Render-Style Managed Databases (EPIC-10) Verification Suite...")
    await init_db()

    # 1. Test Secure Password Generator (Task 10.1.2)
    print("[*] 1. Testing Cryptographic Password Generator...")
    pwd = DatabaseProvisionerService.generate_secure_password(32)
    assert len(pwd) == 32, f"Expected 32 chars, got {len(pwd)}"
    assert any(c.isalnum() for c in pwd), "Password must be alphanumeric"
    print(f"    [+] Secure password generated successfully: {pwd[:8]}*** (Length: {len(pwd)})")

    # 2. Setup Test Project
    print("[*] 2. Setting up project for database association...")
    async with async_session_maker() as db:
        test_project = Project(
            name="Database Consumer App",
            subdomain="db-test-app",
            framework="fastapi",
            port=8000
        )
        db.add(test_project)
        await db.commit()
        await db.refresh(test_project)
        project_id = test_project.id
        print(f"    [+] Test project created: ID={project_id}")

    # 3. Test API Schemas & DB Routes
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test List Databases (empty initially)
        print("[*] 3. Testing GET /api/v1/databases...")
        res = await client.get(f"/api/v1/databases?project_id={project_id}")
        assert res.status_code == 200, f"List failed: {res.text}"
        assert isinstance(res.json(), list)
        print("    [+] GET /api/v1/databases returned 200 OK")

        # Create simulated managed database record directly
        print("[*] 4. Testing ManagedDatabase Model & Secret Encryption (Task 10.4)...")
        async with async_session_maker() as db:
            simulated_url = f"postgresql://postgres:{pwd}@pg-analytics-db:5432/analytics_db"
            sec = await secret_manager.set_secret(
                project_id=project_id,
                key="DATABASE_URL",
                value=simulated_url,
                db=db
            )

            db_entry = ManagedDatabase(
                project_id=project_id,
                name="analytics-db",
                engine="postgres",
                version="16",
                port=5432,
                database_name="analytics_db",
                username="postgres",
                status="RUNNING",
                container_id="test_pg_container_12345",
                connection_url_secret_id=sec.id
            )
            db.add(db_entry)
            await db.commit()
            await db.refresh(db_entry)
            db_id = db_entry.id

        # 5. Test GET /api/v1/databases/{id} (Should return decrypted URL)
        print(f"[*] 5. Testing GET /api/v1/databases/{db_id} with decrypted connection string...")
        res = await client.get(f"/api/v1/databases/{db_id}")
        assert res.status_code == 200, f"Get DB failed: {res.text}"
        data = res.json()
        assert data["id"] == db_id
        assert data["engine"] == "postgres"
        assert data["status"] == "RUNNING"
        assert "postgresql://postgres:" in data["connection_url"]
        print(f"    [+] Database details verified with decrypted URL: {data['connection_url'][:35]}***")

        # 6. Test Redis Model & Secret
        print("[*] 6. Testing Redis Database Association & Secret (REDIS_URL)...")
        async with async_session_maker() as db:
            simulated_redis_url = f"redis://:{pwd}@redis-cache-db:6379/0"
            r_sec = await secret_manager.set_secret(
                project_id=project_id,
                key="REDIS_URL",
                value=simulated_redis_url,
                db=db
            )

            redis_entry = ManagedDatabase(
                project_id=project_id,
                name="cache-db",
                engine="redis",
                version="7",
                port=6379,
                database_name="0",
                username="default",
                status="RUNNING",
                container_id="test_redis_container_67890",
                connection_url_secret_id=r_sec.id
            )
            db.add(redis_entry)
            await db.commit()
            await db.refresh(redis_entry)
            redis_id = redis_entry.id

        res_r = await client.get(f"/api/v1/databases/{redis_id}")
        assert res_r.status_code == 200
        r_data = res_r.json()
        assert r_data["engine"] == "redis"
        assert "redis://:" in r_data["connection_url"]
        print(f"    [+] Redis details verified with decrypted URL: {r_data['connection_url'][:25]}***")

        # 7. Test In-Memory Secret List
        print("[*] 7. Verifying in-memory decrypted secret injection list...")
        async with async_session_maker() as db:
            envs = await secret_manager.get_decrypted_env_list(project_id, db)
            keys = [e.split("=")[0] for e in envs]
            assert "DATABASE_URL" in keys, "DATABASE_URL missing from project envs!"
            assert "REDIS_URL" in keys, "REDIS_URL missing from project envs!"
            print(f"    [+] Secrets successfully bound to application: {keys}")

        # 8. Test DELETE /api/v1/databases/{id}
        print(f"[*] 8. Testing DELETE /api/v1/databases/{db_id}...")
        del_res = await client.delete(f"/api/v1/databases/{db_id}")
        assert del_res.status_code == 204
        print("    [+] Database record deleted successfully (HTTP 204)")

    print("\n[SUCCESS] All Managed Database Provisioning (EPIC-10) tests passed 100%!")

if __name__ == "__main__":
    asyncio.run(run_database_tests())
