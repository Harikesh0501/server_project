import sys
import asyncio
from httpx import AsyncClient, ASGITransport
from cryptography.exceptions import InvalidTag

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.main import app
from app.database import init_db, async_session_maker
from app.models.project import Project
from app.services.secret_service import secret_manager, SecretRedactor

async def run_tests():
    print("[*] Initializing test environment...")
    await init_db()

    project_a = "proj_001_aaa"
    project_b = "proj_002_bbb"
    secret_value = "super-secret-production-stripe-key-live-999"

    # Test 1: Round-trip encryption and decryption
    print("[*] 1. Testing AES-256-GCM Encrypt & Decrypt Round-trip...")
    ciphertext, nonce = secret_manager.encrypt(project_a, secret_value)
    assert ciphertext != secret_value
    decrypted = secret_manager.decrypt(project_a, ciphertext, nonce)
    assert decrypted == secret_value, f"Decryption mismatch: {decrypted} != {secret_value}"
    print("    [+] AES-256-GCM round-trip verified successfully.")

    # Test 2: Cryptographic Tamper Resistance
    print("[*] 2. Testing Cryptographic Tamper Resistance (InvalidTag)...")
    tampered_bytes = bytearray.fromhex(ciphertext)
    tampered_bytes[0] ^= 0xFF # Flip bits
    tampered_hex = tampered_bytes.hex()
    try:
        secret_manager.decrypt(project_a, tampered_hex, nonce)
        assert False, "Tampered ciphertext should have raised InvalidTag!"
    except InvalidTag:
        print("    [+] Tamper detection confirmed: InvalidTag raised correctly.")

    # Test 3: Cross-Project Isolation
    print("[*] 3. Testing Cross-Project Isolation (Tenant Isolation)...")
    try:
        secret_manager.decrypt(project_b, ciphertext, nonce)
        assert False, "Project B should NOT be able to decrypt Project A's ciphertext!"
    except InvalidTag:
        print("    [+] Cross-project isolation confirmed: Project B rejected.")

    # Test 4: Secret Redaction in Streaming Logs
    print("[*] 4. Testing Streaming Log Secret Redactor...")
    sample_log = (
        f"Connecting to stripe with key {secret_value} and token "
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c "
        "and AWS key AKIAIOSFODNN7EXAMPLE"
    )
    redacted_log = SecretRedactor.redact(sample_log, sensitive_values=[secret_value])
    assert secret_value not in redacted_log, "Raw secret leaked in log!"
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted_log, "AWS key leaked in log!"
    assert "eyJhbGci" not in redacted_log, "JWT leaked in log!"
    assert "[REDACTED]" in redacted_log
    print("    [+] Log secret masking confirmed: All credentials replaced with [REDACTED].")

    # Test 5: REST API Secrets Vault endpoints
    print("[*] 5. Testing REST API Secrets Vault Endpoints...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a test project
        res = await client.post("/api/v1/projects", json={
            "name": "Vault Test App",
            "subdomain": "vault-test",
            "framework": "fastapi",
            "runtime_type": "backend"
        })
        project_id = res.json()["id"]

        # Bulk upload secrets (like 'deploy env push')
        res = await client.post(f"/api/v1/projects/{project_id}/secrets/bulk", json={
            "secrets": {
                "DATABASE_PASSWORD": "my-ultra-secure-pg-pass",
                "API_KEY": "sk_live_1234567890abcdef"
            }
        })
        assert res.status_code == 200, f"Bulk secret push failed: {res.text}"
        print("    [+] 'deploy env push' bulk upload stored 2 secrets.")

        # List secrets (verify values are NOT returned across network)
        res = await client.get(f"/api/v1/projects/{project_id}/secrets")
        assert res.status_code == 200
        sec_list = res.json()
        assert len(sec_list) == 2
        for s in sec_list:
            assert "value" not in s
            assert "encrypted_value" not in s
            print(f"        Key registered: {s['key']} (is_system={s['is_system']})")

        # Test In-Memory Process Injection
        async with async_session_maker() as db:
            env_vars = await secret_manager.get_decrypted_env_list(project_id, db)
            assert "DATABASE_PASSWORD=my-ultra-secure-pg-pass" in env_vars
            assert "API_KEY=sk_live_1234567890abcdef" in env_vars
            print("    [+] In-Memory environment injection verified: Decrypted in volatile RAM.")

    print("\n[SUCCESS] ALL ZERO-TRUST SECRETS VAULT & REDACTION TESTS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(run_tests())
