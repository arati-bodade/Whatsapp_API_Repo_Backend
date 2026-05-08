# Google Sheets → WhatsApp Messaging & Automation Module

## Overview

This module provides a complete integration between Google Sheets and WhatsApp messaging, allowing users to automate WhatsApp messages based on Google Sheets data changes. The system supports manual sending, automated triggers, and comprehensive tracking of message history.

## Architecture

### Backend Components

#### 1. Data Models (`models/google_sheet.py`)
- **GoogleSheet**: Stores connected Google Sheets information
- **GoogleSheetTrigger**: Defines automation triggers for sheets
- **GoogleSheetTriggerHistory**: Tracks all message sending attempts

#### 2. API Layer (`api/google_sheets.py`)
Complete REST API implementation with all required endpoints:

**Sheet Management:**
- `POST /api/google-sheets/connect` - Connect new Google Sheet
- `GET /api/google-sheets/` - List user's sheets
- `GET /api/google-sheets/{sheet_id}` - Get sheet details
- `PUT /api/google-sheets/{sheet_id}` - Update sheet
- `DELETE /api/google-sheets/{sheet_id}` - Disconnect sheet

**Trigger Management:**
- `POST /api/google-sheets/{sheet_id}/triggers` - Create trigger
- `GET /api/google-sheets/{sheet_id}/triggers` - List triggers
- `PUT /api/google-sheets/triggers/{trigger_id}` - Update trigger
- `DELETE /api/google-sheets/triggers/{trigger_id}` - Delete trigger

**Manual Actions:**
- `POST /api/google-sheets/{sheet_id}/manual-send` - Send messages manually
- `POST /api/google-sheets/{sheet_id}/sync` - Sync sheet data

**History & Analytics:**
- `GET /api/google-sheets/{sheet_id}/history` - Get sheet history
- `GET /api/google-sheets/triggers/{trigger_id}/history` - Get trigger history
- `GET /api/google-sheets/{sheet_id}/stats` - Get sheet statistics

**Webhook:**
- `POST /api/google-sheets/webhook` - Handle Google Sheets webhooks

#### 3. Service Layer (`services/google_sheets_service.py`)
Handles Google Sheets API integration:
- OAuth authentication flow
- Spreadsheet data retrieval
- Phone number validation
- Message template processing

#### 4. Automation Engine (`services/google_sheets_automation.py`)
Background processing system:
- Polling-based trigger execution
- Webhook event processing
- Message sending automation
- Error handling and retry logic

## Features

### Manual Send
1. **Sheet Selection**: Users can select from connected Google Sheets
2. **Device Selection**: Choose WhatsApp device for sending
3. **Template Configuration**: Define message templates with placeholders
4. **Phone Column Mapping**: Specify which column contains phone numbers
5. **Per-Row Results**: Track success/failure for each row

### Automated Triggers
1. **Trigger Types**:
   - **New Row**: Send messages when new rows are added
   - **Update Row**: Send messages when specific columns change
   - **Time-based**: Send messages at scheduled intervals

2. **Configuration Options**:
   - Message templates with dynamic placeholders
   - Phone column mapping
   - Trigger conditions (column/value pairs)
   - Polling intervals
   - Webhook URLs for real-time updates

3. **Processing Logic**:
   - Validates phone numbers automatically
   - Processes message templates with row data
   - Tracks execution history
   - Handles errors gracefully

### History & Analytics
1. **Comprehensive Tracking**:
   - All message attempts logged
   - Success/failure status
   - Error messages
   - Execution timestamps

2. **Statistics**:
   - Total sent/failed messages
   - Trigger performance metrics
   - Sheet activity overview

## Database Schema

### Tables

#### google_sheets
```sql
sheet_id (UUID, PK)
user_id (UUID, FK)
sheet_name (VARCHAR)
spreadsheet_id (VARCHAR)
status (ENUM: active|paused|error)
rows_count (INTEGER)
last_synced_at (TIMESTAMP)
connected_at (TIMESTAMP)
```

