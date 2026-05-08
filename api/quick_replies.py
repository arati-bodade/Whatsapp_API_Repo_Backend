from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, ConfigDict
import uuid

from db.session import get_db
from models.quick_reply import QuickReply
from models.busi_user import BusiUser
from api.auth import get_current_user

router = APIRouter()

# --- Schemas ---
class QuickReplyCreate(BaseModel):
    shortcut: str
    text: str

class QuickReplyResponse(BaseModel):
    id: str
    shortcut: str
    text: str
    
    model_config = ConfigDict(from_attributes=True)

# --- Endpoints ---

@router.get("/quick-replies", response_model=List[QuickReplyResponse])
async def get_quick_replies(
    current_user: BusiUser = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return db.query(QuickReply).filter(QuickReply.busi_user_id == current_user.busi_user_id).all()

@router.post("/quick-replies", response_model=QuickReplyResponse)
async def create_quick_reply(
    reply: QuickReplyCreate,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_reply = QuickReply(
        busi_user_id=current_user.busi_user_id,
        shortcut=reply.shortcut,
        text=reply.text
    )
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    return new_reply

@router.delete("/quick-replies/{reply_id}")
async def delete_quick_reply(
    reply_id: str,
    current_user: BusiUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reply = db.query(QuickReply).filter(
        QuickReply.id == reply_id,
        QuickReply.busi_user_id == current_user.busi_user_id
    ).first()
    
    if not reply:
        raise HTTPException(status_code=404, detail="Quick reply not found")
        
    db.delete(reply)
    db.commit()
    return {"status": "success"}
