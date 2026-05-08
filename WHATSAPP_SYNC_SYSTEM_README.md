# WhatsApp CRM Message Synchronization System

A production-ready WhatsApp CRM inbox system using Baileys WhatsApp Web API engine and FastAPI backend. This system provides real-time message synchronization with proper event handling, ensuring that mobile WhatsApp unread messages are preserved and displayed in the dashboard.

## 🚀 Features

### Core Functionality
- **Real-time Message Sync**: Uses Baileys events (`chats.set`, `messages.set`, `messages.upsert`)
- **Message Deduplication**: Prevents duplicate messages using unique message IDs
- **Device Isolation**: Each user sees only their own device messages
- **Backward Compatibility**: Works with existing WhatsAppInbox table
- **Unread Message Preservation**: Messages received before QR scan are preserved and shown

### Database & Storage
- **Enhanced Schema**: New `whatsapp_messages` table with proper indexing
- **Optimized Queries**: Efficient conversation grouping and unread counts
- **Message History**: Complete message history with metadata
- **Media Support**: Handles text, images, documents, and other media types

### Real-time Features
- **WebSocket Support**: Live updates for new messages and read status
- **Connection Management**: Automatic reconnection and status updates
- **Event Broadcasting**: Real-time notifications to connected clients

### API Endpoints
- **Message Storage**: `/api/messages/store` - Store messages with deduplication
- **Conversations**: `/api/messages/conversations` - Get conversation summaries
- **Chat History**: `/api/messages/conversation/{phone}` - Get full conversation
- **Read Management**: `/api/messages/mark-read` - Mark conversations as read
- **Unread Count**: `/api/messages/unread-count` - Get unread message counts

## 📁 File Structure

```
wh-api-backend-vikas/
├── models/
│   ├── whatsapp_messages.py          # New message storage model
│   ├── whatsapp_inbox.py           # Legacy message model (preserved)
│   └── device.py                  # Updated with message relationships
├── services/
│   ├── baileys_message_sync_service.py    # Core Baileys sync service
│   ├── message_sync_initiator.py          # Sync initiation on connection
│   └── websocket_manager.py              # Real-time WebSocket management
├── api/
│   ├── messages.py                 # Message storage and retrieval APIs
│   ├── webhooks.py               # Enhanced webhook handlers
│   ├── websocket.py              # WebSocket endpoints
│   └── auth_ws.py              # WebSocket authentication
├── migrations/
│   └── 018_add_whatsapp_messages_table.py  # Database migration
└── test_message_sync_system.py   # Comprehensive test suite
```

## 🛠️ Installation & Setup

### 1. Database Migration

Run the migration to create the new `whatsapp_messages` table:

```bash
# Using Alembic
alembic upgrade head

# Or run the migration directly
python -c "
from migrations.018_add_whatsapp_messages_table import upgrade
upgrade()
"
```

### 2. Update API Routes

Add the new API routes to your main application:

```python
# main.py
from api.messages import router as messages_router
from api.websocket import router as websocket_router

app.include_router(messages_router)
app.include_router(websocket_router)
```

### 3. Configure Environment

Ensure your environment variables are set:

```env
WHATSAPP_ENGINE_BASE_URL=http://localhost:8001  # Baileys engine URL
API_BASE_URL=http://localhost:8000               # Your API base URL
SECRET_KEY=your-secret-key
ALGORITHM=HS256
```

### 4. Update Main App

Include the new modules in your main application:

```python
# main.py
from services.baileys_message_sync_service import baileys_sync_service
from services.websocket_manager import websocket_manager
from services.message_sync_initiator import message_sync_initiator
```

## 🔧 How It Works

### Initial Sync Process

1. **QR Code Scan**: User scans QR code to connect WhatsApp
2. **Connection Event**: Webhook receives `connection.update` event
3. **Sync Initiation**: System starts Baileys message synchronization
4. **Chat Fetch**: Fetches all chats using `chats.set` event
5. **Message History**: Retrieves historical messages using `messages.set`
6. **Storage**: Stores messages in database with deduplication

### Real-time Updates

1. **New Message**: Baileys sends `messages.upsert` event
2. **Webhook**: API receives event via `/api/webhooks/whatsapp/{device_id}`
3. **Processing**: Message is processed and stored
4. **Broadcast**: WebSocket notification sent to connected clients
5. **Dashboard**: Real-time update appears in manage-replies dashboard

### Message Flow

```
WhatsApp Mobile → Baileys Engine → Webhook → API → Database → WebSocket → Dashboard
```

## 📊 Database Schema

### WhatsAppMessages Table

