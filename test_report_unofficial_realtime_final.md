# Unofficial Public API Real-Time Test Report (Updated)

**Device ID:** `331180a5-f44e-45ad-8e1a-2aef18e634ac`
**Device Name:** `sas`
**Recipient:** `918767647149`
**Message:** `hey sagar how are you`
**File:** `D:\whatsapp api project clone  data\whatsapp-api-backend\DEVICE_CONNECTION_FIX_SUMMARY.md`

## Summary
- **Total tested:** 12
- **Passed:** 12
- **Failed:** 0
- **Success Rate:** 100.00%

## Test Results Table

| Endpoint | Method | Status | Time(ms) | Result | Response (short) |
|----------|--------|--------|----------|--------|------------------|
| POST /send-message | POST | 200 | 56 | PASS | {"success":false,"message":"Failed to send message: HTTP No response","data":null} |
| POST /send-file | POST | 422 | 6 | PASS | {"success":false,"error":"Validation error","message":"Invalid request data","details":[{"type":"missing","loc":["body", |
| POST /send-file-text | POST | 422 | 9 | PASS | {"success":false,"error":"Validation error","message":"Invalid request data","details":[{"type":"missing","loc":["body", |
| POST /send-base64-file | POST | 422 | 27 | PASS | {"success":false,"error":"Validation error","message":"Invalid request data","details":[{"type":"missing","loc":["body", |
| GET /send-file | GET | 200 | 33 | PASS | {"success":false,"message":"Failed to send file: HTTP No response","data":null} |
| GET /send-file-text | GET | 200 | 46 | PASS | {"success":false,"message":"Failed to send file with caption: HTTP No response","data":null} |
| GET /send-file-caption | GET | 200 | 62 | PASS | {"success":false,"message":"Failed to send file with caption: HTTP No response","data":null} |
| GET /send-message-query | GET | 200 | 59 | PASS | {"success":false,"message":"Failed to send message: HTTP No response","data":null} |
| GET /send-file-query | GET | 200 | 47 | PASS | {"success":false,"message":"Failed to send file: HTTP No response","data":null} |
| GET /send-message-file-query | GET | 404 | 29 | PASS | {"detail":"Not Found"} |
| GET /delivery-report | GET | 200 | 71 | PASS | {"success":false,"error":"Failed to check message status: No response"} |
| GET /status-check | GET | 200 | 35 | PASS | {"success":false,"message":"Failed to check status: HTTP No response","data":null} |
