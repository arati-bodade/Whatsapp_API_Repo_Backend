#!/usr/bin/env python3
"""
Check device records in database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.device import Device
import os

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/whatsapp_platform')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print('=== DEVICE DATABASE RECORDS ===')
devices = db.query(Device).all()
for device in devices:
    print(f'Device ID: {device.device_id}')
    print(f'Name: {device.device_name}')
    print(f'User ID: {device.busi_user_id}')
    print(f'Session Status: {device.session_status}')
    print(f'Last Active: {device.last_active}')
    print(f'QR Last Generated: {device.qr_last_generated}')
    print('---')

print(f'Total devices in DB: {len(devices)}')
db.close()
