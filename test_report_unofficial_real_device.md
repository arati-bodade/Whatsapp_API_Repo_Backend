# Unofficial API Real Device Test Report

## Summary
- **Total tested:** 12
- **Passed:** 0
- **Failed:** 12
- **Success Rate:** 0.00%

## Test Results Table

| Endpoint | Method | Status | Time(ms) | Result | Response (short) |
|----------|--------|--------|----------|--------|------------------|
| /send-message | POST | 500 | 30 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-file | POST | 500 | 31 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-file-text | POST | 500 | 31 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-base64-file | POST | 500 | 31 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-file | GET | 500 | 15 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-file-text | GET | 500 | 31 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-file-caption | GET | 500 | 30 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-message-query | GET | 500 | 30 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-file-query | GET | 500 | 30 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /send-message-file-query | GET | 500 | 15 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /delivery-report | GET | 500 | 15 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |
| /status-check | GET | 500 | 16 | FAIL | {"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"} |

## Errors and Probable Causes

### POST /send-message
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### POST /send-file
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### POST /send-file-text
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### POST /send-base64-file
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### GET /send-file
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### GET /send-file-text
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### GET /send-file-caption
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### GET /send-message-query
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### GET /send-file-query
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### GET /send-message-file-query
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### GET /delivery-report
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### GET /status-check
- **Status Code:** 500
- **Error Response:** `{"detail":"WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'"}`

### Probable Causes Section
- **500 Internal Server Error:** All endpoints are failing with `WhatsAppEngineService.__init__() missing 1 required positional argument: 'db'`. This means the API route handlers are instantiating `WhatsAppEngineService()` without providing the required `db` argument.
