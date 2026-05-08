# WhatsApp Platform Backend

## 🚀 Production Deployment Guide

### Prerequisites
- Python 3.8+ installed
- PostgreSQL database running and accessible
- All dependencies installed (see requirements.txt)

### Quick Start

#### Option 1: Direct Start
```bash
python main.py
```

#### Option 2: Development with Reload
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option 3: Production Deployment Script
```bash
python deploy.py
```

### Environment Variables
Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql://whatsapp_patform_user:cCR4XEVKwlV3XdoOmWbGw6rdNTyBOppm@dpg-d5fp9qlactks739q3o20-a.oregon-postgres.render.com/whatsapp_patform
SECRET_KEY=your-super-secret-key-here-change-in-production
DEBUG=false
```

### API Endpoints
- **Main API**: http://127.0.0.1:8000
- **Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

### Database Status
- ✅ Connected and operational
- ✅ All tables created and populated
- ✅ Schema migrations applied

### Features
- 📱 WhatsApp API Integration
- 👥 User Management (Resellers & Business Users)
- 🔐 Device Management
- 📊 Analytics & Reporting
- 💳 Credit Distribution System
- 📨 Message Usage Tracking

### Security
- 🔒 JWT Authentication
- 🛡️ SQL Injection Protection
- 🔐 Input Validation
- 🚫 CORS Configuration (configure for production)

## 🎉 Ready for Production!

The WhatsApp Platform Backend is fully operational and ready to serve requests.
