import asyncio
import sys
import os
import secrets

sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database import async_session_factory
from app.models.app import MarketplaceApp, AppStatus, AppCategory, AppVersion
from app.models.user import User, UserRole

async def seed_apps():
    async with async_session_factory() as session:
        # 1. Get or Create a Developer User
        result = await session.execute(select(User).where(User.email == "system_dev@aiplatform.com"))
        developer = result.scalar_one_or_none()
        
        if not developer:
            print("Creating System Developer account...")
            developer = User(
                email="system_dev@aiplatform.com",
                password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", # "password"
                full_name="System Developer",
                role=UserRole.DEVELOPER,
                is_active=True,
                is_verified=True
            )
            session.add(developer)
            await session.commit()
            await session.refresh(developer)
        
        # 2. Define Default Apps
        apps_data = [
            {
                "name": "Weather Assistant",
                "slug": "weather-assistant",
                "description": "Get real-time weather updates for any location worldwide. Supports current conditions, forecasts, and historical data.",
                "short_description": "Real-time weather updates globaly.",
                "category": AppCategory.CONTENT,
                "mcp_endpoint": "http://localhost:8001/mcp", # Mock endpoint
                "icon_url": "https://cdn-icons-png.flaticon.com/512/4052/4052984.png",
                "status": AppStatus.APPROVED,
                "is_public": True,
                "version": "1.0.0",
                "permissions": {"scopes": ["read_weather", "location"]}
            },
            {
                "name": "Code Optimizer",
                "slug": "code-optimizer",
                "description": "Analyze your code for performance bottlenecks and suggest optimizations. Supports Python, JavaScript, and Go.",
                "short_description": "Optimize and refactor your code.",
                "category": AppCategory.DEVELOPMENT,
                "mcp_endpoint": "http://localhost:8002/mcp",
                "icon_url": "https://cdn-icons-png.flaticon.com/512/1005/1005141.png",
                "status": AppStatus.APPROVED,
                "is_public": True,
                "version": "1.2.0",
                "permissions": {"scopes": ["read_code", "write_code"]}
            },
            {
                "name": "Data Visualizer",
                "slug": "data-visualizer",
                "description": "Turn complex datasets into beautiful charts and graphs. Upload CSV or JSON and get instant visualizations.",
                "short_description": "Create charts from your data.",
                "category": AppCategory.DATA_ANALYSIS,
                "mcp_endpoint": "http://localhost:8003/mcp",
                "icon_url": "https://cdn-icons-png.flaticon.com/512/2920/2920323.png",
                "status": AppStatus.APPROVED,
                "is_public": True,
                "version": "2.1.0",
                "permissions": {"scopes": ["analyze_data"]}
            }
        ]
        
        # 3. Insert Apps
        for app_info in apps_data:
            # Check if exists
            result = await session.execute(select(MarketplaceApp).where(MarketplaceApp.slug == app_info["slug"]))
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"App '{app_info['name']}' already exists. Skipping.")
                continue
            
            print(f"Creating app '{app_info['name']}'...")
            app = MarketplaceApp(
                name=app_info["name"],
                slug=app_info["slug"],
                description=app_info["description"],
                short_description=app_info["short_description"],
                category=app_info["category"],
                mcp_endpoint=app_info["mcp_endpoint"],
                icon_url=app_info["icon_url"],
                status=app_info["status"],
                is_public=app_info["is_public"],
                version=app_info["version"],
                developer_id=developer.id,
                permissions=app_info["permissions"]
            )
            session.add(app)
            await session.flush() # Get ID
            
            # Version
            version = AppVersion(
                app_id=app.id,
                version=app_info["version"],
                mcp_endpoint=app_info["mcp_endpoint"],
                changelog="Initial seed release",
                is_active=True
            )
            session.add(version)
        
        await session.commit()
        print("Seeding complete!")

    from app.database import async_engine
    await async_engine.dispose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_apps())
