import os
import httpx
from typing import AsyncGenerator
from app.config import settings

class DockerService:
    """
    Direct asynchronous Docker Engine API Client communicating over
    the local Unix domain socket (/var/run/docker.sock) or Windows named pipe.
    """

    def __init__(self):
        # Determine socket transport based on OS
        if os.name == "nt":
            # Windows named pipe / Docker Desktop HTTP endpoint
            self.base_url = "http://localhost:2375"
            self.transport = httpx.AsyncHTTPTransport()
        else:
            # Linux Unix Domain Socket
            self.base_url = "http://docker"
            self.transport = httpx.AsyncHTTPTransport(uds=settings.DOCKER_SOCKET)

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self.transport, base_url=self.base_url, timeout=60.0)

    async def ping(self) -> bool:
        """Pings the local Docker Engine daemon."""
        try:
            async with self._get_client() as client:
                res = await client.get("/_ping")
                return res.status_code == 200
        except Exception:
            return False

    async def create_container(
        self,
        image: str,
        name: str,
        env_vars: list[str],
        port: int,
        cpu_quota: int = 100000, # 1.0 CPU Core
        memory_bytes: int = 512 * 1024 * 1024, # 512 MB
        network: str = settings.DOCKER_PRIVATE_NETWORK
    ) -> dict:
        """
        Creates an isolated container with cgroups resource bounds,
        network attachment, and in-memory environment variables.
        """
        payload = {
            "Image": image,
            "Env": env_vars,
            "HostConfig": {
                "NetworkMode": network,
                "CpuQuota": cpu_quota,
                "CpuPeriod": 100000,
                "Memory": memory_bytes,
                "MemorySwap": memory_bytes,
                "RestartPolicy": {"Name": "unless-stopped"},
                "SecurityOpt": ["no-new-privileges:true"]
            },
            "Labels": {
                "managed_by": "sovereign-cloud",
                "app_name": name,
                "app_port": str(port)
            }
        }

        async with self._get_client() as client:
            res = await client.post(f"/containers/create?name={name}", json=payload)
            if res.status_code != 201:
                raise RuntimeError(f"Docker container creation failed: {res.text}")
            return res.json()

    async def start_container(self, container_id: str) -> None:
        """Starts a created container."""
        async with self._get_client() as client:
            res = await client.post(f"/containers/{container_id}/start")
            if res.status_code not in (204, 304):
                raise RuntimeError(f"Failed to start container {container_id}: {res.text}")

    async def stop_container(self, container_id: str, timeout: int = 15) -> None:
        """Stops a running container with graceful timeout."""
        async with self._get_client() as client:
            res = await client.post(f"/containers/{container_id}/stop?t={timeout}")
            if res.status_code not in (204, 304):
                raise RuntimeError(f"Failed to stop container {container_id}: {res.text}")

    async def remove_container(self, container_id: str, force: bool = True) -> None:
        """Removes a container and its anonymous volumes."""
        async with self._get_client() as client:
            res = await client.delete(f"/containers/{container_id}?v=1&force={'true' if force else 'false'}")
            if res.status_code not in (204, 404):
                raise RuntimeError(f"Failed to remove container {container_id}: {res.text}")

    async def inspect_container(self, container_id: str) -> dict:
        """Returns container inspection data including private IP address and health."""
        async with self._get_client() as client:
            res = await client.get(f"/containers/{container_id}/json")
            if res.status_code != 200:
                raise RuntimeError(f"Failed to inspect container {container_id}: {res.text}")
            data = res.json()

            # Extract IP on private bridge
            networks = data.get("NetworkSettings", {}).get("Networks", {})
            private_ip = None
            if settings.DOCKER_PRIVATE_NETWORK in networks:
                private_ip = networks[settings.DOCKER_PRIVATE_NETWORK].get("IPAddress")
            elif networks:
                first_net = next(iter(networks.values()))
                private_ip = first_net.get("IPAddress")

            return {
                "id": data.get("Id"),
                "name": data.get("Name"),
                "status": data.get("State", {}).get("Status"),
                "running": data.get("State", {}).get("Running"),
                "private_ip": private_ip,
                "exit_code": data.get("State", {}).get("ExitCode"),
                "created": data.get("Created")
            }

    async def stream_container_logs(self, container_id: str, tail: int = 100) -> AsyncGenerator[str, None]:
        """Streams real-time container logs."""
        async with self._get_client() as client:
            async with client.stream(
                "GET",
                f"/containers/{container_id}/logs?stdout=1&stderr=1&follow=1&tail={tail}"
            ) as stream:
                async for line in stream.aiter_lines():
                    if line:
                        yield line

docker_service = DockerService()
