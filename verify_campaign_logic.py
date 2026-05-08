import asyncio
import logging
from unittest.mock import MagicMock
from models.campaign import CampaignStatus

logger = logging.getLogger("VERIFY")

class MockDevice:
    def __init__(self, name, warm=False):
        self.device_name = name
        self.device_id = f"dev_{name}"
        self.warm_status = warm

class MockTemplate:
    def __init__(self, content, delay=None):
        self.content = content
        self.delay_override = delay
        self.id = "mock_template_id"

async def mock_send(device, phone, content):
    print(f"[Device: {device.device_name}] Sending '{content}' to {phone}")
    await asyncio.sleep(0.1)
    return {"status": "sent"}

async def test_round_robin():
    devices = [MockDevice("Phone1"), MockDevice("Phone2", warm=True)]
    templates = [MockTemplate("Hello {Name}"), MockTemplate("Hi {Name}")]
    
    queue = [
        {"phone": "100", "row_data": {"Name": "Alice"}},
        {"phone": "101", "row_data": {"Name": "Bob"}},
        {"phone": "102", "row_data": {"Name": "Charlie"}},
        {"phone": "103", "row_data": {"Name": "Dave"}},
    ]
    
    device_index = 0
    template_index = 0
    
    print("Testing local Round-Robin Engine:")
    for recipient in queue:
        device = devices[device_index]
        template = templates[template_index]
        
        device_index = (device_index + 1) % len(devices)
        template_index = (template_index + 1) % len(templates)
        
        content = template.content.replace("{Name}", recipient["row_data"]["Name"])
        await mock_send(device, recipient["phone"], content)
        print(f" -> Device Index Shift: {device_index}, Template Index Shift: {template_index}")

if __name__ == "__main__":
    asyncio.run(test_round_robin())
