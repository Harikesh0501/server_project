import sys
import os
import asyncio
import argparse
import getpass
from pathlib import Path

# Add server root to PYTHONPATH
server_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(server_root))

from sqlalchemy import select
from app.database import async_session_maker
from app.models.user import User
from app.services.auth_service import auth_service

async def create_or_promote_admin(email: str, username: str, password: str, full_name: str | None = None):
    async with async_session_maker() as db:
        clean_email = email.strip().lower()
        clean_username = username.strip().lower()

        res = await db.execute(
            select(User).where((User.email == clean_email) | (User.username == clean_username))
        )
        user = res.scalar_one_or_none()

        hashed_pw = auth_service.hash_password(password)

        if user:
            user.hashed_password = hashed_pw
            user.role = "admin"
            user.is_superuser = True
            user.is_active = True
            if full_name:
                user.full_name = full_name
            await db.commit()
            print(f"\n✔ Updated existing user '{clean_username}' ({clean_email}) to Root Administrator!\n")
        else:
            user = User(
                email=clean_email,
                username=clean_username,
                hashed_password=hashed_pw,
                full_name=full_name or "Root Administrator",
                role="admin",
                oauth_provider="local",
                is_active=True,
                is_superuser=True
            )
            db.add(user)
            await db.commit()
            print(f"\n✔ Created new Root Administrator '{clean_username}' ({clean_email}) successfully!\n")

def main():
    parser = argparse.ArgumentParser(description="Bootstrap Root Administrator for Sovereign Cloud Platform")
    parser.add_argument("--email", type=str, help="Administrator email address")
    parser.add_argument("--username", type=str, help="Administrator username")
    parser.add_argument("--password", type=str, help="Administrator password")
    parser.add_argument("--name", type=str, default="Root Administrator", help="Full name")

    args = parser.parse_args()

    email = args.email
    if not email:
        email = input("Enter admin email (e.g. admin@deploy.local): ").strip()

    username = args.username
    if not username:
        username = input("Enter admin username [admin]: ").strip() or "admin"

    password = args.password
    if not password:
        password = getpass.getpass("Enter secure admin password: ")
        confirm = getpass.getpass("Confirm admin password: ")
        if password != confirm:
            print("\n❌ Passwords do not match.")
            sys.exit(1)

    if len(password) < 6:
        print("\n❌ Password must be at least 6 characters.")
        sys.exit(1)

    asyncio.run(create_or_promote_admin(email, username, password, args.name))

if __name__ == "__main__":
    main()
