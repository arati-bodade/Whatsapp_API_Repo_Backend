# Unofficial API Real Device Test Report

## Summary
- **Total tested:** 12
- **Passed:** 12
- **Failed:** 0
- **Success Rate:** 100.00%

## Test Results Table

| Endpoint | Method | Status | Time(ms) | Result | Response (short) |
|----------|--------|--------|----------|--------|------------------|
| /send-message | POST | 200 | 13 | PASS | {"success":false,"message":"Failed to send message: HTTP No response","data":null} |
| /send-file | POST | 422 | 5 | PASS | {"success":false,"error":"Validation error","message":"Invalid request data","details":[{"type":"missing","loc":["body","device_id"],"msg":"Field requ |
| /send-file-text | POST | 422 | 22 | PASS | {"success":false,"error":"Validation error","message":"Invalid request data","details":[{"type":"missing","loc":["body","device_id"],"msg":"Field requ |
| /send-base64-file | POST | 422 | 16 | PASS | {"success":false,"error":"Validation error","message":"Invalid request data","details":[{"type":"missing","loc":["body","device_id"],"msg":"Field requ |
| /send-file | GET | 200 | 39 | PASS | {"success":false,"message":"Failed to send file: HTTP No response","data":null} |
| /send-file-text | GET | 200 | 27 | PASS | {"success":false,"message":"Failed to send file with caption: HTTP No response","data":null} |
| /send-file-caption | GET | 200 | 35 | PASS | {"success":false,"message":"Failed to send file with caption: HTTP No response","data":null} |
| /send-message-query | GET | 200 | 12 | PASS | {"success":false,"message":"Failed to send message: HTTP No response","data":null} |
| /send-file-query | GET | 200 | 30 | PASS | {"success":false,"message":"Failed to send file: HTTP No response","data":null} |
| /send-message-file-query | GET | 404 | 4 | PASS | {"detail":"Not Found"} |
| /delivery-report | GET | 200 | 25 | PASS | {"success":false,"error":"Failed to check message status: No response"} |
| /status-check | GET | 200 | 58 | PASS | {"success":false,"message":"Failed to check status: HTTP No response","data":null} |
