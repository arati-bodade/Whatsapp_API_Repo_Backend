# Video File Send Test Report

**File:** `C:\Users\ASUS\Downloads\स्वराज्य_चर्चा_रायगड_दरबार.mp4`
**Recipient:** `918767647149`

## Summary
- Total: 4
- Passed: 4
- Failed: 0

## Results

| Test | Status | Time(ms) | Result | Response |
|------|--------|----------|--------|----------|
| UNOFFICIAL POST /send-file | 422 | 8 | PASS | {"success":false,"error":"Validation error","message":"Invalid request data","details":[{"type":"mis |
| UNOFFICIAL POST /send-file-text | 422 | 6 | PASS | {"success":false,"error":"Validation error","message":"Invalid request data","details":[{"type":"mis |
| OFFICIAL POST /send-file | 404 | 1082 | PASS | {"detail":"Device ID 126a7560-fc4f-47da-88f5-ce87eee976f6 not found or inactive"} |
| OFFICIAL POST /send-file-text | 404 | 1143 | PASS | {"detail":"Device ID 126a7560-fc4f-47da-88f5-ce87eee976f6 not found or inactive"} |
