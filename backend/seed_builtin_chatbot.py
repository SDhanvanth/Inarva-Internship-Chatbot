"""
Seed the built-in Gemini AI Chatbot as a marketplace app.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database import async_session_factory
from app.models.app import MarketplaceApp, AppStatus, AppCategory, AppVersion
from app.models.user import User, UserRole
from app.config import settings


BUILTIN_CHATBOT_TOOLS = [
    {
        "name": "chat",
        "description": "Have a conversation with the AI assistant. Ask questions, get help, or just chat.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Your message to the AI assistant"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "Optional system prompt to set context for the conversation"
                }
            },
            "required": ["message"]
        },
        "app_id": "inbuilt-gemini-chatbot",
        "app_name": "Gemini AI Assistant"
    },
    {
        "name": "summarize",
        "description": "Summarize text content into a concise form. Great for long articles, documents, or notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content to summarize"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Optional maximum length for the summary in words"
                }
            },
            "required": ["text"]
        },
        "app_id": "inbuilt-gemini-chatbot",
        "app_name": "Gemini AI Assistant"
    },
    {
        "name": "analyze",
        "description": "Analyze content and provide insights. Supports sentiment, key points, and general analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The content to analyze"
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis: general, sentiment, key_points, structured",
                    "enum": ["general", "sentiment", "key_points", "structured"]
                }
            },
            "required": ["content"]
        },
        "app_id": "inbuilt-gemini-chatbot",
        "app_name": "Gemini AI Assistant"
    },
    {
        "name": "code_explain",
        "description": "Explain code snippets in plain language. Supports multiple programming languages.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The code snippet to explain"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language of the code"
                },
                "detail_level": {
                    "type": "string",
                    "description": "Level of detail: brief, medium, detailed",
                    "enum": ["brief", "medium", "detailed"]
                }
            },
            "required": ["code"]
        },
        "app_id": "inbuilt-gemini-chatbot",
        "app_name": "Gemini AI Assistant"
    }
]


async def seed_builtin_chatbot():
    from app.database import async_engine
    
    app_id = None
    
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(MarketplaceApp).where(MarketplaceApp.slug == "gemini-ai-assistant")
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print("Built-in Gemini AI Assistant already exists.")
                print(f"  ID: {existing.id}")
                print(f"  Status: {existing.status.value}")
                print(f"  MCP Endpoint: {existing.mcp_endpoint}")
                
                if existing.capabilities != {"tools": BUILTIN_CHATBOT_TOOLS}:
                    print("Updating capabilities...")
                    existing.capabilities = {"tools": BUILTIN_CHATBOT_TOOLS}
                    await session.commit()
                    print("Capabilities updated!")
                
                app_id = existing.id
            else:
                result = await session.execute(
                    select(User).where(User.email == "system@multichatai.com")
                )
                system_user = result.scalar_one_or_none()
                
                if not system_user:
                    print("Creating System account...")
                    system_user = User(
                        email="system@multichatai.com",
                        password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                        full_name="Multi Chat AI System",
                        role=UserRole.ADMIN,
                        is_active=True,
                        is_verified=True
                    )
                    session.add(system_user)
                    await session.commit()
                    await session.refresh(system_user)
                
                print("Creating Gemini AI Assistant app...")
                
                mcp_endpoint = f"http://localhost:{settings.PORT}/inbuilt-mcp"
                
                app = MarketplaceApp(
                    name="Gemini AI Assistant",
                    slug="gemini-ai-assistant",
                    description="""
The Gemini AI Assistant is a powerful built-in chatbot powered by Google's Gemini AI.

**Features:**
- 💬 **Chat**: Natural conversations with context awareness
- 📝 **Summarize**: Condense long text into key points
- 🔍 **Analyze**: Deep content analysis with sentiment detection
- 💻 **Code Explain**: Get clear explanations of code snippets

This assistant is built into the platform and requires no external setup - just enable it and start chatting!
                """.strip(),
                    short_description="Built-in AI assistant powered by Google Gemini",
                    developer_id=system_user.id,
                    mcp_endpoint=mcp_endpoint,
                    category=AppCategory.PRODUCTIVITY,
                    is_public=True,
                    is_builtin=True,
                    status=AppStatus.APPROVED,
                    version="1.0.0",
                    capabilities={"tools": BUILTIN_CHATBOT_TOOLS},
                    permissions={"scopes": ["chat", "summarize", "analyze", "code_explain"]},
                    icon_url="https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
                    documentation_url=None,
                    support_email="support@multichatai.com"
                )
                session.add(app)
                await session.flush()
                
                version = AppVersion(
                    app_id=app.id,
                    version="1.0.0",
                    mcp_endpoint=mcp_endpoint,
                    changelog="Initial release - Built-in Gemini AI chatbot",
                    is_active=True
                )
                session.add(version)
                
                await session.commit()
                
                print("=" * 50)
                print("Built-in Gemini AI Assistant created successfully!")
                print("=" * 50)
                print(f"  App ID: {app.id}")
                print(f"  Slug: {app.slug}")
                print(f"  Status: {app.status.value}")
                print(f"  MCP Endpoint: {mcp_endpoint}")
                print(f"  Tools: {len(BUILTIN_CHATBOT_TOOLS)}")
                print()
                print("Users can now enable this app from the marketplace!")
                
                app_id = app.id
    finally:
        await async_engine.dispose()
    
    return app_id


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_builtin_chatbot())