#### google_sheet_triggers
```sql
trigger_id (UUID, PK)
user_id (UUID, FK)
sheet_id (UUID, FK)
device_id (UUID, FK)
trigger_type (ENUM: new_row|update_row|time)
message_template (TEXT)
phone_column (VARCHAR)
trigger_column (VARCHAR)
trigger_value (VARCHAR)
webhook_url (VARCHAR)
polling_interval (INTEGER)
last_processed_row (INTEGER)
is_enabled (BOOLEAN)
last_triggered_at (TIMESTAMP)
created_at (TIMESTAMP)
```

#### google_sheet_trigger_history
```sql
history_id (UUID, PK)
sheet_id (UUID, FK)
trigger_id (UUID, FK)
device_id (UUID, FK)
row_number (INTEGER)
phone (VARCHAR)
message (TEXT)
status (ENUM: sent|failed)
executed_at (TIMESTAMP)
```

## Configuration

### Environment Variables
```env
# Google Sheets API
GOOGLE_SHEETS_CLIENT_ID=your_client_id
GOOGLE_SHEETS_CLIENT_SECRET=your_client_secret
GOOGLE_SHEETS_REDIRECT_URI=your_redirect_uri
GOOGLE_SHEETS_SCOPES=https://www.googleapis.com/auth/spreadsheets.readonly
GOOGLE_SHEETS_WEBHOOK_SECRET=your_webhook_secret
```

### Dependencies
```txt
google-api-python-client>=2.100.0
google-auth-httplib2>=0.1.1
google-auth-oauthlib>=1.0.0
```

## API Usage Examples

### Connect a Google Sheet
```bash
POST /api/google-sheets/connect
{
  "sheet_name": "Customer Contacts",
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
}
```

### Create a Trigger
```bash
POST /api/google-sheets/{sheet_id}/triggers
{
  "device_id": "uuid",
  "trigger_type": "new_row",
  "message_template": "Hello {name}, your order {order_id} is ready!",
  "phone_column": "A",
  "polling_interval": 5
}
```

### Manual Send
```bash
POST /api/google-sheets/{sheet_id}/manual-send
{
  "device_id": "uuid",
  "message_template": "Hi {name}, this is a test message",
  "phone_column": "A",
  "send_all": true
}
```

## Deployment

### Database Migration
```bash
# Apply migrations
alembic upgrade head

# Specific migrations
alembic upgrade 014_add_google_sheets_models
alembic upgrade 015_add_trigger_config_columns
```

### Background Tasks
The automation service starts automatically with the FastAPI application and runs:
- Polling loop every 5 minutes (configurable)
- Webhook processing for real-time updates
- Error handling and retry mechanisms

## Security Considerations

1. **OAuth Authentication**: Google Sheets access uses OAuth 2.0
2. **User Isolation**: Users can only access their own sheets and devices
3. **Input Validation**: All inputs validated using Pydantic schemas
4. **Phone Number Sanitization**: Phone numbers validated and formatted
5. **Rate Limiting**: Consider implementing rate limiting for API endpoints

## Error Handling

### Common Error Responses
- `401`: Not authenticated
- `403`: No permission / plan restricted
- `404`: Resource not found
- `400`: Validation error
- `500`: Internal server error

### Automation Errors
- Invalid phone numbers are logged but don't stop processing
- Network errors trigger retries
- Failed messages are tracked in history
- Polling continues despite individual failures

## Monitoring & Logging

### Log Levels
- `INFO`: Normal operations, trigger executions
- `WARNING`: Non-critical errors, webhook failures
- `ERROR`: Critical errors, database issues

### Key Metrics
- Trigger execution frequency
- Message success/failure rates
- API response times
- Background task health

## Future Enhancements

1. **Real-time Webhooks**: Replace polling with Google Sheets webhooks
2. **Advanced Templates**: Support for conditional templates
3. **Batch Processing**: Optimize for large sheets
4. **Analytics Dashboard**: Visual trigger performance metrics
5. **Multi-sheet Triggers**: Triggers spanning multiple sheets
6. **Message Scheduling**: Time-based message delivery

## Testing

### Unit Tests
```bash
pytest tests/test_google_sheets.py
```

### Integration Tests
```bash
pytest tests/test_google_sheets_integration.py
```

### API Testing
Use Swagger UI at `/docs` for interactive API testing.

## Support

For issues and questions:
1. Check application logs
2. Verify Google Sheets API credentials
3. Ensure database migrations are applied
4. Review trigger configurations
5. Check WhatsApp device connectivity
