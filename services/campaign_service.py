import asyncio
import json
import logging
import traceback
from typing import List, Dict, Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from core.config import settings
from core.campaign_state import campaign_tracker
from models.campaign import Campaign, CampaignDevice, MessageTemplate, MessageLog, CampaignStatus
from models.device import Device
from schemas.campaign import CampaignCreateRequest, CampaignResponse
from workers.bulk_messaging_worker import campaign_worker
from workers.worker_manager import is_worker_active, register_worker

logger = logging.getLogger("CAMPAIGN_SERVICE")

class CampaignService:
    def __init__(self, db: Session):
        self.db = db

    def create_campaign(self, user_id: str, request_data: CampaignCreateRequest) -> Campaign:
        try:
            # Check max devices validation
            if len(request_data.device_ids) > 5:
                raise HTTPException(status_code=400, detail="Maximum 5 devices allowed per campaign")
            
            # Check user owns devices
            for device_id in request_data.device_ids:
                device = self.db.query(Device).filter(Device.device_id == str(device_id), Device.busi_user_id == str(user_id), Device.is_active == True).first()
                if not device:
                    raise HTTPException(status_code=400, detail=f"Device {device_id} not found or unauthorized")

            # Create Campaign
            campaign = Campaign(
                busi_user_id=str(user_id),
                sheet_id=request_data.sheet_id,
                source_file_url=request_data.source_file_url, # 🔥 NEW
                name=request_data.name,
                status=CampaignStatus.PENDING,
                scheduled_at=request_data.scheduled_at, # 🔥 NEW: Save global schedule
                media_url=request_data.media_url,
                media_type=request_data.media_type
            )
            self.db.add(campaign)
            self.db.flush()

            # Add Devices
            for device_id in request_data.device_ids:
                cd = CampaignDevice(campaign_id=str(campaign.id), device_id=str(device_id))
                self.db.add(cd)

            # Add Templates
            for t in request_data.templates:
                mt = MessageTemplate(
                    campaign_id=str(campaign.id), 
                    content=t.content, 
                    media_url=t.media_url,
                    media_type=t.media_type,
                    delay_override=t.delay_override
                )
                self.db.add(mt)

            self.db.commit()
            self.db.refresh(campaign)
            return campaign
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def start_campaign(self, user_id: str, campaign_id: str, rows_data: List[Dict[str, Any]]):
        """
        Start a campaign: process rows directly, set status to running, spawn worker task.
        Uses worker_manager for concurrency control.
        """
        try:
            campaign = self.db.query(Campaign).filter(Campaign.id == str(campaign_id), Campaign.busi_user_id == str(user_id)).first()
            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")

            if campaign.status not in [CampaignStatus.PENDING, CampaignStatus.PAUSED]:
                raise HTTPException(status_code=400, detail=f"Cannot start campaign in state {campaign.status.value}")

            # 1. Check if worker is already active via worker_manager
            if await is_worker_active(str(campaign_id)):
                logger.info(f"Campaign {campaign_id} already has an active worker task.")
                # Ensure DB status is synced if tracker/registry says it's running
                if campaign.status != CampaignStatus.RUNNING:
                    campaign.status = CampaignStatus.RUNNING
                    self.db.commit()
                return {"status": "success", "message": "Campaign is already running."}

            # 2. Prepare recipients if Pending
            if campaign.status == CampaignStatus.PENDING:
                # Basic sync logic
                if not rows_data:
                     raise HTTPException(status_code=400, detail="No recipient data found for this campaign")
                
                campaign.total_recipients = len(rows_data)
                self.db.commit()

            # 🔥 NEW: Initialize the in-memory tracker for the worker
            # The campaign_worker expects this to exist before it starts
            campaign_tracker[str(campaign_id)] = {
                "status": CampaignStatus.RUNNING.value,
                "recipients": rows_data,
                "total": len(rows_data),
                "remaining": len(rows_data),
                "sent": 0,
                "failed": 0
            }
            logger.info(f"Initialized campaign tracker for {campaign_id} with {len(rows_data)} recipients")

            campaign.status = CampaignStatus.RUNNING
            self.db.commit()

            # 3. Create Background Worker Task
            task = asyncio.create_task(campaign_worker(str(campaign.id)))
            await register_worker(str(campaign_id), task)
            
            return {"status": "success", "message": "Campaign started in background"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error starting campaign {campaign_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def pause_campaign(self, user_id: str, campaign_id: str):
        try:
            campaign = self.db.query(Campaign).filter(Campaign.id == str(campaign_id), Campaign.busi_user_id == str(user_id)).first()
            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")

            # 🔥 GRACEFUL STOP: Allow stopping even if not strictly 'Running' (e.g., already paused)
            if campaign.status == CampaignStatus.PAUSED:
                return {"status": "success", "message": "Campaign is already stopped."}
            
            if campaign.status in [CampaignStatus.COMPLETED, CampaignStatus.FAILED]:
                return {"status": "success", "message": "Campaign has already finished."}
            
            # For other states (like PENDING), we still want to allow stopping/cancelling
            if campaign.status not in [CampaignStatus.RUNNING, CampaignStatus.PENDING]:
                raise HTTPException(status_code=400, detail=f"Cannot stop campaign in state {campaign.status}")

            # Update tracker status first (worker checks this on next iteration)
            if str(campaign_id) in campaign_tracker:
                campaign_tracker[str(campaign_id)]["status"] = CampaignStatus.PAUSED.value
                
            campaign.status = CampaignStatus.PAUSED
            self.db.commit()
            return {"status": "success", "message": "Campaign paused"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error pausing campaign {campaign_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def resume_campaign(self, user_id: str, campaign_id: str):
        try:
            campaign = self.db.query(Campaign).filter(Campaign.id == str(campaign_id), Campaign.busi_user_id == str(user_id)).first()
            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")

            if campaign.status == CampaignStatus.RUNNING:
                return {"status": "success", "message": "Campaign is already running."}
            
            if campaign.status not in [CampaignStatus.PAUSED, CampaignStatus.PENDING]:
                raise HTTPException(status_code=400, detail=f"Cannot start campaign in state {campaign.status}")

            # Update tracker status first
            if str(campaign_id) in campaign_tracker:
                campaign_tracker[str(campaign_id)]["status"] = CampaignStatus.RUNNING.value
            else:
                return {"status": "error", "message": "Campaign tracker lost. Cannot resume."}

            campaign.status = CampaignStatus.RUNNING
            self.db.commit()

            # Re-spawn task if not already active
            if not await is_worker_active(str(campaign_id)):
                task = asyncio.create_task(campaign_worker(str(campaign.id)))
                await register_worker(str(campaign_id), task)
            
            return {"status": "success", "message": "Campaign resumed"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resuming campaign {campaign_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_campaign_status(self, user_id: str, campaign_id: str):
        try:
            campaign = self.db.query(Campaign).filter(Campaign.id == str(campaign_id), Campaign.busi_user_id == str(user_id)).first()
            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")

            status = campaign.status.value if hasattr(campaign.status, 'value') else campaign.status
            total_recipients = campaign.total_recipients
            sent_count = campaign.sent_count
            failed_count = campaign.failed_count
            
            remaining = 0
            tracker = campaign_tracker.get(str(campaign_id))
            if tracker:
                remaining = tracker.get("remaining", 0)
                tracker_status = tracker.get("status")
                if tracker_status:
                    status = tracker_status

            return {
                "campaign_id": str(campaign.id),
                "status": status,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_recipients": total_recipients,
                "remaining": remaining
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching campaign status: {e}")
            raise HTTPException(status_code=500, detail="Internal server error fetching status")

    def get_user_campaigns(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Campaign]:
        try:
            return self.db.query(Campaign).filter(
                Campaign.busi_user_id == str(user_id)
            ).order_by(Campaign.created_at.desc()).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing user campaigns: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve campaigns")

    def delete_campaign(self, user_id: str, campaign_id: str) -> bool:
        try:
            campaign = self.db.query(Campaign).filter(
                Campaign.id == campaign_id,
                Campaign.busi_user_id == user_id
            ).first()
            if not campaign:
                return False
            self.db.delete(campaign)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting campaign: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete campaign")
