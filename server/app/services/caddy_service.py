import httpx
import structlog
from app.config import settings

logger = structlog.get_logger()

class CaddyService:
    """
    Dynamic Edge Ingress & Reverse Proxy Manager (Mini-Task 2.3.4).
    Communicates with Caddy 2 Admin API (http://127.0.0.1:2019)
    to add, update, and remove reverse proxy routes for deployed applications
    without dropping active connections (Zero-Downtime Traffic Cutover).
    """

    def __init__(self, admin_url: str | None = None):
        self.admin_url = admin_url or settings.CADDY_ADMIN_URL

    async def get_config(self) -> dict | None:
        """Retrieves full active Caddy runtime configuration JSON."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.admin_url}/config/")
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning("caddy_get_config_failed", error=str(e))
        return None

    async def set_subdomain_route(self, subdomain: str, upstream_ips: list[str], port: int = 3000) -> bool:
        """
        Dynamically provisions an ingress route for `{subdomain}.deploy.local`.
        Routes incoming HTTP traffic to target container replicas on deploy-private-net.
        """
        full_host = f"{subdomain}.{settings.ROOT_DOMAIN}"
        upstreams_payload = [{"dial": f"{ip}:{port}"} for ip in upstream_ips]

        route_id = f"route_{subdomain}"
        route_config = {
            "@id": route_id,
            "match": [{"host": [full_host]}],
            "handle": [
                {
                    "handler": "headers",
                    "response": {
                        "set": {
                            "X-Content-Type-Options": ["nosniff"],
                            "X-Frame-Options": ["SAMEORIGIN"],
                            "X-Deployed-By": ["sovereign-cloud"]
                        }
                    }
                },
                {
                    "handler": "reverse_proxy",
                    "upstreams": upstreams_payload,
                    "load_balancing": {
                        "selection_policy": {
                            "policy": "round_robin"
                        }
                    }
                }
            ],
            "terminal": True
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check if route already exists
                check_res = await client.get(f"{self.admin_url}/id/{route_id}")
                if check_res.status_code == 200:
                    # Update existing route
                    res = await client.patch(f"{self.admin_url}/id/{route_id}", json=route_config)
                else:
                    # Prepend new route at index 0 so dynamic subdomains match before default routes
                    res = await client.post(
                        f"{self.admin_url}/config/apps/http/servers/srv0/routes/0",
                        json=route_config
                    )
                    if res.status_code not in (200, 201):
                        # Fallback append if server route array has no elements yet
                        res = await client.post(
                            f"{self.admin_url}/config/apps/http/servers/srv0/routes",
                            json=route_config
                        )

                if res.status_code in (200, 201):
                    logger.info("caddy_route_configured", host=full_host, upstreams=upstream_ips)
                    return True
                else:
                    logger.error("caddy_route_failed", status=res.status_code, body=res.text)
        except Exception as e:
            logger.error("caddy_admin_api_error", error=str(e), host=full_host)

        return False

    async def remove_subdomain_route(self, subdomain: str) -> bool:
        """Removes a dynamic route from Caddy when a deployment is stopped or deleted."""
        route_id = f"route_{subdomain}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.delete(f"{self.admin_url}/id/{route_id}")
                return res.status_code in (200, 204)
        except Exception as e:
            logger.warning("caddy_route_removal_failed", error=str(e), route_id=route_id)
            return False

caddy_service = CaddyService()
