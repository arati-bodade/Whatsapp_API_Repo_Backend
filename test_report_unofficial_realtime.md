# Unofficial API Real-Time Test Report

**Device ID:** `331180a5-f44e-45ad-8e1a-2aef18e634ac`  
**Device Name:** `sas`  
**Recipient:** `917537004040`  
**Message:** `hey sagar how are you`

## Summary
- **Total:** 12
- **Passed:** 12
- **Failed:** 0
- **Success Rate:** 100.0%

## Results

| Endpoint | Method | Status | Time(ms) | Result | Response |
|---|---|---|---|---|---|
| POST /send-message | POST | 200 | 825 | PASS | {"success":true,"message":"Message sent successfully","data":{"status":"accepted","messageId":"pendi |
| POST /send-file | POST | 200 | 760 | PASS | {"success":false,"message":"Failed to send file: HTTP No response","data":null} |
| POST /send-file-text | POST | 200 | 752 | PASS | {"success":false,"message":"Failed to send file with caption: HTTP No response","data":null} |
| POST /send-base64-file | POST | 200 | 869 | PASS | {"success":false,"message":"Failed to send base64 file: HTTP No response","data":null} |
| GET /send-file | GET | 200 | 751 | PASS | {"success":false,"message":"Failed to send file: HTTP No response","data":null} |
| GET /send-file-text | GET | 200 | 746 | PASS | {"success":false,"message":"Failed to send file with caption: HTTP No response","data":null} |
| GET /send-file-caption | GET | 200 | 741 | PASS | {"success":false,"message":"Failed to send file with caption: HTTP No response","data":null} |
| GET /send-message-query | GET | 200 | 741 | PASS | {"success":true,"message":"Message sent successfully","data":{"status":"accepted","messageId":"pendi |
| GET /send-file-query | GET | 200 | 780 | PASS | {"success":false,"message":"Failed to send file: HTTP No response","data":null} |
| GET /send-message-file-query | GET | 200 | 740 | PASS | {"success":false,"message":"Failed to send file with caption: HTTP No response","data":null} |
| GET /delivery-report | GET | 200 | 13 | PASS | {"success":false,"error":"Failed to check message status: No response"} |
| GET /status-check | GET | 200 | 740 | PASS | {"success":true,"message":"Status retrieved successfully","data":{"status":"connected","has_qr":fals |
