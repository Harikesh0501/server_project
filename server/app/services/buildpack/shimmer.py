import re

class HostShimmer:
    """
    Host-Binding Automated Shimmer & Port Rewriter (Task 5.2).
    Many web developers write `app.listen(3000, 'localhost')` or `--host 127.0.0.1`
    which causes containers to be unreachable across private bridge networks.
    HostShimmer dynamically rewrites loopback bindings to `0.0.0.0`.
    """

    LOOPBACK_PATTERNS = [
        (re.compile(r"--host\s+127\.0\.0\.1\b", re.IGNORECASE), "--host 0.0.0.0"),
        (re.compile(r"--host\s+localhost\b", re.IGNORECASE), "--host 0.0.0.0"),
        (re.compile(r"-b\s+127\.0\.0\.1:(\d+)\b", re.IGNORECASE), r"-b 0.0.0.0:\1"),
        (re.compile(r"--bind\s+127\.0\.0\.1:(\d+)\b", re.IGNORECASE), r"--bind 0.0.0.0:\1"),
        (re.compile(r"--bind\s+localhost:(\d+)\b", re.IGNORECASE), r"--bind 0.0.0.0:\1"),
        (re.compile(r"-h\s+127\.0\.0\.1\b", re.IGNORECASE), "-h 0.0.0.0"),
        (re.compile(r"-h\s+localhost\b", re.IGNORECASE), "-h 0.0.0.0"),
    ]

    @classmethod
    def rewrite_start_command(cls, command: str | None) -> tuple[str | None, bool]:
        """
        Rewrites localhost/127.0.0.1 bindings to 0.0.0.0.
        Returns (modified_command, was_rewritten).
        """
        if not command:
            return None, False

        modified = command
        was_rewritten = False

        for pattern, replacement in cls.LOOPBACK_PATTERNS:
            if pattern.search(modified):
                modified = pattern.sub(replacement, modified)
                was_rewritten = True

        return modified, was_rewritten

    @classmethod
    def get_shimmer_env(cls, port: int) -> dict[str, str]:
        """
        Injects standard universal runtime environment variables ensuring
        frameworks (Node, Python, Go, Rust) bind to all interfaces on the designated port.
        """
        return {
            "HOST": "0.0.0.0",
            "HOSTNAME": "0.0.0.0",
            "PORT": str(port),
            "NODE_ENV": "production",
            "PYTHONUNBUFFERED": "1"
        }
