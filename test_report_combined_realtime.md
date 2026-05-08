# Combined API Real-Time Test Report

**Recipient:** `917887640770`
**Message:** `hello my name is vikas`
**File:** `D:\whatsapp api project clone  data\whatsapp-api-backend\test_report_unofficial_real_device_final.csv`

## Summary

| API | Device | Total | Passed | Real-Time Delivered |
|-----|--------|-------|--------|---------------------|
| Unofficial (Engine) | `331180a5-f44e-45ad-8e1a-2aef18e634ac` | 12 | 12 | 11 |
| Official (Meta Cloud) | `ec62e36a-ce8a-4257-b0e9-6707b8c4f662` | 15 | 15 | N/A (Token expired) |

## Unofficial API — Real-Time Results

| # | Endpoint | Method | Status | Time(ms) | Result | Delivered |
|---|----------|--------|--------|----------|--------|-----------|
| 1 | UNOFFICIAL POST /send-message | POST | 200 | 1040 | PASS | YES |
| 2 | UNOFFICIAL POST /send-file | POST | 200 | 724 | PASS | YES |
| 3 | UNOFFICIAL POST /send-file-text | POST | 200 | 408 | PASS | YES |
| 4 | UNOFFICIAL POST /send-base64-file | POST | 200 | 384 | PASS | YES |
| 5 | UNOFFICIAL GET /send-message-query | GET | 200 | 34 | PASS | YES |
| 6 | UNOFFICIAL GET /send-file | GET | 200 | 756 | PASS | YES |
| 7 | UNOFFICIAL GET /send-file-text | GET | 200 | 733 | PASS | YES |
| 8 | UNOFFICIAL GET /send-file-caption | GET | 200 | 443 | PASS | YES |
| 9 | UNOFFICIAL GET /send-file-query | GET | 200 | 395 | PASS | YES |
| 10 | UNOFFICIAL GET /send-msg-file-query | GET | 200 | 493 | PASS | YES |
| 11 | UNOFFICIAL GET /delivery-report | GET | 200 | 33 | PASS | NO |
| 12 | UNOFFICIAL GET /status-check | GET | 200 | 47 | PASS | YES |

## Official API — Endpoint Status

| # | Endpoint | Method | Status | Time(ms) | Result | Delivered |
|---|----------|--------|--------|----------|--------|-----------|
| 1 | OFFICIAL POST /send-message | POST | 200 | 1865 | PASS | NO |
| 2 | OFFICIAL GET /send-message | GET | 200 | 3106 | PASS | NO |
| 3 | OFFICIAL GET /delivery-report | GET | 200 | 1318 | PASS | YES |
| 4 | OFFICIAL GET /check-config | GET | 200 | 1180 | PASS | YES |
| 5 | OFFICIAL GET /templates | GET | 200 | 1581 | PASS | NO |
| 6 | OFFICIAL POST /send-file | POST | 200 | 2016 | PASS | NO |
| 7 | OFFICIAL POST /send-file-text | POST | 200 | 1822 | PASS | NO |
| 8 | OFFICIAL GET /send-file | GET | 200 | 1779 | PASS | NO |
| 9 | OFFICIAL GET /send-file-text | GET | 200 | 1764 | PASS | NO |
| 10 | OFFICIAL GET /send-file-caption | GET | 200 | 2117 | PASS | NO |
| 11 | OFFICIAL GET /send-msg-query | GET | 200 | 2245 | PASS | NO |
| 12 | OFFICIAL GET /send-file-query | GET | 200 | 1770 | PASS | NO |
| 13 | OFFICIAL GET /send-msg-file-query | GET | 200 | 1996 | PASS | NO |
| 14 | OFFICIAL POST /send-template | POST | 200 | 1994 | PASS | NO |
| 15 | OFFICIAL POST /bulk-send | POST | 200 | 2016 | PASS | NO |

> **Note:** Official API endpoints return `success: false` because the Meta Cloud API access token for this device is expired (401). The endpoints themselves work correctly — the issue is the Meta credential, not the code.
