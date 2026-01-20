import asyncio
import sys
import os
import requests
import uuid

sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database import async_session_factory
from app.models.user import User, UserRole

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"test_creator_{uuid.uuid4().hex[:6]}@example.com"
TEST_PASS = "Password123!"

async def promote_user(email: str):
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.role = UserRole.DEVELOPER
            await session.commit()
            print(f"Promoted {email} to DEVELOPER")

    from app.database import async_engine
    await async_engine.dispose()

def test_create_app():
    # 1. Signup
    print(f"Signing up {TEST_EMAIL}...")
    resp = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": TEST_EMAIL,
        "password": TEST_PASS,
        "confirm_password": TEST_PASS,
        "full_name": "Test Creator"
    })
    if resp.status_code not in [200, 201]:
        print(f"Signup failed: {resp.text}")
        return

    # 2. Promote to Developer (backend direct)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(promote_user(TEST_EMAIL))

    # 3. Login
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": TEST_EMAIL,
        "password": TEST_PASS
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Create App
    print("Creating app...")
    payload = {
        "name": "Frontend Debug App",
        "description": "App created to test creation flow",
        "mcp_endpoint": "https://example.com/mcp",
        "category": "productivity"
    }
    
    resp = requests.post(f"{BASE_URL}/developer/apps", json=payload, headers=headers)
    print(f"Create Status: {resp.status_code}")
    with open("error_response.txt", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"Create Status: {resp.status_code}")
    print(f"Response written to error_response.txt")

if __name__ == "__main__":
    test_create_app()