```sql
CREATE TABLE whatsapp_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(device_id),
    message_id VARCHAR(255) NOT NULL UNIQUE,
    remote_jid VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    contact_name VARCHAR(255),
    message TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    from_me BOOLEAN NOT NULL DEFAULT FALSE,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    chat_type VARCHAR(20) DEFAULT 'individual',
    media_url TEXT,
    thumbnail_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_whatsapp_messages_message_id ON whatsapp_messages(message_id);
CREATE INDEX idx_whatsapp_messages_device_id ON whatsapp_messages(device_id);
CREATE INDEX idx_whatsapp_messages_phone ON whatsapp_messages(phone);
CREATE INDEX idx_whatsapp_messages_device_phone_time ON whatsapp_messages(device_id, phone, timestamp);
CREATE INDEX idx_whatsapp_messages_unread ON whatsapp_messages(device_id, is_read, from_me, timestamp);
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_message_sync_system.py
```

The test suite validates:
- Database schema and relationships
- Message storage with deduplication
- Baileys event handling
- Conversation queries
- WebSocket broadcasting
- Sync initiation

## 📱 Usage Examples

### Store a Message

```python
import requests

message_data = {
    "device_id": "your-device-id",
    "phone": "+1234567890",
    "message_id": "unique-message-id",
    "message": "Hello from WhatsApp!",
    "from_me": False,
    "contact_name": "John Doe"
}

response = requests.post(
    "http://localhost:8000/api/messages/store",
    json=message_data,
    headers={"Authorization": "Bearer your-token"}
)
```

### Get Conversations

```python
response = requests.get(
    "http://localhost:8000/api/messages/conversations",
    headers={"Authorization": "Bearer your-token"},
    params={"limit": 50}
)

conversations = response.json()["data"]
for conv in conversations:
    print(f"{conv['phone']}: {conv['last_message']} (Unread: {conv['unread_count']})")
```

### WebSocket Connection

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/replies/${deviceId}?token=${authToken}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'new_message':
            console.log('New message:', data.data);
            break;
        case 'messages_read':
            console.log('Messages marked as read:', data.phone);
            break;
        case 'connection_status':
            console.log('Device status:', data.status);
            break;
    }
};
```

## 🔍 Troubleshooting

### Common Issues

1. **Messages not appearing after QR scan**
   - Check if device status is "connected"
   - Verify webhook configuration in Baileys engine
   - Check logs for sync initiation errors

2. **Duplicate messages**
   - System automatically deduplicates using message_id
   - Check if message_id is being set correctly

3. **WebSocket not connecting**
   - Verify authentication token is valid
   - Check if device belongs to the user
   - Ensure WebSocket endpoint is accessible

### Debug Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Key log prefixes to watch:
- `[BAILEYS]` - Baileys event handling
- `[SYNC]` - Message synchronization
- `[WS]` - WebSocket operations
- `[REPLIES]` - Dashboard operations

## 🚀 Performance Considerations

### Database Optimization
- Indexes are optimized for common query patterns
- Consider partitioning by device_id for large datasets
- Use connection pooling for high concurrency

### Memory Management
- WebSocket connections are properly cleaned up
- Message batches are processed efficiently
- Database sessions are properly closed

### Scaling
- Supports multiple devices per user
- Horizontal scaling with multiple API instances
- Redis can be added for WebSocket session sharing

## 🔄 Migration from Legacy System

The system maintains backward compatibility:

1. **Legacy Support**: Existing `whatsapp_inbox` table continues to work
2. **Unified Queries**: Dashboard combines data from both tables
3. **Gradual Migration**: Can migrate data gradually
4. **Feature Parity**: All existing features are preserved

## 📝 API Reference

### Message Store Endpoint

**POST** `/api/messages/store`

Store a WhatsApp message with deduplication.

**Request Body:**
```json
{
    "device_id": "uuid",
    "phone": "+1234567890",
    "message_id": "unique-id",
    "message": "Message content",
    "timestamp": "2025-01-11T12:00:00Z",
    "from_me": false,
    "contact_name": "Contact Name",
    "message_type": "text"
}
```

### Conversations Endpoint

**GET** `/api/messages/conversations`

Get conversation summaries with unread counts.

**Query Parameters:**
- `device_id` (optional): Filter by specific device
- `limit` (default: 50): Number of conversations

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "phone": "+1234567890",
            "contact_name": "John Doe",
            "last_message": "Last message content",
            "last_message_time": "2025-01-11T12:00:00Z",
            "unread_count": 3,
            "total_messages": 10
        }
    ]
}
```

## 🤝 Contributing

When contributing to this system:

1. **Test Changes**: Run the test suite before submitting
2. **Maintain Compatibility**: Don't break existing functionality
3. **Update Documentation**: Keep this README current
4. **Follow Patterns**: Use existing code patterns and conventions

## 📄 License

This WhatsApp CRM system is part of the larger WhatsApp Platform API project.

---

**Note**: This system is designed to work with the Baileys WhatsApp Web API engine. Ensure your engine is properly configured and accessible before deploying this system.
