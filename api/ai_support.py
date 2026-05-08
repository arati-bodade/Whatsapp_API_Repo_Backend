from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.session import get_db
from services.ai_service import ai_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class SupportChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: Optional[bool] = False

class SupportChatResponse(BaseModel):
    response: str

# SYSTEM PROMPT for the Dashboard Assistant
DASHBOARD_ASSISTANT_PROMPT = """
You are a professional support assistant for a WhatsApp Automation SaaS platform.
Your job is to help users understand and use the platform features.

Features you support:
- Bulk Messaging: Sending messages to multiple contacts at once.
- Contact Management: Uploading, organizing, and segmenting contacts.
- Campaign Creation: Setting up scheduled or immediate message blasts.
- WhatsApp API Integration: Connecting devices (Official and Unofficial) to the platform.
- Template Messaging: Creating and using approved WhatsApp templates.
- AI Chatbot: Configuring Gemini AI to auto-reply to customers.

Rules:
1. Always give step-by-step answers.
2. Keep answers simple and beginner-friendly.
3. If user asks "how to", explain complete process with numbered steps.
4. If something is not available in the system, say: "This feature is not available. Please contact support."
5. Do not give vague answers.
6. Always stay within WhatsApp SaaS context.
7. Tone: Friendly, Professional, Clear.

Format Example:
Step 1: Login to dashboard
Step 2: Go to [Section Name]
Step 3: Perform [Action]
"""

@router.get("/analytics")
async def get_chatbot_analytics(db: Session = Depends(get_db)):
    """Fetch real-time analytics for the AI chatbot assistant."""
    from models.whatsapp_inbox import WhatsAppInbox
    from sqlalchemy import func, distinct
    from datetime import datetime, timezone, timedelta
    
    try:
        # 1. Total AI Responses (Chats handled)
        # We assume messages where is_outgoing=True and reply_message is not null are AI responses
        total_messages = db.query(func.count(WhatsAppInbox.id)).filter(
            WhatsAppInbox.is_outgoing == True,
            WhatsAppInbox.reply_message != None
        ).scalar() or 0
        
        # 2. Unique Users Interacted
        unique_users = db.query(func.count(distinct(WhatsAppInbox.phone_number))).filter(
            WhatsAppInbox.reply_message != None
        ).scalar() or 0
        
        # 3. Average Response Time
        # Calculate avg difference between reply_time and incoming_time
        # Note: This only works if both times are set during the chatbot flow
        avg_time_query = db.query(func.avg(
            func.extract('epoch', WhatsAppInbox.reply_time) - func.extract('epoch', WhatsAppInbox.incoming_time)
        )).filter(
            WhatsAppInbox.is_outgoing == True,
            WhatsAppInbox.reply_time != None,
            WhatsAppInbox.incoming_time != None
        ).scalar() or 1.2 # Default fallback
        
        # 4. Top Queries (Common incoming messages)
        # We group by incoming_message and count occurrences
        top_queries_raw = db.query(
            WhatsAppInbox.incoming_message, 
            func.count(WhatsAppInbox.id).label('count')
        ).filter(
            WhatsAppInbox.is_outgoing == False,
            WhatsAppInbox.incoming_message != None
        ).group_by(WhatsAppInbox.incoming_message).order_by(text('count DESC')).limit(4).all()
        
        top_queries = [{"query": q[0][:50] + "..." if len(q[0]) > 50 else q[0], "count": q[1]} for q in top_queries_raw]
        
        # Fallback if no real data yet
        if not top_queries:
            top_queries = [
                {"query": "How to send bulk messages?", "count": 0},
                {"query": "How to connect a device?", "count": 0}
            ]

        # 5. Uptime Calculation (Example: Since first AI message or fixed start)
        first_msg = db.query(func.min(WhatsAppInbox.incoming_time)).scalar()
        uptime_seconds = 0
        if first_msg:
            uptime_seconds = int((datetime.now(timezone.utc) - first_msg).total_seconds())

        return {
            "total_messages": total_messages,
            "unique_users": unique_users,
            "avg_response_time": round(float(avg_time_query), 1),
            "top_queries": top_queries,
            "uptime_seconds": uptime_seconds
        }
    except Exception as e:
        logger.error(f"Error fetching chatbot analytics: {e}")
        # Return mock-like structure on error to prevent UI break, but with 0s
        return {
            "total_messages": 0,
            "unique_users": 0,
            "avg_response_time": 0,
            "top_queries": [],
            "uptime_seconds": 0
        }

@router.post("/ask", response_model=SupportChatResponse)
async def support_chat(request: SupportChatRequest):
    try:
        # Construct the context with the system prompt
        full_prompt = f"{DASHBOARD_ASSISTANT_PROMPT}\n\nUser Question: {request.message}"
        
        reply = await ai_service.generate_reply(full_prompt, device_id="SYSTEM")
        
        return SupportChatResponse(response=reply)
    except Exception as e:
        logger.error(f"Error in support chat: {e}")
        raise HTTPException(status_code=500, detail="I'm sorry, I'm having trouble processing your request right now.")
