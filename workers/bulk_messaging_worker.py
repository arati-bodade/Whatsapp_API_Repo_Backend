import asyncio
import logging
import random
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from core.config import settings
from core.campaign_state import campaign_tracker
from db.db_session import SessionLocal
from models.campaign import Campaign, CampaignStatus, MessageLog
from models.device import Device
from services.unified_service import UnifiedWhatsAppService
from workers.worker_manager import unregister_worker
from utils.template_engine import render_template

logger = logging.getLogger("CAMPAIGN_WORKER")

async def campaign_worker(campaign_id: str):
    """
    Independent worker task for a specific campaign.
    Ensures DB session isolation by creating and closing sessions inside the loop.
    """
    worker_id = str(uuid.uuid4())
    logger.info(f"🚀 Worker {worker_id} started for campaign {campaign_id}")

    try:
        while True:
            # 1. Use context manager for automatic session cleanup
            with SessionLocal() as db:
                try:
                    # Refresh campaign and tracker status from DB/InMemory
                    tracker = campaign_tracker.get(campaign_id)
                    if not tracker:
                        logger.warning(f"No tracker found for campaign {campaign_id}. Worker exiting.")
                        break

                    # Check if campaign is PAUSED or stopped
                    if tracker["status"] == CampaignStatus.PAUSED.value:
                        logger.info(f"⏹️ Campaign {campaign_id} PAUSED. Worker stopping.")
                        break
                    
                    if tracker["status"] in [CampaignStatus.COMPLETED.value, CampaignStatus.FAILED.value]:
                        logger.info(f"✅ Campaign {campaign_id} already {tracker['status']}. Worker exiting.")
                        break
                    
                    # Fetch static campaign details needed for this iteration
                    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
                    if not campaign:
                        logger.error(f"Campaign {campaign_id} not found in DB.")
                        break

                    # 2. Check Global Scheduling (IST)
                    if campaign.scheduled_at:
                        ist_tz = timezone(timedelta(hours=5, minutes=30))
                        now_ist = datetime.now(timezone.utc).astimezone(ist_tz)
                        
                        # 🔥 FIX: Handle timezone-aware vs naive timestamps from Postgres
                        # If Postgres Column is DateTime(timezone=True), it often returns UTC
                        target_time = campaign.scheduled_at
                        
                        # If it's UTC, it might have been a naive local time saved as UTC
                        # We should treat the DATE and TIME parts as intended locally
                        if target_time.tzinfo and target_time.tzinfo != ist_tz:
                            # Convert to IST but preserve the intended hour/minute if it was saved naively
                            # Actually, better to just convert the UTC to IST 
                            # and see if it's in the past
                            target_ist = target_time.astimezone(ist_tz)
                        else:
                            target_ist = target_time.replace(tzinfo=ist_tz)
                        
                        if now_ist < target_ist:
                            # logger.info(f"⏳ Campaign {campaign_id} scheduled for {target_ist}. Now: {now_ist}. Result: {now_ist < target_ist}")
                            await asyncio.sleep(10)
                            continue  # Context manager will close session

                    # 3. Dequeue next recipient
                    if not tracker.get("recipients"):
                        # Double check if we should be COMPLETED
                        campaign.status = CampaignStatus.COMPLETED
                        db.commit()
                        tracker["status"] = CampaignStatus.COMPLETED.value
                        logger.info(f"✅ Campaign {campaign_id} finished all recipients.")
                        
                        # 🔥 DEDUCT CREDITS AFTER LOOP (Campaign flow)
                        if campaign.sent_count > 0:
                            from services.message_usage_service import MessageUsageService
                            try:
                                message_usage_service = MessageUsageService(db)
                                message_usage_service.deduct_credits(
                                    busi_user_id=str(campaign.busi_user_id),
                                    message_id=f"campaign-{campaign_id}",
                                    amount=campaign.sent_count,
                                    source="campaign"
                                )
                                logger.info(f"💰 Deducted {campaign.sent_count} credits for campaign {campaign_id}")
                            except Exception as credit_err:
                                logger.error(f"⚠️ Credit deduction failed for campaign {campaign_id}: {str(credit_err)}")
                        
                        break

                    recipient_data = tracker["recipients"].pop(0)
                    tracker["remaining"] = len(tracker["recipients"])
                    
                    phone = recipient_data.get("phone")
                    row_data = recipient_data.get("row_data", {})
                    
                    if not phone:
                        # Skip empty phone numbers but count as failed
                        campaign.failed_count += 1
                        logger.warning(f"📊 Campaign {campaign_id}: Empty phone number -> ❌")
                        continue

                    # Prepare devices and templates (Round Robin style based on count)
                    # Note: We fetch these from campaign relationship which is now session-bound
                    devices = [cd.device for cd in campaign.devices if cd.device]
                    templates = list(campaign.templates)

                    if not devices or not templates:
                        logger.error(f"Campaign {campaign_id} lacks devices or templates.")
                        tracker["status"] = CampaignStatus.FAILED.value
                        campaign.status = CampaignStatus.FAILED
                        db.commit()
                        break

                    sent_so_far = campaign.sent_count + campaign.failed_count
                    device = devices[sent_so_far % len(devices)]
                    template = templates[sent_so_far % len(templates)]

                    # Content formatting using render_template utility
                    content = render_template(template.content, row_data)

                    # Rate limiting / Delay
                    delay = template.delay_override
                    if delay is None:
                        is_warm = getattr(device, 'warm_status', False)
                        delay = random.randint(settings.WARM_MIN_DELAY, settings.WARM_MAX_DELAY) if is_warm else random.randint(settings.MIN_DELAY, settings.MAX_DELAY)
                    
                    actual_delay = max(0.5, delay)
                    await asyncio.sleep(actual_delay)

                    # Send Message
                    success = False
                    error_msg = None
                    
                    media_url = campaign.media_url or template.media_url
                    media_type = campaign.media_type or (template.media_type or "image")
                    
                    unified_service = UnifiedWhatsAppService(db)
                    try:
                        if media_url:
                            result = await unified_service.send_media_message(
                                device_id=str(device.device_id),
                                to=phone,
                                caption=content,
                                media_url=media_url,
                                media_type=media_type,
                                skip_credit_deduction=True,
                                authenticated_user_id=str(campaign.busi_user_id)
                            )
                        else:
                            result = await unified_service.send_message(
                                device_id=str(device.device_id),
                                to=phone,
                                message=content,
                                skip_credit_deduction=True,
                                authenticated_user_id=str(campaign.busi_user_id)
                            )
                        
                        if result and result.get("success"):
                            success = True
                            campaign.sent_count += 1
                        else:
                            error_msg = result.get("error", "Unknown error") if result else "No response"
                            # Check if this is a validation error or non-WhatsApp number
                            if result:
                                if result.get("not_on_whatsapp"):
                                    error_msg = "Number not registered on WhatsApp"
                                elif "Invalid phone number format" in error_msg:
                                    error_msg = "Invalid phone number format"
                            campaign.failed_count += 1
                    except Exception as e:
                        error_msg = str(e)
                        campaign.failed_count += 1
                        logger.error(f"Error sending message to {phone}: {e}")

                    # Log Result
                    log_entry = MessageLog(
                        campaign_id=campaign_id,
                        device_id=device.device_id,
                        recipient=phone,
                        template_id=template.id,
                        status="success" if success else f"failed: {error_msg}",
                        retry_count=0,
                        response_time=int(actual_delay * 1000)
                    )
                    db.add(log_entry)
                    
                    # Commit iteration
                    db.commit()
                    logger.info(f"📊 Campaign {campaign_id}: {phone} -> {'✅' if success else '❌'}")

                except Exception as e:
                    logger.error(f"Error in worker loop iteration: {e}")
                    db.rollback()
                    # Context manager will close session automatically

            # yield control back to event loop
            await asyncio.sleep(0.01)

    except asyncio.CancelledError:
        logger.info(f"🛑 Worker {worker_id} for campaign {campaign_id} CANCELLED")
    except Exception as e:
        logger.error(f"🔥 Worker {worker_id} CRASHED: {e}\n{traceback.format_exc()}")
    finally:
        # Cleanup Registry
        await unregister_worker(campaign_id)
        logger.info(f"🏁 Worker {worker_id} for campaign {campaign_id} STOPPED")
