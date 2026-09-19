import sys
import io
import tarfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.quarantine_service import ServerQuarantineVerifier, QuarantineViolationError

def test_server_quarantine():
    print("[*] 1. Testing valid clean tarball extraction...")
    # Generate clean tar in memory
    clean_buf = io.BytesIO()
    with tarfile.open(fileobj=clean_buf, mode="w:gz") as tar:
        data = b"console.log('clean app');"
        ti = tarfile.TarInfo("src/index.js")
        ti.size = len(data)
        tar.addfile(ti, io.BytesIO(data))
    
    clean_bytes = clean_buf.getvalue()
    dest_dir = Path("./data/test_extract_clean")
    extracted = ServerQuarantineVerifier.verify_and_extract(clean_bytes, dest_dir)
    assert "src/index.js" in extracted
    print("    [+] Clean bundle verified and extracted safely.")

    print("[*] 2. Testing rejection of bundle containing .env file...")
    tainted_buf = io.BytesIO()
    with tarfile.open(fileobj=tainted_buf, mode="w:gz") as tar:
        data = b"SECRET=leaked_database_password"
        ti = tarfile.TarInfo(".env")
        ti.size = len(data)
        tar.addfile(ti, io.BytesIO(data))
    
    tainted_bytes = tainted_buf.getvalue()
    try:
        ServerQuarantineVerifier.verify_and_extract(tainted_bytes, Path("./data/test_extract_tainted"))
        assert False, "Server should have rejected .env file!"
    except QuarantineViolationError as e:
        print(f"    [+] Server quarantine caught secret and rejected build: {e}")

    print("[*] 3. Testing rejection of bundle containing id_rsa SSH private key...")
    ssh_buf = io.BytesIO()
    with tarfile.open(fileobj=ssh_buf, mode="w:gz") as tar:
        data = b"-----BEGIN OPENSSH PRIVATE KEY-----"
        ti = tarfile.TarInfo("id_rsa")
        ti.size = len(data)
        tar.addfile(ti, io.BytesIO(data))
    
    ssh_bytes = ssh_buf.getvalue()
    try:
        ServerQuarantineVerifier.verify_and_extract(ssh_bytes, Path("./data/test_extract_ssh"))
        assert False, "Server should have rejected id_rsa file!"
    except QuarantineViolationError as e:
        print(f"    [+] Server quarantine caught id_rsa: {e}")

    print("\n[SUCCESS] SERVER QUARANTINE VERIFIER PASSED 100%!")

if __name__ == "__main__":
    test_server_quarantine()
