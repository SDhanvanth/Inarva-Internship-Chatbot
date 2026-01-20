"""
Chat endpoints.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.chat import Conversation, Message, MessageRole
from app.models.app import UserEnabledApp, MarketplaceApp
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ChatRequest,
    ChatResponse,
    MessageResponse,
    ToolCall,
)
from app.api.deps import require_auth, check_rate_limit, get_rate_limiter
from app.core.security import sanitize_input
from app.config import settings


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    include_archived: bool = False,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversations."""
    from sqlalchemy.orm import selectinload
    
    query = select(Conversation).where(Conversation.user_id == user.id)
    
    if not include_archived:
        query = query.where(Conversation.is_archived == False)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate with eager loading for messages
    offset = (page - 1) * per_page
    query = query.options(selectinload(Conversation.messages)).offset(offset).limit(per_page).order_by(Conversation.updated_at.desc())
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=c.id,
                title=c.title,
                is_archived=c.is_archived,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=len(c.messages) if c.messages else 0
            )
            for c in conversations
        ],
        total=total,
        page=page,
        pages=(total + per_page - 1) // per_page
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation."""
    conversation = Conversation(
        user_id=user.id,
        title=sanitize_input(data.title) if data.title else None
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        is_archived=conversation.is_archived,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation with messages."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        is_archived=conversation.is_archived,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(messages),
        messages=[MessageResponse.model_validate(m) for m in messages]
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    await db.delete(conversation)
    await db.commit()
    
    return {"message": "Conversation deleted"}


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Archive a conversation."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conversation.is_archived = True
    await db.commit()
    
    return {"message": "Conversation archived"}


@router.post("/send", response_model=ChatResponse)
async def send_message(
    data: ChatRequest,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Send a message and get AI response.
    
    This is the main chat endpoint that:
    1. Creates or uses existing conversation
    2. Stores user message
    3. Processes through enabled app tools (including inbuilt Gemini chatbot)
    4. Returns AI response
    """
    from app.mcp.client import mcp_client
    from app.mcp.gemini import gemini_client
    from datetime import datetime
    import json
    
    # Sanitize input
    content = sanitize_input(data.message)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    # Get or create conversation
    if data.conversation_id:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.id == data.conversation_id,
                Conversation.user_id == user.id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=user.id,
            title=content[:50] + "..." if len(content) > 50 else content
        )
        db.add(conversation)
        await db.flush()
    
    # Store user message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=content
    )
    db.add(user_message)
    
    # Get user's enabled apps
    from app.models.app import AppStatus
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(UserEnabledApp)
        .options(selectinload(UserEnabledApp.app))
        .join(MarketplaceApp)
        .where(
            UserEnabledApp.user_id == user.id,
            MarketplaceApp.status == AppStatus.APPROVED
        )
    )
    enabled_apps = result.scalars().all()
    
    # Get conversation history for context
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history_messages = list(reversed(history_result.scalars().all()))
    conversation_history = [
        {"role": msg.role.value, "content": msg.content}
        for msg in history_messages
    ]
    
    ai_response_content = ""
    tool_calls_made = []
    
    # Check if user has any chat-capable apps enabled
    chat_app = None
    for ea in enabled_apps:
        app = ea.app
        if app.is_builtin and app.slug == "gemini-ai-assistant":
            chat_app = app
            break
        # Also check for other apps with chat capability
        if app.capabilities and "tools" in app.capabilities:
            for tool in app.capabilities["tools"]:
                if tool.get("name") == "chat":
                    chat_app = app
                    break
    
    if chat_app:
        # Use the enabled chat app
        if chat_app.is_builtin and chat_app.slug == "gemini-ai-assistant":
            # Use inbuilt Gemini directly
            if gemini_client.is_configured:
                result = await gemini_client.chat(
                    message=content,
                    conversation_history=conversation_history
                )
                if result["success"]:
                    ai_response_content = result["response"]
                    tool_calls_made.append({
                        "tool_name": "chat",
                        "app_name": "Gemini AI Assistant",
                        "success": True
                    })
                else:
                    ai_response_content = f"Sorry, I encountered an error: {result.get('error', 'Unknown error')}"
                    tool_calls_made.append({
                        "tool_name": "chat",
                        "app_name": "Gemini AI Assistant",
                        "success": False,
                        "error": result.get("error")
                    })
            else:
                ai_response_content = "The Gemini AI Assistant is not configured. Please set the GEMINI_API_KEY environment variable."
        else:
            # Use external MCP server
            if chat_app.mcp_endpoint:
                tool_result = await mcp_client.invoke_tool(
                    mcp_endpoint=chat_app.mcp_endpoint,
                    tool_name="chat",
                    arguments={"message": content},
                    api_key_encrypted=chat_app.mcp_api_key_encrypted
                )
                if tool_result.success:
                    # Extract response from tool result
                    if isinstance(tool_result.result, dict):
                        ai_response_content = tool_result.result.get("response", str(tool_result.result))
                    else:
                        ai_response_content = str(tool_result.result)
                    tool_calls_made.append({
                        "tool_name": "chat",
                        "app_name": chat_app.name,
                        "success": True,
                        "duration_ms": tool_result.duration_ms
                    })
                else:
                    ai_response_content = f"Sorry, I couldn't get a response from {chat_app.name}: {tool_result.error}"
                    tool_calls_made.append({
                        "tool_name": "chat",
                        "app_name": chat_app.name,
                        "success": False,
                        "error": tool_result.error
                    })
            else:
                ai_response_content = f"The app {chat_app.name} doesn't have a valid MCP endpoint configured."
    else:
        # No chat app enabled
        if len(enabled_apps) == 0:
            ai_response_content = "You don't have any apps enabled. Please go to the Marketplace and enable an app like 'Gemini AI Assistant' to start chatting!"
        else:
            # List enabled apps but note they don't have chat capability
            app_names = [ea.app.name for ea in enabled_apps]
            ai_response_content = f"You have {len(enabled_apps)} app(s) enabled ({', '.join(app_names)}), but none of them have chat capability. Enable the 'Gemini AI Assistant' from the Marketplace for AI chat!"
    
    # Store AI response
    ai_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=ai_response_content,
        tool_calls=tool_calls_made if tool_calls_made else None
    )
    db.add(ai_message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(ai_message)
    
    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageResponse.model_validate(ai_message),
        tool_calls=tool_calls_made if tool_calls_made else None
    )


@router.get("/enabled-tools")
async def get_enabled_tools(
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get list of tools available from enabled apps."""
    result = await db.execute(
        select(UserEnabledApp)
        .join(MarketplaceApp)
        .where(
            UserEnabledApp.user_id == user.id,
            MarketplaceApp.status == "approved"
        )
    )
    enabled_apps = result.scalars().all()
    
    tools = []
    for ea in enabled_apps:
        app = ea.app
        if app.capabilities:
            for tool in app.capabilities.get("tools", []):
                tools.append({
                    "app_id": app.id,
                    "app_name": app.name,
                    "tool_name": tool.get("name"),
                    "description": tool.get("description"),
                    "parameters": tool.get("parameters")
                })
    
    return {"tools": tools}
