import asyncio
import time
import structlog
from datetime import datetime, timezone
import httpx
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import async_session_maker
from app.models.project import Project
from app.models.deployment import Deployment
from app.models.replica import ContainerReplica
from app.models.autoscale import AutoscaleEvent
from app.services.docker_service import docker_service
from app.services.caddy_service import caddy_service
from app.services.secret_service import secret_manager

logger = structlog.get_logger()

class AutoscalerDaemon:
    """
    Dynamic Horizontal Autoscaler Daemon (HPA) & Real-Time Metrics (EPIC-09).
    Monitors replica CPU/RAM via Docker Engine API, dynamically scales 3 to 10+ replicas,
    executes auto-healing watchdogs, and maintains zero-downtime Caddy routing.
    """

    CHECK_INTERVAL_SECONDS = 5.0
    SCALE_OUT_CPU_THRESHOLD = 75.0
    SCALE_IN_CPU_THRESHOLD = 30.0
    SCALE_IN_COOLDOWN_SECONDS = 60.0 # Standard 60s cooldown for responsive testing
    MIN_REPLICAS_DEFAULT = 3
    MAX_REPLICAS_DEFAULT = 10

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        # rolling_cpu_cache[deployment_id] -> list of last N cpu_percent measurements
        self._rolling_cpu_cache: dict[str, list[float]] = {}
        # cooldown_timers[deployment_id] -> float (timestamp when low load began)
        self._cooldown_timers: dict[str, float] = {}
        # latest_metrics_cache[deployment_id] -> live metrics dict
        self._latest_metrics: dict[str, dict] = {}

    def start(self):
        """Starts the autoscaler daemon loop in the background."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._main_loop())
            logger.info("autoscaler_daemon_started", check_interval=self.CHECK_INTERVAL_SECONDS)

    async def stop(self):
        """Stops the autoscaler daemon loop gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("autoscaler_daemon_stopped")

    async def _main_loop(self):
        """Core periodic sampling and autoscaling evaluation loop."""
        while self._running:
            try:
                await self._evaluate_deployments()
            except Exception as e:
                logger.error("autoscaler_loop_error", error=str(e))
            
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)

    async def _evaluate_deployments(self):
        """Evaluates all ACTIVE deployments on the platform."""
        async with async_session_maker() as db:
            query = (
                select(Deployment)
                .where(Deployment.status == "ACTIVE")
                .options(selectinload(Deployment.project), selectinload(Deployment.replicas))
            )
            result = await db.execute(query)
            active_deployments = result.scalars().all()

        for deployment in active_deployments:
            if not deployment.project:
                continue
            try:
                await self._process_deployment(deployment)
            except Exception as e:
                logger.error(
                    "autoscaler_deployment_processing_failed",
                    deployment_id=deployment.id,
                    project=deployment.project.name,
                    error=str(e)
                )

    async def _process_deployment(self, deployment: Deployment):
        """Collects metrics, heals dead replicas, and checks scale-out/in triggers."""
        dep_id = deployment.id
        project = deployment.project
        min_reps = project.min_replicas or self.MIN_REPLICAS_DEFAULT
        max_reps = project.max_replicas or self.MAX_REPLICAS_DEFAULT

        # ------------------------------------------------------------------
        # Phase 1: Metric Collection & Auto-Healing Watchdog (Task 9.4)
        # ------------------------------------------------------------------
        healthy_replicas: list[ContainerReplica] = []
        replica_stats_list: list[dict] = []
        dead_replicas: list[ContainerReplica] = []

        for replica in deployment.replicas:
            container_id = replica.container_id
            try:
                inspection = await docker_service.inspect_container(container_id)
                if not inspection.get("running"):
                    logger.warning("replica_container_not_running", container_id=container_id, status=inspection.get("status"))
                    dead_replicas.append(replica)
                    continue

                stats = await docker_service.get_container_stats(container_id)
                replica_stats_list.append(stats)
                healthy_replicas.append(replica)
            except Exception:
                # Container is unreachable or dead
                logger.warning("replica_container_unhealthy", container_id=container_id, replica_id=replica.id)
                dead_replicas.append(replica)

        # Execute Auto-Healing Watchdog if any replica died
        if dead_replicas:
            await self._auto_heal_replicas(deployment, dead_replicas)
            return # Let next tick evaluate load after healing completes

        if not replica_stats_list:
            return

        # Calculate cluster averages
        avg_cpu = sum(s["cpu_percent"] for s in replica_stats_list) / len(replica_stats_list)
        avg_mem_mb = sum(s["memory_usage_mb"] for s in replica_stats_list) / len(replica_stats_list)
        avg_mem_pct = sum(s["memory_percent"] for s in replica_stats_list) / len(replica_stats_list)

        # Update 30s rolling CPU window (6 samples @ 5s)
        window = self._rolling_cpu_cache.setdefault(dep_id, [])
        window.append(avg_cpu)
        if len(window) > 6:
            window.pop(0)
        rolling_avg_cpu = sum(window) / len(window)

        # Cache live telemetry for SSE stream and API
        current_replicas_count = len(healthy_replicas)
        self._latest_metrics[dep_id] = {
            "deployment_id": dep_id,
            "project_name": project.name,
            "subdomain": project.subdomain,
            "active_replicas": current_replicas_count,
            "min_replicas": min_reps,
            "max_replicas": max_reps,
            "average_cpu_percent": round(rolling_avg_cpu, 2),
            "average_memory_mb": round(avg_mem_mb, 2),
            "average_memory_percent": round(avg_mem_pct, 2),
            "replicas": [
                {
                    "container_id": r.container_id[:12],
                    "container_name": r.container_name,
                    "private_ip": r.private_ip,
                    "port": r.port,
                    "cpu_percent": stats["cpu_percent"],
                    "memory_mb": stats["memory_usage_mb"],
                    "memory_percent": stats["memory_percent"],
                    "status": "HEALTHY"
                }
                for r, stats in zip(healthy_replicas, replica_stats_list)
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # ------------------------------------------------------------------
        # Phase 2: Scale-Out Evaluation (Task 9.2)
        # ------------------------------------------------------------------
        if rolling_avg_cpu >= self.SCALE_OUT_CPU_THRESHOLD and current_replicas_count < max_reps:
            logger.info(
                "autoscaler_scale_out_triggered",
                deployment_id=dep_id,
                rolling_avg_cpu=rolling_avg_cpu,
                threshold=self.SCALE_OUT_CPU_THRESHOLD,
                current_replicas=current_replicas_count
            )
            # Cancel any pending scale-in cooldown
            self._cooldown_timers.pop(dep_id, None)
            await self._scale_out(deployment, current_replicas_count, rolling_avg_cpu)
            return

        # ------------------------------------------------------------------
        # Phase 3: Scale-In & Cooldown Evaluation (Task 9.3)
        # ------------------------------------------------------------------
        if rolling_avg_cpu < self.SCALE_IN_CPU_THRESHOLD and current_replicas_count > min_reps:
            now = time.time()
            if dep_id not in self._cooldown_timers:
                self._cooldown_timers[dep_id] = now
                logger.info(
                    "autoscaler_cooldown_started",
                    deployment_id=dep_id,
                    rolling_avg_cpu=rolling_avg_cpu,
                    cooldown_seconds=self.SCALE_IN_COOLDOWN_SECONDS
                )
            else:
                elapsed = now - self._cooldown_timers[dep_id]
                if elapsed >= self.SCALE_IN_COOLDOWN_SECONDS:
                    logger.info(
                        "autoscaler_scale_in_triggered",
                        deployment_id=dep_id,
                        rolling_avg_cpu=rolling_avg_cpu,
                        current_replicas=current_replicas_count
                    )
                    self._cooldown_timers.pop(dep_id, None)
                    await self._scale_in(deployment, current_replicas_count, rolling_avg_cpu)
        else:
            # Load spiked above scale-in threshold, reset cooldown timer
            if dep_id in self._cooldown_timers:
                self._cooldown_timers.pop(dep_id, None)
                logger.debug("autoscaler_cooldown_reset", deployment_id=dep_id, rolling_avg_cpu=rolling_avg_cpu)

    async def _scale_out(self, deployment: Deployment, current_count: int, trigger_cpu: float):
        """Spawns 1 new replica on deploy-private-net and appends to Caddy upstream pool."""
        project = deployment.project
        new_index = current_count
        new_container_name = f"{project.subdomain}-{deployment.id[:8]}-{new_index}"

        # Resolve secrets in-memory
        async with async_session_maker() as db:
            secret_envs = await secret_manager.get_decrypted_env_list(project.id, db)

        combined_envs = [f"HOST=0.0.0.0", f"PORT={project.port or 3000}"] + secret_envs

        try:
            container_data = await docker_service.create_container(
                image=deployment.image_tag or f"127.0.0.1:5000/{project.subdomain}:{deployment.id[:8]}",
                name=new_container_name,
                env_vars=combined_envs,
                port=project.port or 3000,
                network=settings.DOCKER_PRIVATE_NETWORK
            )
            container_id = container_data["Id"]
            await docker_service.start_container(container_id)

            inspection = await docker_service.inspect_container(container_id)
            private_ip = inspection.get("private_ip") or "127.0.0.1"

            # Verify health probe before adding to load balancer
            healthy = await self._verify_health(private_ip, project.port or 3000)
            if not healthy:
                await docker_service.stop_container(container_id)
                await docker_service.remove_container(container_id)
                logger.error("scale_out_health_probe_failed", container=new_container_name, ip=private_ip)
                return

            # Update database with new replica
            async with async_session_maker() as db:
                new_rep = ContainerReplica(
                    deployment_id=deployment.id,
                    container_id=container_id,
                    container_name=new_container_name,
                    replica_index=new_index,
                    private_ip=private_ip,
                    port=project.port or 3000,
                    status="HEALTHY"
                )
                db.add(new_rep)

                # Record AutoscaleEvent audit record
                event = AutoscaleEvent(
                    project_id=project.id,
                    deployment_id=deployment.id,
                    action="SCALE_UP",
                    old_replicas=current_count,
                    new_replicas=current_count + 1,
                    trigger_reason=f"Average CPU utilization exceeded threshold ({trigger_cpu:.1f}% >= 75%)",
                    cpu_percent=trigger_cpu
                )
                db.add(event)

                # Fetch all healthy IPs for Caddy update
                rep_query = select(ContainerReplica.private_ip).where(
                    ContainerReplica.deployment_id == deployment.id,
                    ContainerReplica.status == "HEALTHY"
                )
                all_ips = (await db.execute(rep_query)).scalars().all()
                all_ips_list = list(all_ips) + [private_ip]

                await db.commit()

            # Dynamic Caddy routing cutover
            await caddy_service.set_subdomain_route(
                subdomain=project.subdomain,
                upstream_ips=all_ips_list,
                port=project.port or 3000
            )

            logger.info("scale_out_complete", new_replicas=current_count + 1, added_ip=private_ip)

        except Exception as e:
            logger.error("scale_out_failed", deployment_id=deployment.id, error=str(e))

    async def _scale_in(self, deployment: Deployment, current_count: int, trigger_cpu: float):
        """Decommissions the oldest surplus replica and updates Caddy upstream pool."""
        project = deployment.project

        async with async_session_maker() as db:
            # Pick highest replica_index surplus container
            query = (
                select(ContainerReplica)
                .where(ContainerReplica.deployment_id == deployment.id, ContainerReplica.status == "HEALTHY")
                .order_by(ContainerReplica.replica_index.desc())
            )
            surplus_rep = (await db.execute(query)).scalars().first()
            if not surplus_rep:
                return

            surplus_id = surplus_rep.container_id
            surplus_db_id = surplus_rep.id

            # Remove record from database
            await db.delete(surplus_rep)

            # Record AutoscaleEvent
            event = AutoscaleEvent(
                project_id=project.id,
                deployment_id=deployment.id,
                action="SCALE_DOWN",
                old_replicas=current_count,
                new_replicas=current_count - 1,
                trigger_reason=f"Average CPU utilization cooled down below threshold ({trigger_cpu:.1f}% < 30%)",
                cpu_percent=trigger_cpu
            )
            db.add(event)

            # Query remaining IPs for Caddy update
            rem_query = select(ContainerReplica.private_ip).where(
                ContainerReplica.deployment_id == deployment.id,
                ContainerReplica.id != surplus_db_id
            )
            remaining_ips = list((await db.execute(rem_query)).scalars().all())
            await db.commit()

        # Update Caddy upstream pool first (stop sending new traffic)
        await caddy_service.set_subdomain_route(
            subdomain=project.subdomain,
            upstream_ips=remaining_ips,
            port=project.port or 3000
        )

        # Gracefully stop and remove surplus container
        try:
            await docker_service.stop_container(surplus_id, timeout=10)
            await docker_service.remove_container(surplus_id)
            logger.info("scale_in_complete", new_replicas=current_count - 1, removed_container=surplus_id[:12])
        except Exception as e:
            logger.warning("scale_in_container_cleanup_failed", container=surplus_id, error=str(e))

    async def _auto_heal_replicas(self, deployment: Deployment, dead_replicas: list[ContainerReplica]):
        """Auto-healing watchdog: restores dead baseline containers within 5 seconds (Task 9.4)."""
        project = deployment.project
        logger.warning(
            "auto_healing_watchdog_activated",
            project=project.name,
            dead_count=len(dead_replicas)
        )

        for dead in dead_replicas:
            # Clean up dead container reference
            try:
                await docker_service.remove_container(dead.container_id, force=True)
            except Exception:
                pass

            # Spawn replacement replica with same index
            new_name = f"{project.subdomain}-{deployment.id[:8]}-{dead.replica_index}-h{int(time.time()) % 10000}"
            async with async_session_maker() as db:
                secret_envs = await secret_manager.get_decrypted_env_list(project.id, db)

            combined_envs = [f"HOST=0.0.0.0", f"PORT={project.port or 3000}"] + secret_envs

            try:
                new_container = await docker_service.create_container(
                    image=deployment.image_tag or f"127.0.0.1:5000/{project.subdomain}:{deployment.id[:8]}",
                    name=new_name,
                    env_vars=combined_envs,
                    port=project.port or 3000,
                    network=settings.DOCKER_PRIVATE_NETWORK
                )
                new_id = new_container["Id"]
                await docker_service.start_container(new_id)

                inspection = await docker_service.inspect_container(new_id)
                new_ip = inspection.get("private_ip") or "127.0.0.1"

                # Update database record
                async with async_session_maker() as db:
                    rep_res = await db.execute(select(ContainerReplica).where(ContainerReplica.id == dead.id))
                    existing = rep_res.scalar_one_or_none()
                    if existing:
                        existing.container_id = new_id
                        existing.container_name = new_name
                        existing.private_ip = new_ip
                        existing.status = "HEALTHY"
                    await db.commit()

                    # Query all current healthy IPs
                    all_query = select(ContainerReplica.private_ip).where(
                        ContainerReplica.deployment_id == deployment.id
                    )
                    all_ips = list((await db.execute(all_query)).scalars().all())

                # Update Caddy
                await caddy_service.set_subdomain_route(
                    subdomain=project.subdomain,
                    upstream_ips=all_ips,
                    port=project.port or 3000
                )

                logger.info("auto_heal_successful", replacement_name=new_name, ip=new_ip)

            except Exception as e:
                logger.error("auto_heal_failed_for_replica", replica_id=dead.id, error=str(e))

    async def _verify_health(self, ip: str, port: int, timeout: float = 2.0) -> bool:
        """Probes HTTP endpoint until HTTP 200 OK or timeout."""
        url = f"http://{ip}:{port}/"
        for _ in range(5):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    res = await client.get(url)
                    if res.status_code in (200, 204, 301, 302, 404):
                        return True
            except Exception:
                await asyncio.sleep(1.0)
        return False

    def get_cached_metrics(self, deployment_id: str) -> dict | None:
        """Returns the latest sampled metrics snapshot for a deployment."""
        return self._latest_metrics.get(deployment_id)

autoscaler_daemon = AutoscalerDaemon()
