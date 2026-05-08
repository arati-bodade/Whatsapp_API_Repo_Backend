# Render Deployment Guide

## Production-Ready Configuration

This deployment has been optimized for Render's free tier to prevent startup hanging and restart loops.

## Architecture

The system consists of two services:
1. **Backend** (Python/FastAPI) - API server
2. **Engine** (Node.js/Express) - WhatsApp session management

Both services must be deployed for the system to work.

## Key Changes Made

### 1. render.yaml Configuration
- Created `render.yaml` with proper service configuration
- Set `autoDeploy: false` to prevent automatic deploys that cause restart loops
- Configured health check path to `/health`
- Set `WEB_CONCURRENCY=1` to prevent resource exhaustion
- Limited to 1 instance for free tier compatibility

### 2. Startup Optimization (main.py)
- **Removed trigger auto-start** on boot to prevent hanging
- Reduced auto-migration initial delay from 5s to 2s
- Reduced database statement timeouts from 10s to 5s
- Disabled keep-alive background task (can be re-enabled if needed)
- Made migrations run in background to prevent blocking startup

### 3. Startup Script (start.sh)
- Created `start.sh` for controlled startup
- Sets default PORT to 10000 if not specified
- Uses single worker configuration
- Includes error handling with `set -e`

### 4. Python Version (runtime.txt)
- Explicitly set Python 3.11.0 for consistency

## Deployment Steps

### Step 1: Deploy Engine Service (Required First)

1. **Push code to GitHub** (if not already done)
2. **Connect to Render**:
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `whatsapp-platform-api-engine` directory

3. **Configure Render Service**:
   - **Name**: whatsapp-platform-api-engine
   - **Region**: Oregon (or closest to your users)
   - **Branch**: main
   - **Runtime**: Node
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`
   - **Instance Type**: Free

4. **Environment Variables** (Optional):
   ```
   PORT=10000
   NODE_ENV=production
   ```

5. **Advanced Settings**:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Disable (to prevent restart loops)

6. **Wait for deployment** and verify:
   - Health check: https://whatsapp-platform-api-engine.onrender.com/health
   - Should return: `{"status":"ok","engine":"running",...}`

### Step 2: Deploy Backend Service

1. **Push code to GitHub** (if not already done)
2. **Connect to Render**:
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `whatsapp-platform-api-backend` directory

3. **Configure Render Service**:
   - **Name**: whatsapp-platform-api-backend
   - **Region**: Oregon (or closest to your users)
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `bash start.sh`
   - **Instance Type**: Free

4. **Environment Variables** (Required):
   ```
   DATABASE_URL=postgresql://user:pass@host/db
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   WHATSAPP_ENGINE_URL=https://whatsapp-platform-api-engine.onrender.com
   ```

5. **Advanced Settings**:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Disable (to prevent restart loops)

### Troubleshooting

#### Engine Service Issues

**HTTP 502 Errors from Engine**
- Verify the Engine service is deployed and running
- Check Engine health: https://whatsapp-platform-api-engine.onrender.com/health
- Ensure WHATSAPP_ENGINE_URL in Backend env vars is correct (no trailing slash)
- Check Engine logs for startup errors or crashes

**Engine Cold Start Delays**
- The free tier has a 15-minute inactivity timeout
- Cold starts can take 30-60 seconds
- The Backend has retry logic (15 attempts) to handle cold starts
- Consider upgrading to paid tier for always-on service

**Engine Returns HTML Instead of JSON**
- This is normal during cold starts - Render shows a loading page
- The Backend automatically retries when this happens
- Check logs for "RENDER_COLD_START" warnings

#### Backend Service Issues

#### Service Keeps Restarting
- Check logs for "Detected service running on port 10000"
- Ensure `autoDeploy` is set to `false` in render.yaml
- Verify PORT environment variable is set to 10000

#### Startup Hanging
- The auto-migrate task now runs in background
- Trigger auto-start is disabled (can be manually started via API)
- Database timeouts reduced to 5s to prevent hanging

#### Health Check Failing
- The `/health` endpoint should return `{"status": "healthy"}`
- Check if the service is actually running on port 10000
- Verify no firewall issues

## Manual Trigger Start (Optional)

If you need to start Google Sheets triggers after deployment:

```bash
# Via API
POST /api/google-sheets/triggers/start-all

# Or via admin panel (if available)
```

## Monitoring

- Check logs at: https://dashboard.render.com/web/your-service/logs
- Health check: https://your-service.onrender.com/health
- API docs: https://your-service.onrender.com/docs

## Post-Deployment Checklist

### Engine Service
- [ ] Engine service starts successfully
- [ ] Engine health check passes (/health)
- [ ] Engine responds to API requests
- [ ] WhatsApp sessions can be created

### Backend Service
- [ ] Backend service starts successfully
- [ ] Backend health check passes (/health)
- [ ] Database migrations complete
- [ ] API endpoints respond
- [ ] Backend can connect to Engine service
- [ ] Device sync works
- [ ] Background tasks running (if re-enabled)

## Notes

- The free tier has a 15-minute inactivity timeout
- Consider upgrading to paid tier for production use
- Monitor memory usage - free tier has 512MB RAM limit
- Database connection pool is optimized for 50 max connections
