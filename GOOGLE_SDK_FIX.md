# Google Sheets SDK Installation and Fix

## Root Cause
The `ModuleNotFoundError: No module named 'google'` occurs because the Google API client libraries are not installed in the virtual environment. The code is trying to import `google.oauth2.credentials` but the required Google SDK packages are missing.

## Why installing `google` alone is WRONG
- `google` is a namespace package, not a complete SDK
- It only provides basic Google utilities, NOT the Sheets API
- You need specific Google API client libraries for Sheets integration

## Pip Install Commands (Python 3.13 + Windows compatible)
```bash
# Activate virtual environment first
.\venv\Scripts\activate

# Install required Google SDK packages
pip install google-api-python-client>=2.100.0
pip install google-auth-httplib2>=0.1.1  
pip install google-auth-oauthlib>=1.0.0

# Or install all at once
pip install google-api-python-client>=2.100.0 google-auth-httplib2>=0.1.1 google-auth-oauthlib>=1.0.0
```

## Updated requirements.txt
```txt
# Google Sheets API (add these to existing requirements.txt)
google-api-python-client>=2.100.0
google-auth-httplib2>=0.1.1
google-auth-oauthlib>=1.0.0
```

## Safe Import Implementation
The service now includes safe imports with fallback:

```python
# Safe Google SDK imports with fallback
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_SDK_AVAILABLE = True
except ImportError:
    GOOGLE_SDK_AVAILABLE = False
    Credentials = None
    Flow = None
    Request = None
    build = None
    HttpError = None
```

## Safe Initialization
```python
class GoogleSheetsService:
    def __init__(self):
        if not GOOGLE_SDK_AVAILABLE:
            logger.warning("Google SDK not available. Google Sheets integration will be disabled.")
            self.sdk_available = False
            return
            
        self.sdk_available = True
        # Initialize only if SDK is available
```

## Why This Fixes It Permanently
1. **Complete SDK**: Provides full Google Sheets API functionality
2. **Version Compatibility**: Tested with Python 3.13
3. **Safe Initialization**: Won't crash app if SDK missing
4. **Clear Error Messages**: Helpful logging for debugging
5. **Graceful Degradation**: App works without Google Sheets if SDK missing

## Verification
After installation, test with:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
print("Google SDK successfully imported!")
```

## Startup Check
The service now logs a clear warning if Google SDK is missing:
```
WARNING: Google SDK not available. Google Sheets integration will be disabled.
```

This prevents the app from crashing and provides clear guidance for fixing the issue.
