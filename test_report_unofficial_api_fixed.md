# Unofficial Public API Test Report

| Endpoint | Method | Status Code | Time (ms) | Result | Response (Short) | Probable Cause |
|----------|--------|-------------|-----------|--------|------------------|----------------|
| /send-message | POST | 422 | 28.43 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-file | POST | 422 | 29.94 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-file-text | POST | 422 | 30.06 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-base64-file | POST | 422 | 31.12 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-file | GET | 422 | 30.11 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-file-text | GET | 422 | 31.88 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-file-caption | GET | 422 | 31.41 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-message-query | GET | 422 | 30.73 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-file-query | GET | 422 | 30.24 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /send-message-file-query | GET | 422 | 6.82 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
| /delivery-report | GET | 200 | 56.48 | PASS | `{"success": false, "error": "Failed to c...` |  |
| /status-check | GET | 422 | 29.07 | FAIL | `{"detail": "Invalid payload"}` | Validation error (check payload structure) |
