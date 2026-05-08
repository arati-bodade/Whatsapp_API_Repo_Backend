import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import SessionLocal
from models.device import Device
from services.whatsapp_engine_service import WhatsAppEngineService

async def reconnect_device():
    db = SessionLocal()
    try:
        device = db.query(Device).filter(
            Device.device_id == "ce0105f5-f672-460f-a45a-776cb9a82ef3"
        ).first()
        
        if not device:
            print("Device not found in database")
            return
        
        print(f"Device: {device.device_name}")
        print(f"Session Status: {device.session_status}")
        print(f"Device Type: {device.device_type}")
        
        # Update device status to trigger reconnection
        device.session_status = "connecting"
        db.commit()
        
        # Trigger reconnection in engine
        engine_service = WhatsAppEngineService(db)
        try:
            result = engine_service._make_request_with_retry(
                "POST",
                f"/session/{device.device_id}/reconnect"
            )
            print(f"Reconnection request sent: {result.status_code if result else 'Failed'}")
        except Exception as e:
            print(f"Engine request failed: {e}")
        
        print("Reconnection initiated. Please check the device status in a few seconds.")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(reconnect_device())
