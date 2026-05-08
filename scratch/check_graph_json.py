import sys
import os
sys.path.append(os.getcwd())

from db.session import SessionLocal
from models.busi_user import BusiUser
from api.user import get_dashboard_graph_data
import asyncio
from unittest.mock import MagicMock

async def mock_call(email):
    db = SessionLocal()
    try:
        user = db.query(BusiUser).filter(BusiUser.email == email).first()
        if not user: return
        
        # Mock the dependency
        token_payload = {"sub": str(user.busi_user_id)}
        
        result = await get_dashboard_graph_data(token_payload, db)
        print("Backend Response JSON:")
        import json
        print(json.dumps(result, indent=2))
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(mock_call('sushant.bodade@gmail.com'))
