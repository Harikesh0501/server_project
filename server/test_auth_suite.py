import asyncio
import os
import sys
from pathlib import Path

# Add server root to sys.path
server_root = Path(__file__).resolve().parent
sys.path.insert(0, str(server_root))

from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.user import User
from app.services.auth_service import auth_service

async def run_auth_tests():
    print("\n=======================================================")
    print("🚀 Running Sovereign Platform Authentication Test Suite")
    print("=======================================================\n")

    await init_db()

    # 1. Test Password Hashing
    print("[1/6] Testing Bcrypt Password Hashing & Verification...")
    raw_pass = "SuperSecurePassword123!"
    hashed = auth_service.hash_password(raw_pass)
    assert hashed != raw_pass, "Password was not hashed"
    assert auth_service.verify_password(raw_pass, hashed) is True, "Password verification failed"
    assert auth_service.verify_password("WrongPassword!", hashed) is False, "Wrong password accepted"
    print("  ✔ Password hashing and verification passed.")

    # 2. Test JWT Token Lifecycle
    print("[2/6] Testing Platform JWT Token Generation & Claims...")
    test_user_id = "test-user-uuid-1234"
    test_email = "test@deploy.local"
    test_role = "developer"

    access_tok, exp_in = auth_service.create_access_token(test_user_id, test_email, test_role)
    refresh_tok = auth_service.create_refresh_token(test_user_id)

    decoded_access = auth_service.decode_token(access_tok)
    assert decoded_access["sub"] == test_user_id
    assert decoded_access["email"] == test_email
    assert decoded_access["role"] == test_role
    assert decoded_access["type"] == "access"

    decoded_refresh = auth_service.decode_token(refresh_tok)
    assert decoded_refresh["sub"] == test_user_id
    assert decoded_refresh["type"] == "refresh"
    print("  ✔ JWT tokens generated and claims validated successfully.")

    # 3. Test Token Revocation & Blacklisting
    print("[3/6] Testing Token Revocation & Blacklisting...")
    assert await auth_service.is_token_revoked(access_tok) is False, "Fresh token marked revoked"
    await auth_service.revoke_token(access_tok)
    assert await auth_service.is_token_revoked(access_tok) is True, "Revoked token was not recognized as revoked"
    print("  ✔ Instant token revocation verified.")

    # 4. Test RFC 8628 Device Authorization Flow
    print("[4/6] Testing RFC 8628 CLI Device Code Flow...")
    device_data = await auth_service.generate_device_code()
    dev_code = device_data["device_code"]
    user_code = device_data["user_code"]

    assert len(user_code) == 9, f"Unexpected user_code format: {user_code}"
    assert "-" in user_code, "User code missing hyphen"

    # Initial poll should be pending
    poll1 = await auth_service.poll_device_token(dev_code)
    assert poll1["status"] == "pending", "Initial device status is not pending"

    # User approves code in browser
    approved = await auth_service.verify_device_code(user_code, test_user_id)
    assert approved is True, "User code approval failed"

    # Poll should now be approved
    poll2 = await auth_service.poll_device_token(dev_code)
    assert poll2["status"] == "approved", "Poll did not return approved state"
    assert poll2["user_id"] == test_user_id, "Approved user ID does not match"
    print(f"  ✔ RFC 8628 Device Flow (Code: {user_code}) verified.")

    # 5. Test Database User Creation & Roles
    print("[5/6] Testing User DB Model & Role Assignment...")
    async with async_session_maker() as db:
        test_uname = "auth_test_user"
        test_uemail = "auth_test@deploy.local"

        # Cleanup if leftover
        res = await db.execute(select(User).where(User.username == test_uname))
        old = res.scalar_one_or_none()
        if old:
            await db.delete(old)
            await db.commit()

        new_user = User(
            email=test_uemail,
            username=test_uname,
            hashed_password=hashed,
            full_name="Auth Test User",
            role="admin",
            oauth_provider="local",
            is_active=True,
            is_superuser=True
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        assert new_user.role == "admin"
        assert new_user.is_superuser is True
        print(f"  ✔ User '{new_user.username}' created with role '{new_user.role}'.")

        # Cleanup
        await db.delete(new_user)
        await db.commit()

    print("[6/6] All Authentication Subsystems Operating Correctly!\n")
    print("=======================================================")
    print("✔ EPIC-11 CORE TEST SUITE: 100% PASSED!")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(run_auth_tests())
