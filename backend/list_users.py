import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database import async_session_factory
from app.models.user import User

async def list_users():
    async with async_session_factory() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No users found.")
        else:
            for user in users:
                print(f"User: {user.email} (Role: {user.role.value})")
                
    from app.database import async_engine
    await async_engine.dispose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(list_users())
