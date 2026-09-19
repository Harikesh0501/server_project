import sys
import asyncio
from httpx import AsyncClient, ASGITransport

# Force UTF-8 on Windows stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.main import app
from app.database import init_db

async def run_tests():
    print("[*] Initializing test database...")
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. OpenAPI & Swagger Docs Verification
        print("[*] 1. Testing OpenAPI & Swagger Docs (/docs, /openapi.json)...")
        res = await client.get("/openapi.json")
        assert res.status_code == 200, f"OpenAPI failed: {res.text}"
        spec = res.json()
        assert "BearerAuth" in spec["components"]["securitySchemes"], "BearerAuth missing from OpenAPI spec!"
        print("    [+] OpenAPI spec valid with BearerAuth security scheme")

        # 2. Create Project
        print("[*] 2. Registering new Project ('demo-app')...")
        res = await client.post("/api/v1/projects", json={
            "name": "Demo Application",
            "subdomain": "demo-app",
            "framework": "nextjs",
            "runtime_type": "frontend",
            "git_url": "https://github.com/example/demo-app.git",
            "git_branch": "main",
            "port": 3000
        })
        assert res.status_code == 201, f"Project creation failed: {res.text}"
        project_data = res.json()
        project_id = project_data["id"]
        print(f"    [+] Project created: ID={project_id}, Subdomain={project_data['subdomain']}")

        # 3. Create Deployment
        print("[*] 3. Triggering Deployment (POST /api/v1/deployments)...")
        res = await client.post("/api/v1/deployments", json={
            "project_id": project_id,
            "branch": "main",
            "commit_hash": "a1b2c3d4e5f67890123456789012345678901234",
            "commit_message": "feat: initialize master dashboard layout"
        })
        assert res.status_code == 201, f"Deployment failed: {res.text}"
        dep_data = res.json()
        deployment_id = dep_data["id"]
        assert dep_data["status"] == "PENDING"
        assert dep_data["public_url"] == "https://demo-app.deploy.local"
        print(f"    [+] Deployment queued: ID={deployment_id}, Status={dep_data['status']}, URL={dep_data['public_url']}")

        # 4. Inspect Deployment
        print(f"[*] 4. Inspecting Deployment (GET /api/v1/deployments/{deployment_id})...")
        res = await client.get(f"/api/v1/deployments/{deployment_id}")
        assert res.status_code == 200
        inspect_data = res.json()
        assert inspect_data["id"] == deployment_id
        assert inspect_data["project_name"] == "Demo Application"
        print(f"    [+] Deployment inspected successfully: Project={inspect_data['project_name']}")

        # 5. Cancel Deployment
        print(f"[*] 5. Testing Deployment Cancellation (POST /api/v1/deployments/{deployment_id}/cancel)...")
        res = await client.post(f"/api/v1/deployments/{deployment_id}/cancel")
        assert res.status_code == 200
        cancelled_data = res.json()
        assert cancelled_data["status"] == "CANCELLED"
        print(f"    [+] Deployment cancelled: Status={cancelled_data['status']}")

        # 6. Git Repositories Listing
        print("[*] 6. Testing Git Repositories (GET /api/v1/git/repositories)...")
        res = await client.get("/api/v1/git/repositories")
        assert res.status_code == 200
        repos = res.json()
        assert len(repos) >= 1
        print(f"    [+] Connected Git repositories: {len(repos)} repository found ({repos[0]['name']})")

        # 7. GitHub Webhook Ping
        print("[*] 7. Testing GitHub Webhook Ping (POST /api/v1/webhooks/github)...")
        res = await client.post("/api/v1/webhooks/github", headers={"X-GitHub-Event": "ping"}, json={})
        assert res.status_code == 200
        assert res.json()["status"] == "pong"
        print("    [+] Webhook Ping response: pong")

        # 8. GitHub Webhook Push (CD Auto-Trigger)
        print("[*] 8. Testing GitHub Webhook Push (CD Auto-Trigger)...")
        res = await client.post("/api/v1/webhooks/github", headers={"X-GitHub-Event": "push"}, json={
            "ref": "refs/heads/main",
            "repository": {
                "name": "demo-app",
                "clone_url": "https://github.com/example/demo-app.git"
            },
            "head_commit": {
                "id": "fedcba98765432101234567890abcdef12345678",
                "message": "fix: update responsive navbar styles"
            }
        })
        assert res.status_code == 200
        webhook_result = res.json()
        assert webhook_result["status"] == "triggered"
        assert len(webhook_result["deployments"]) == 1
        cd_dep_id = webhook_result["deployments"][0]["deployment_id"]
        print(f"    [+] Webhook CD automatically triggered deployment: ID={cd_dep_id}")

        # 9. Logs retrieval
        print(f"[*] 9. Testing Deployment Logs (GET /api/v1/deployments/{cd_dep_id}/logs)...")
        res = await client.get(f"/api/v1/deployments/{cd_dep_id}/logs")
        assert res.status_code == 200
        logs = res.json()
        print(f"    [+] Retrieved historical logs: {len(logs)} entries")

    print("\n[SUCCESS] ALL EPIC-06 API LIFECYCLE TESTS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(run_tests())
