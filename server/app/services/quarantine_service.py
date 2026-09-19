import io
import re
import tarfile
from pathlib import Path

class QuarantineViolationError(Exception):
    """Raised when a quarantined sensitive file is detected in an uploaded source bundle."""
    pass

class ServerQuarantineVerifier:
    """
    Server-Side Pre-Flight Quarantine Verifier (Mini-Task 4.2.4).
    Inspects archive members in-memory before extracting into build workspace.
    Guarantees that NO secrets or credentials ever enter the build pipeline.
    """

    QUARANTINE_REGEX = [
        re.compile(r"(?:^|/)\.env(?:\..*)?$", re.IGNORECASE),
        re.compile(r"(?:^|/)id_rsa(?:\.pub)?$", re.IGNORECASE),
        re.compile(r"(?:^|/)id_ed25519(?:\.pub)?$", re.IGNORECASE),
        re.compile(r".*\.(?:pem|key|pfx)$", re.IGNORECASE),
        re.compile(r"(?:^|/)credentials\.json$", re.IGNORECASE),
        re.compile(r"(?:^|/)service-account.*\.json$", re.IGNORECASE),
    ]

    @classmethod
    def verify_and_extract(cls, archive_bytes: bytes, destination_dir: Path) -> list[str]:
        """
        Inspects tarball in-memory. If any member violates quarantine, aborts immediately.
        Otherwise extracts safely to destination directory.
        """
        destination_dir.mkdir(parents=True, exist_ok=True)
        extracted_files = []

        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as tar:
            members = tar.getmembers()

            # Pass 1: Security Audit
            for member in members:
                norm_name = member.name.replace("\\", "/")
                for pattern in cls.QUARANTINE_REGEX:
                    if pattern.search(norm_name):
                        raise QuarantineViolationError(
                            f"ZERO-TRUST REJECTION: Quarantined sensitive file '{norm_name}' "
                            f"found in source bundle. Build immediately aborted."
                        )

            # Pass 2: Safe Extraction
            for member in members:
                # Prevent directory traversal attacks (zip-slip / tar-slip)
                target_path = (destination_dir / member.name).resolve()
                if not str(target_path).startswith(str(destination_dir.resolve())):
                    raise QuarantineViolationError(
                        f"SECURITY VIOLATION: Path traversal attempt detected: '{member.name}'"
                    )

            tar.extractall(path=destination_dir)
            extracted_files = [m.name for m in members if m.isfile()]

        return extracted_files
