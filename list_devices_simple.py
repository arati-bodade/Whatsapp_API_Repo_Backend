#!/usr/bin/env python3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.device import Device
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/whatsapp_platform')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print('All devices:')
devices = db.query(Device).all()
for device in devices:
    print(f'ID: {device.device_id}')
    print(f'Name: "{device.device_name}"')
    print(f'Status: {device.session_status}')
    print('---')

db.close()
