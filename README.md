# WhatsApp Platform Backend

A comprehensive WhatsApp automation and messaging platform API built with FastAPI, supporting both official and unofficial WhatsApp integration.

## 🚀 Features

- **User Management**: Multi-role system (reseller, business_owner)
- **WhatsApp Integration**: Support for both official and unofficial WhatsApp modes
- **Device Management**: WhatsApp Web device session management
- **Message Handling**: Send/receive messages with multiple types (OTP, TEXT, TEMPLATE, MEDIA)
- **Credit System**: Credit distribution and usage tracking
- **Analytics**: Reseller and business user analytics dashboard
- **Database Migrations**: Automated database schema management

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based authentication
- **Migration System**: Custom migration manager
- **API Documentation**: Auto-generated Swagger/OpenAPI docs

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mayur533/whatsapp_platform_backend.git
cd whatsapp_platform_backend
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Activate (Linux/Mac)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist:

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/whatsapp_platform

# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# WhatsApp Configuration (Optional)
WHATSAPP_WEBHOOK_URL=https://your-webhook-url.com
```

### 5. Database Setup

Run database migrations:

```bash
python migrations/migration_manager.py
```

### 6. Start the Server

```bash
python main.py
```

The server will start at `http://127.0.0.1:8000`

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## 🏗️ Project Structure

```
whatsapp_platform_backend/
├── api/                    # API route handlers
│   ├── users.py            # User management endpoints
│   ├── messages.py         # Message endpoints
│   ├── devices.py          # Device management
│   └── ...
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── message.py
│   ├── device.py
│   └── ...
├── schemas/                # Pydantic schemas
│   ├── user.py
│   ├── message.py
│   └── ...
├── services/               # Business logic
│   ├── user_service.py
│   ├── message_service.py
│   └── ...
├── db/                    # Database configuration
│   ├── base.py
│   ├── session.py
│   └── init_db.py
├── migrations/             # Database migrations
│   ├── migration_manager.py
│   ├── 001_initial_schema.py
│   └── ...
├── core/                   # Core configuration
│   └── config.py
├── main.py                 # Application entry point
└── requirements.txt        # Python dependencies
```

## 🔧 API Endpoints

### User Management
- `POST /api/users/` - Create new user
- `GET /api/users/{user_id}` - Get user by ID
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user

### Message Management
- `POST /api/messages/send` - Send message
- `GET /api/messages/{message_id}` - Get message by ID
- `GET /api/messages/` - Get user messages (paginated)
- `PATCH /api/messages/{message_id}/status` - Update message status

### Device Management
- `POST /api/devices/` - Create device
- `GET /api/devices/{device_id}` - Get device by ID
- `POST /api/devices/{device_id}/qr` - Generate QR code
- `POST /api/devices/{device_id}/connect` - Connect device

### Credit Management
- `POST /api/credit-distribution/` - Distribute credits
- `GET /api/credit-distribution/` - Get credit distributions

### Analytics
- `GET /api/reseller-analytics/` - Get reseller analytics
- `GET /api/message-usage/` - Get message usage logs

## 📊 Database Schema

### Core Tables
- **users**: User accounts with roles and wallet
- **messages**: Message tracking and status
- **devices**: WhatsApp device management
- **device_sessions**: Device session tracking
- **credit_distributions**: Credit allocation tracking
- **message_usage_logs**: Message usage analytics
- **reseller_analytics**: Reseller performance metrics
- **official_whatsapp_config**: Official WhatsApp settings
- **campaigns**: Core details of a Bulk Messaging campaign
- **campaign_devices**: Pivot table linking devices allocated sequentially to a given bulk campaign
- **message_templates**: Configured message structures for campaigns
- **message_logs**: Execution logs tracking success, retries, and failure points

## 🚀 Bulk Messaging System

The Bulk Messaging System is an automated queue-driven worker architecture designed for production scale operations without triggering anti-spam blocking limits.

