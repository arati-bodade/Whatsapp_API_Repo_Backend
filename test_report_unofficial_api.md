# Unofficial Public API Test Report

| Endpoint | Method | Status Code | Time (ms) | Result | Response (Short) | Probable Cause |
|----------|--------|-------------|-----------|--------|------------------|----------------|
| /send-message | POST | 500 | 26.71 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-file | POST | 500 | 31.25 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-file-text | POST | 500 | 14.29 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-base64-file | POST | 500 | 16.29 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-file | GET | 500 | 15.53 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-file-text | GET | 500 | 15.73 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-file-caption | GET | 500 | 15.38 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-message-query | GET | 500 | 15.23 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-file-query | GET | 500 | 15.04 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /send-message-file-query | GET | 500 | 15.37 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /delivery-report | GET | 500 | 14.79 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
| /status-check | GET | 500 | 15.33 | FAIL | `{"detail": "WhatsAppEngineService.__init...` | Internal logic/engine error |
