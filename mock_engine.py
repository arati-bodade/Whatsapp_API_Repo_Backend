#!/usr/bin/env python3

"""
Mock WhatsApp Engine for testing purposes
Run this to simulate a working WhatsApp Engine on localhost:3002
"""

from flask import Flask, request, jsonify
import uuid
from datetime import datetime

app = Flask(__name__)

# Mock device storage
devices = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/session/<device_id>/status', methods=['GET'])
def device_status(device_id):
    # Return connected for any device
    return jsonify({
        "status": "connected",
        "device_id": device_id,
        "last_seen": datetime.now().isoformat()
    })

@app.route('/session/<device_id>/message', methods=['POST'])
def send_message(device_id):
    data = request.get_json()
    
    # Mock successful send
    return jsonify({
        "success": True,
        "message_id": str(uuid.uuid4()),
        "status": "sent",
        "to": data.get("to"),
        "message": data.get("message"),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/session/<device_id>/qr', methods=['GET'])
def get_qr(device_id):
    # Mock QR code
    return jsonify({
        "qr_code": f"mock_qr_{device_id}_{datetime.now().timestamp()}",
        "status": "qr_generated",
        "expires_at": (datetime.now().timestamp() + 300)  # 5 minutes
    })

if __name__ == '__main__':
    print("🚀 Starting Mock WhatsApp Engine on localhost:3002")
    print("📱 This simulates a working WhatsApp Engine for testing")
    print("🔗 Health: http://localhost:3002/health")
    print("🔗 Device Status: http://localhost:3002/session/<device_id>/status")
    print("🔗 Send Message: POST http://localhost:3002/session/<device_id>/message")
    print("\n⚠️  This is a MOCK engine - no real WhatsApp messages will be sent!")
    print("⚠️  Use for development testing only!")
    
    app.run(host='localhost', port=3002, debug=True)