### Architecture details:
- **Sessions**: The bulk message limit allocates distributions into 4 daily sessions. Each session runs automatically per user configurations.
- **Async Processing**: Campaigns run directly in the background using FastAPI background tasks and in-memory status tracking.
- **Round Robin Logic**: For up to 5 devices mapped simultaneously to a single campaign, the system orchestrates a clean rotating index mapping for load balancing. If `len(devices) = 1`, templates still rotate dynamically.
- **Template Rotation**: To bypass spam matching, `MessageTemplates` rotate recursively. Overlap overrides per-template specify strict deliberate delays via `delay_override`.
- **Warm Mode**: Dynamically scales sleep ranges (8-15 seconds) over standard 3-7 delay when `warm_status` flags apply.
- **Rate Limiting**: Strict 1-message-per-second minimum delay is enforced to ensure stability.
- **Pause/Resume**: Instantly halts dequeues globally altering in-memory states saving execution bounds gracefully via explicit REST actions.
- **WebSocket Progress**: Binds directly onto connected clients broadcasting live counts tracking `total_recipients`, `sent_count`, `failed_count`, and `remaining_count`.


## 🔐 Authentication

The API uses JWT-based authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## 📝 Example Usage

### Create a Business User

```bash
curl -X POST "http://127.0.0.1:8000/api/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "business_owner",
    "status": "active",
    "parent_reseller_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "profile": {
      "name": "Rajesh Kumar",
      "username": "rajesh_tech",
      "email": "rajesh.kumar@techsolutions.com",
      "phone": "9876543210",
      "password": "SecurePass123!"
    },
    "business": {
      "business_name": "TechSolutions India Pvt Ltd",
      "business_description": "Leading software development company",
      "erp_system": "SAP",
      "gstin": "27AAAPL1234C1ZV"
    },
    "address": {
      "full_address": "123, Tech Park, Phase 2, Hinjewadi, Pune - 411057",
      "pincode": "411057",
      "country": "India"
    },
    "wallet": {
      "credits_allocated": 5000,
      "credits_used": 0,
      "credits_remaining": 5000
    },
    "whatsapp_mode": "unofficial"
  }'
```

### Send a Message

```bash
curl -X POST "http://127.0.0.1:8000/api/messages/send?user_id=760e3d35-7efd-4774-b064-27d9d0e9c66b" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_number": "+919876543210",
    "message_type": "TEXT",
    "message_body": "Hello! This is a test message from our WhatsApp platform.",
    "mode": "UNOFFICIAL"
  }'
```

### Create a Device

```bash
curl -X POST "http://127.0.0.1:8000/api/devices/" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Android Phone",
    "device_type": "mobile"
  }'
```

## 🔄 Database Migrations

The project uses a custom migration system. To run migrations:

```bash
python migrations/migration_manager.py
```

This will:
1. Create the migrations table if it doesn't exist
2. Check for pending migrations
3. Apply migrations in order
4. Track applied migrations

## 🐛 Development

### Running in Development Mode

```bash
python main.py
```

The server will automatically reload on file changes.

### Database Migrations

When making database changes:
1. Create a new migration file in `migrations/` directory
2. Name it with sequential number: `008_new_feature.py`
3. Implement `upgrade()` and `downgrade()` functions
4. Run migration manager

### Adding New API Endpoints

1. Create Pydantic schemas in `schemas/`
2. Implement business logic in `services/`
3. Add route handlers in `api/`
4. Include router in `main.py`

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=.
```

## 📝 Logging

The application uses Python's built-in logging. Configure logging levels in `core/config.py`.

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

Set these in production:
- `DATABASE_URL`: Production database connection
- `SECRET_KEY`: Secure JWT secret
- `ENVIRONMENT`: Set to `production`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the migration logs for database issues

## 🔮 Roadmap

- [ ] WebSocket support for real-time message updates
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Rate limiting and quota management
- [ ] Message templates management
- [ ] File upload support for media messages
- [ ] Webhook configuration for message events
- [ ] Enhanced security features
- [ ] Performance optimization
- [ ] Monitoring and alerting

---

**Built with ❤️ by [mayur533](https://github.com/mayur533)**
