import json
from sqlalchemy import select
from db.session import SessionLocal
from models.busi_user import BusiUser
from models.device import Device, DeviceType, SessionStatus

def main():
    with SessionLocal() as session:
        # Get User
        result = session.execute(
            select(BusiUser).where(BusiUser.email == "amit.verma@testmail.com")
        )
        user = result.scalars().first()
        
        if not user:
            print("User not found")
            return
        
        # Get devices
        device_result = session.execute(
            select(Device).where(
                Device.busi_user_id == user.busi_user_id,
                Device.device_type.in_([DeviceType.web, DeviceType.mobile, DeviceType.desktop]),
                Device.session_status == SessionStatus.connected
            )
        )
        devices = device_result.scalars().all()
        
        output = []
        for d in devices:
            output.append({
                "device_name": d.device_name,
                "type": d.device_type.value,
                "status": d.session_status.value,
                "device_id": str(d.device_id),
                "last_active": d.last_active.strftime("%Y-%m-%d %H:%M:%S") if d.last_active else "N/A"
            })
            
        with open("connected_devices.json", "w") as f:
            json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
