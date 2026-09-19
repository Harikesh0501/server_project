import asyncio
import sys
from pathlib import Path

# Enable UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add server directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import init_db, async_session_maker
from app.services.domain_service import DomainService
from app.models.project import Project

async def run_tests():
    print("[*] Initializing Database...")
    await init_db()
    print("[+] Database schema created successfully.")

    async with async_session_maker() as db:
        print("\n[*] Test 1: Checking availability of fresh domain 'my-shop'...")
        res1 = await DomainService.check_availability("my-shop", db)
        print(f"Result: available={res1.available}, msg='{res1.message}', full='{res1.full_domain}'")
        assert res1.available is True, "Expected 'my-shop' to be available"

        print("\n[*] Test 2: Registering project 'my-shop' in database...")
        proj = Project(
            name="My Awesome Shop",
            subdomain="my-shop",
            framework="nextjs",
            runtime_type="frontend",
            port=3000
        )
        db.add(proj)
        await db.commit()
        print(f"[+] Project registered with ID: {proj.id}")

        print("\n[*] Test 3: Checking availability of 'my-shop' AFTER registration (duplicate conflict test)...")
        res2 = await DomainService.check_availability("my-shop", db)
        print(f"Result: available={res2.available}, msg='{res2.message}'")
        print(f"Suggestions: {res2.suggestions}")
        assert res2.available is False, "Expected 'my-shop' to be taken"
        assert len(res2.suggestions) > 0, "Expected suggestions to be provided"

        print("\n[*] Test 4: Checking reserved subdomain 'api'...")
        res3 = await DomainService.check_availability("api", db)
        print(f"Result: available={res3.available}, msg='{res3.message}'")
        assert res3.available is False, "Expected 'api' to be reserved"

    print("\n[SUCCESS] ALL TESTS PASSED! The FastAPI Domain Engine and SQLite database are working flawlessly!")

if __name__ == "__main__":
    asyncio.run(run_tests())
