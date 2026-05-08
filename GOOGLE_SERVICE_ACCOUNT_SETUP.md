# Google Service Account Setup Guide

## Problem
Your deployed backend is showing the error: "Could not load Service Account credentials" which prevents Google Sheets integration from working.

## Solution Steps

### 1. Create Google Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Go to **IAM & Admin** → **Service Accounts**
4. Click **Create Service Account**
5. Give it a name (e.g., "whatsapp-sheets-service")
6. Click **Create and Continue**
7. Skip roles for now, click **Done**
8. Find your service account and click on it
9. Go to **Keys** tab
10. Click **Add Key** → **Create new key**
11. Choose **JSON** and click **Create**
12. Download the JSON file

### 2. Enable Google Sheets API
1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Google Sheets API"
3. Click on it and click **Enable**
4. Also enable "Google Drive API" (required for spreadsheet access)

### 3. Update Credentials File
Replace the placeholder content in `credentials/google-service-account.json` with your actual service account JSON content:

```json
{
  "type": "service_account",
  "project_id": "your-actual-project-id",
  "private_key_id": "your-actual-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_ACTUAL_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
  "client_id": "your-actual-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
}
```

### 4. Share Your Google Sheets
For each Google Sheet you want to access:
1. Open the Google Sheet
2. Click **Share** button
3. Add the service account email (e.g., `your-service-account@your-project-id.iam.gserviceaccount.com`)
4. Give it **Viewer** or **Editor** permissions
5. Click **Send**

### 5. Deploy Changes
1. Commit the updated credentials file:
   ```bash
   git add credentials/google-service-account.json
   git commit -m "Add Google Service Account credentials"
   git push origin main
   ```

2. Your deployment will automatically pick up the new credentials file

### 6. Verify Setup
After deployment, check your backend logs to confirm:
- "Service Account JSON found at: /app/credentials/google-service-account.json"
- No more "Could not load Service Account credentials" errors

## Environment Variables (Optional)
The service account method doesn't require additional environment variables, but you can also add these to your `.env` if needed:

```bash
GOOGLE_SHEETS_CLIENT_ID=your-client-id
GOOGLE_SHEETS_CLIENT_SECRET=your-client-secret
GOOGLE_SHEETS_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

## Security Notes
- Never commit real credentials to public repositories
- The credentials file should be in your `.gitignore` for local development
- For production, consider using environment variables or secret management services
- Keep the private key secure and don't share it

## Troubleshooting
If you still get errors after setup:
1. Check that the JSON file is valid
2. Verify the service account email has access to the sheets
3. Ensure Google Sheets API is enabled in your project
4. Check deployment logs for specific error messages
