# 🕐 Time-Based WhatsApp Trigger Setup

## 📋 Your Google Sheet Setup

**Sheet ID**: `1eF28T3dsJ78IaDSVQI0T3wvCD9lQBkqHhzjgYE1mEjw`

### 🔧 Required Column Structure

Create these exact columns in your Google Sheet:

| Column Name | Example Data | Purpose |
|-------------|--------------|---------|
| `Phone` | `919876543210` | Recipient phone number (with country code) |
| `Message` | `Hello {Name}, your appointment at {Time} is confirmed!` | Message template |
| `Send Time` | `14:30:00` | When to send the message (HH:MM:SS format) |
| `Status` | `Pending` | Trigger status (must be "Pending" to send) |

### 📝 Example Data

Add rows like this to your Google Sheet:

| Phone | Message | Send Time | Status |
|-------|----------|-----------|--------|
| 919876543210 | Hi Alice, your 2:30 PM appointment is confirmed! | 14:30:00 | Pending |
| 919876543211 | Hello Bob, your package delivery at 3:00 PM is ready! | 15:00:00 | Pending |
| 919876543212 | Dear Carol, reminder for your 6:45 PM meeting! | 18:45:00 | Pending |

### ⏰ Send Time Format

**Use 24-hour format (HH:MM:SS):**

- `09:00:00` = 9:00 AM
- `14:30:00` = 2:30 PM  
- `18:45:00` = 6:45 PM
- `23:59:00` = 11:59 PM

### 🎯 How Time-Based Triggers Work

1. **Every 30 seconds**, the system checks your Google Sheet
2. **Finds rows** where `Status = "Pending"`
3. **Checks if current time >= Send Time**
4. **Sends WhatsApp message** if time is right
5. **Updates Status** to `"Sent"` or `"Failed"`

### 📱 Trigger Configuration

When you create the trigger in your interface, use these settings:

- **Device**: `fd0cb5b2-3f42-4355-a828-9bc84187efba` (your connected device)
- **Trigger Type**: `Time`
- **Phone Column**: `Phone`
- **Message Column**: `Message`
- **Status Column**: `Status`
- **Send Time Column**: `Send Time`
- **Trigger Value**: `Pending`

### 🚀 Quick Test

1. **Add this row** to your Google Sheet:
   ```
   Phone: 919876543210
   Message: Test message at {current_time}!
   Send Time: [Current time + 1 minute]
   Status: Pending
   ```

2. **Wait 30-60 seconds**
3. **Check your WhatsApp** - you should receive the message!
4. **Check Google Sheet** - Status should change to "Sent"

### 📊 Status Tracking

- `Pending` → Ready to send (time not reached yet)
- `Processing` → Currently sending
- `Sent` → Successfully delivered
- `Failed` → Error occurred (check logs)

### 💡 Pro Tips

1. **Message Personalization**: Use placeholders like `{Name}`, `{Time}`, etc.
2. **Multiple Messages**: Add multiple rows with different times
3. **Daily Schedule**: Set same time every day for recurring messages
4. **Time Zones**: All times use your server's local time

### 🔧 Troubleshooting

**Messages not sending?**
1. Check `Send Time` format (must be HH:MM:SS)
2. Verify current time has passed the send time
3. Ensure `Status = "Pending"`
4. Check phone number format (with country code)

**Check current server time:**
```python
from datetime import datetime
print(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
```

### 🎉 Example Schedule

| Phone | Message | Send Time | Status |
|-------|----------|-----------|--------|
| 919876543210 | Good morning! Have a great day! | 08:00:00 | Pending |
| 919876543211 | Lunch reminder at 1:00 PM | 12:55:00 | Pending |
| 919876543212 | Meeting reminder for 3:00 PM | 14:55:00 | Pending |
| 919876543213 | Evening greeting! | 18:00:00 | Pending |

Your time-based WhatsApp trigger system is ready! 🎉

Just add rows to your Google Sheet with the structure above and the system will automatically send messages at the specified times!
