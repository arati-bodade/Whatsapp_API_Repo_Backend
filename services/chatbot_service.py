import logging
from services.ai_service import ai_service
from services.unified_whatsapp_sender import send_whatsapp_message
from db.session import SessionLocal
from models.whatsapp_inbox import WhatsAppInbox
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class ChatbotService:
    async def process_incoming_message(self, device_id: str, phone: str, message: str, jid: str = None):
        """
        Process an incoming message and generate an AI response.
        Runs in background to avoid blocking webhook response.
        """
        db = SessionLocal()
        try:
            # 1. Check if AI Chatbot is enabled in settings (optional)
            # For now, we assume it's enabled if this is called
            
            logger.info(f"🤖 [CHATBOT] Generating AI reply for {phone} via device {device_id}...")
            
            # 2. Construct Prompt (System Instructions)
            # This prompt guides the AI to behave as a customer support bot for the business
            system_prompt = (
                "You are the Official AI Support Assistant for this WhatsApp Automation Platform. "
                "You have expert knowledge of Bulk Messaging, Device Management, and Credit Systems. "
                "Answer the customer's question concisely using bullet points if possible. "
                "If they ask about technical features, use your project knowledge. "
                "Always be professional and helpful."
            )
            
            full_prompt = f"{system_prompt}\n\nCustomer: {message}\nAI:"
            
            # 3. Generate reply from AI Service (OpenAI or Ollama)
            ai_reply = await ai_service.generate_reply(full_prompt, device_id=device_id)
            
            if not ai_reply or "Error" in ai_reply or "Ollama error" in ai_reply:
                logger.warning(f"🤖 [CHATBOT] AI failed or returned error for {phone}: {ai_reply}")
                return

            # 4. Send reply back to WhatsApp
            logger.info(f"🤖 [CHATBOT] Sending AI reply to {phone}...")
            result = send_whatsapp_message(
                device_id=device_id,
                phone=phone,
                message=ai_reply,
                jid=jid
            )
            
            if result.get("success"):
                # 5. Record the outgoing AI message in the inbox
                now = datetime.now(timezone.utc)
                
                # Fetch contact name if possible
                contact_name = phone
                prev_msg = db.query(WhatsAppInbox).filter(
                    WhatsAppInbox.phone_number == phone
                ).first()
                if prev_msg:
                    contact_name = prev_msg.contact_name

                sent_row = WhatsAppInbox(
                    device_id=device_id,
                    phone_number=phone,
                    contact_name=contact_name,
                    chat_type="individual",
                    incoming_message=ai_reply,   # The AI text
                    message_id=result.get("message_id"),
                    incoming_time=now,
                    is_read=True,
                    is_replied=True,
                    is_outgoing=True,
                    reply_message=ai_reply,
                    reply_time=now,
                )
                db.add(sent_row)
                db.commit()
                logger.info(f"🤖 [CHATBOT] AI reply successfully sent and recorded for {phone}")
            else:
                logger.error(f"🤖 [CHATBOT] Failed to send AI reply to {phone}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"🤖 [CHATBOT] Error in AI response logic: {e}")
        finally:
            db.close()

chatbot_service = ChatbotService()
