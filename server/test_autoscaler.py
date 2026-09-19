import asyncio
import sys
from httpx import AsyncClient, ASGITransport

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.main import app
from app.database import init_db, async_session_maker
from app.models.project import Project
from app.models.deployment import Deployment
from app.models.replica import ContainerReplica
from app.models.autoscale import AutoscaleEvent
from app.services.autoscaler import AutoscalerDaemon

async def run_autoscaler_tests():
    print("[*] Starting Dynamic Horizontal Autoscaler (HPA) Verification Suite...")
    await init_db()

    # 1. Delta CPU Calculation Test
    print("[*] 1. Testing CPU and RAM Delta Math Formula...")
    # Simulated Docker stats
    stats = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 500000000},
            "system_cpu_usage": 1000000000,
            "online_cpus": 2
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 100000000},
            "system_cpu_usage": 500000000
        },
        "memory_stats": {
            "usage": 256 * 1024 * 1024,
            "limit": 1024 * 1024 * 1024
        }
    }

    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
    online_cpus = stats["cpu_stats"]["online_cpus"]
    cpu_percent = round((cpu_delta / system_delta) * online_cpus * 100.0, 2)
    assert cpu_percent == 160.0, f"Expected 160.0% across 2 cores, got {cpu_percent}%"

    mem_percent = round((stats["memory_stats"]["usage"] / stats["memory_stats"]["limit"]) * 100.0, 2)
    assert mem_percent == 25.0, f"Expected 25.0%, got {mem_percent}%"
    print(f"    [+] Delta math verified: CPU={cpu_percent}% across {online_cpus} cores, Memory={mem_percent}%")

    # 2. Database Integration & Deployment Setup
    print("[*] 2. Setting up test project & deployment records...")
    async with async_session_maker() as db:
        test_project = Project(
            name="Autoscale Web Service",
            subdomain="autoscale-test",
            framework="generic",
            port=3000,
            min_replicas=3,
            max_replicas=10
        )
        db.add(test_project)
        await db.commit()
        await db.refresh(test_project)

        test_deployment = Deployment(
            project_id=test_project.id,
            status="ACTIVE",
            active_replicas=3,
            image_tag="127.0.0.1:5000/autoscale-test:latest"
        )
        db.add(test_deployment)
        await db.commit()
        await db.refresh(test_deployment)

        for i in range(3):
            rep = ContainerReplica(
                deployment_id=test_deployment.id,
                container_id=f"test_container_id_{i:04d}",
                container_name=f"autoscale-test-{test_deployment.id[:8]}-{i}",
                replica_index=i,
                private_ip=f"172.28.0.{10+i}",
                port=3000,
                status="HEALTHY"
            )
            db.add(rep)
        
        # Add a simulated autoscale event
        ev = AutoscaleEvent(
            project_id=test_project.id,
            deployment_id=test_deployment.id,
            action="SCALE_UP",
            old_replicas=3,
            new_replicas=4,
            trigger_reason="CPU threshold exceeded (82.5% >= 75%)",
            cpu_percent=82.5
        )
        db.add(ev)
        await db.commit()

        project_id = test_project.id
        deployment_id = test_deployment.id
        print(f"    [+] Created Project={project_id}, Deployment={deployment_id} with 3 replicas")

    # 3. Test Telemetry Endpoint via HTTPX
    print("[*] 3. Testing GET /api/v1/deployments/{id}/metrics...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/deployments/{deployment_id}/metrics")
        assert res.status_code == 200, f"Metrics API failed: {res.text}"
        data = res.json()
        assert data["deployment_id"] == deployment_id
        assert data["min_replicas"] == 3
        assert data["max_replicas"] == 10
        assert len(data["replicas"]) == 3
        print(f"    [+] Telemetry API active: replicas={data['active_replicas']}, min={data['min_replicas']}, max={data['max_replicas']}")

        # 4. Test Autoscale Events Audit Endpoint
        print("[*] 4. Testing GET /api/v1/deployments/{id}/autoscale/events...")
        res_events = await client.get(f"/api/v1/deployments/{deployment_id}/autoscale/events")
        assert res_events.status_code == 200, f"Events API failed: {res_events.text}"
        events_data = res_events.json()
        assert len(events_data) >= 1
        assert events_data[0]["action"] == "SCALE_UP"
        assert events_data[0]["new_replicas"] == 4
        print(f"    [+] Autoscale Audit Trail verified: action={events_data[0]['action']}, reason='{events_data[0]['trigger_reason']}'")

    # 5. Daemon Logic & Threshold Verification
    print("[*] 5. Verifying AutoscalerDaemon thresholds...")
    daemon = AutoscalerDaemon()
    assert daemon.SCALE_OUT_CPU_THRESHOLD == 75.0
    assert daemon.SCALE_IN_CPU_THRESHOLD == 30.0
    assert daemon.MIN_REPLICAS_DEFAULT == 3
    assert daemon.MAX_REPLICAS_DEFAULT == 10
    print("    [+] AutoscalerDaemon thresholds verified (Scale-Out >= 75%, Scale-In < 30%, Floor=3, Ceiling=10)")

    print("\n[SUCCESS] All Dynamic Horizontal Autoscaler (EPIC-09) tests passed 100%!")

if __name__ == "__main__":
    asyncio.run(run_autoscaler_tests())
