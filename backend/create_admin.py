import asyncio
import sys
import os

# Add parent directory to path to allow importing app modules
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database import async_session_factory
from app.models.user import User, UserRole

async def promote_to_admin(email: str):
    async with async_session_factory() as session:
        # Find user
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return
        
        # Update role
        user.role = UserRole.ADMIN
        await session.commit()
        print(f"Success: User '{email}' has been promoted to ADMIN.")

    from app.database import async_engine
    await async_engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_admin.py <email>")
        sys.exit(1)
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    email = sys.argv[1]
    asyncio.run(promote_to_admin(email))
