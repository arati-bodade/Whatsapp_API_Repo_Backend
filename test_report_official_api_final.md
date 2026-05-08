# Official Public API Test Report

**Device ID:** `126a7560-fc4f-47da-88f5-ce87eee976f6`
**Recipient:** `917887640770`
**Message:** `hello my name is vikas`

## Summary
- **Total tested:** 16
- **Passed:** 16
- **Failed:** 0
- **Success Rate:** 100.00%

## Test Results Table

| Endpoint | Method | Status | Time(ms) | Result | Response (short) |
|----------|--------|--------|----------|--------|------------------|
| POST /send-message | POST | 200 | 5693 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| POST /send-file | POST | 200 | 4089 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","file_path":"https://www.w3.org/WAI/ER/tests/xhtml/te |
| POST /send-file-text | POST | 200 | 2470 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| POST /send-base64-file | POST | 200 | 2931 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","filename":"test_official.txt","file_url":"http://127 |
| POST /send-template | POST | 200 | 2428 | PASS | {"success":true,"message_id":"wamid.HBgMOTE3ODg3NjQwNzcwFQIAERgSMzFDMTNBMTIyRjMzRDQxNzNEAA==","device_id":"126a7560-fc4f |
| POST /bulk-send | POST | 200 | 2826 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","total_recipients":1,"successful_sends":1,"failed_sen |
| GET /send-message | GET | 200 | 2852 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| GET /send-file | GET | 200 | 2584 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| GET /send-file-text | GET | 200 | 2638 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| GET /send-file-caption | GET | 200 | 3526 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| GET /send-message-query | GET | 200 | 4010 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| GET /send-file-query | GET | 200 | 2568 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| GET /send-message-file-query | GET | 200 | 2627 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"wamid.HBgMOTE3 |
| GET /delivery-report | GET | 200 | 1331 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","result":{"success":true,"message_id":"test-message-i |
| GET /public/check-config | GET | 200 | 1028 | PASS | {"success":true,"active":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","device_status":"connected","created_at |
| GET /templates | GET | 200 | 2640 | PASS | {"success":true,"device_id":"126a7560-fc4f-47da-88f5-ce87eee976f6","templates":[{"name":"address_update_rsl","status":"A |
