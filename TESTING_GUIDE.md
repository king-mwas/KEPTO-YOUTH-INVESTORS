# Testing Guide - STK Push & Notifications

This guide walks you through testing the M-Pesa STK Push integration and notification system.

## Server Status

Development server is running at: **http://localhost:8000**

## Test Credentials

| Component | Value |
|-----------|-------|
| Admin User | `admin` / `admin123` |
| Test User | `testuser` / `test123` |
| Member ID | `12345678` |
| Phone Number | `0712345678` |
| M-Pesa Mode | Sandbox |

## Testing Steps

### 1. Access Django Admin

1. Go to **http://localhost:8000/admin/**
2. Login with: `admin` / `admin123`
3. Verify you can see:
   - M-Pesa > M-Pesa Credentials
   - M-Pesa > STK Push Requests
   - M-Pesa > Transactions
   - Notifications > Notifications
   - Notifications > Notification Templates

### 2. Verify M-Pesa Configuration

In Django Admin:

1. Go to **M-Pesa > M-Pesa Credentials**
2. Click on the credential entry
3. Verify:
   ```
   ✓ Consumer Key: test_consumer_key_123456
   ✓ Consumer Secret: test_consumer_secret_123456
   ✓ Business Shortcode: 123456
   ✓ Pass Key: test_passkey_123456
   ✓ Callback URL: http://localhost:8000/api/mpesa/callback/
   ✓ Is Sandbox: ✓ (checked)
   ✓ Is Active: ✓ (checked)
   ```

### 3. Test STK Push API (Authentication Flow)

**Step 1: Login**
```bash
curl -X POST http://localhost:8000/accounts/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=test123" \
  -c /tmp/cookies.txt
```

**Step 2: Initiate Payment**
```bash
curl -X POST http://localhost:8000/api/mpesa/initiate-payment/ \
  -H "Content-Type: application/json" \
  -b /tmp/cookies.txt \
  -d '{"amount": 100.00}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "STK Push initiated. Please enter your M-Pesa PIN.",
  "request_id": "uuid-here",
  "checkout_request_id": "checkout-id-here"
}
```

### 4. Test with Python/JavaScript

**Python Example:**
```python
import requests

# Start session
session = requests.Session()

# Login
session.post('http://localhost:8000/accounts/login/', data={
    'username': 'testuser',
    'password': 'test123'
})

# Initiate payment
response = session.post('http://localhost:8000/api/mpesa/initiate-payment/', json={
    'amount': 100.00
})

print(response.json())
```

**JavaScript Example:**
```javascript
// Login
await fetch('http://localhost:8000/accounts/login/', {
  method: 'POST',
  body: new URLSearchParams({
    username: 'testuser',
    password: 'test123'
  }),
  credentials: 'include'
});

// Initiate payment
const response = await fetch('http://localhost:8000/api/mpesa/initiate-payment/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ amount: 100.00 }),
  credentials: 'include'
});

console.log(await response.json());
```

### 5. Test Notification Creation

When you create a STK Push request, a notification should be automatically created.

**Check in Django Admin:**
1. Go to **Notifications > Notifications**
2. Look for notifications with:
   - Member: `12345678`
   - Title: Related to deposit

Or via Django Shell:
```python
python manage.py shell
>>> from notifications.models import Notification
>>> from accounts.models import Member
>>> member = Member.objects.get(member_id='12345678')
>>> member.notifications.all()
<QuerySet [<Notification: 12345678 - Deposit Initiated>]>
>>> notification = member.notifications.first()
>>> notification.title
'Deposit Initiated'
>>> notification.status
'pending'
```

### 6. Test M-Pesa Callback (Manual)

Simulate a successful M-Pesa callback:

```bash
# Get a checkout_request_id from the admin panel first
CHECKOUT_ID="checkout_id_from_admin"

curl -X POST http://localhost:8000/api/mpesa/callback/ \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "MerchantRequestID": "16813-1590513-1",
        "CheckoutRequestID": "'$CHECKOUT_ID'",
        "ResultCode": 0,
        "ResultDesc": "The service request has been processed successfully.",
        "CallbackMetadata": {
          "Item": [
            {
              "Name": "Amount",
              "Value": 100.0
            },
            {
              "Name": "MpesaReceiptNumber",
              "Value": "LHG31H500G12"
            },
            {
              "Name": "TransactionDate",
              "Value": 20260820061521
            },
            {
              "Name": "PhoneNumber",
              "Value": 712345678
            }
          ]
        }
      }
    }
  }'
```

### 7. Verify Transaction Processing

After callback is received:

**In Django Admin:**
1. Go to **M-Pesa > Transactions**
2. Verify transaction record exists
3. Go to **Notifications > Notifications**
4. Verify success notification was created

**Via Shell:**
```python
python manage.py shell
>>> from mpesa.models import MpesaTransaction
>>> MpesaTransaction.objects.all()
<QuerySet [<MpesaTransaction: ...>]>
>>> t = MpesaTransaction.objects.first()
>>> t.status
'success'
>>> t.mpesa_receipt_number
'LHG31H500G12'
```

### 8. Test User Preferences

**Check Current Preferences:**
```python
python manage.py shell
>>> from accounts.models import Member
>>> member = Member.objects.get(member_id='12345678')
>>> prefs = member.notification_preferences
>>> prefs.receive_sms
True
>>> prefs.notify_on_deposit
True
```

**Update Preferences:**
```python
>>> prefs.receive_sms = False
>>> prefs.notify_on_deposit = False
>>> prefs.save()
```

**Verify Notification Blocking:**
```python
from notifications.utils import NotificationService
# Should return None because preferences block SMS
notification = NotificationService.send_notification(
    member=member,
    event_type='deposit_initiated',
    title='Test',
    message='Test',
    channel_name='sms'
)
print(notification)  # None
```

## Testing Scenarios

### Scenario 1: Complete Payment Flow
```
1. User initiates payment (100 KES)
2. STK Push request created ✓
3. Deposit status: pending ✓
4. Notification sent to user ✓
5. M-Pesa callback received (success)
6. Transaction recorded ✓
7. Deposit status: approved ✓
8. Success notification sent ✓
```

### Scenario 2: Failed Payment
```
1. User initiates payment (100 KES)
2. STK Push request created ✓
3. M-Pesa callback received (failure)
4. Transaction status: failed ✓
5. Failure notification sent ✓
```

### Scenario 3: Notification Preferences
```
1. User disables SMS notifications
2. STK Push initiated
3. SMS notification should NOT be sent ✓
4. In-App notification should be sent ✓
```

## Debugging

### Check Server Logs
```bash
tail -f /tmp/django.log
```

### View Database State
```bash
python manage.py dbshell
sqlite> SELECT * FROM mpesa_stk_push_request;
sqlite> SELECT * FROM mpesa_transaction;
sqlite> SELECT * FROM notifications_notification;
```

### Clear Test Data
```bash
python manage.py shell
>>> from mpesa.models import StkPushRequest, MpesaTransaction
>>> from notifications.models import Notification
>>> StkPushRequest.objects.all().delete()
>>> MpesaTransaction.objects.all().delete()
>>> Notification.objects.all().delete()
```

## Common Issues

### Issue: "No active M-Pesa credentials found"
**Solution**: Check Django admin that credentials are created and `is_active` is checked

### Issue: Callback 404 error
**Solution**: Ensure you're posting to correct URL: `/api/mpesa/callback/`

### Issue: "Request not found" on callback
**Solution**: The checkout_request_id in callback must match one created in the database

### Issue: Notification not created
**Solution**: Check user preferences, notification channels, and Django logs

## Next Steps for Production

1. **Real M-Pesa Credentials**: Get production keys from Safaricom
2. **HTTPS Callback**: Use ngrok or public domain with SSL
3. **SMS Gateway**: Integrate Twilio or Africa's Talking
4. **Email Service**: Configure AWS SES or SendGrid
5. **Monitoring**: Set up Sentry or similar for error tracking
6. **Logging**: Configure structured logging to ELK stack
7. **Testing**: Write unit and integration tests
8. **Load Testing**: Test with actual transaction volume

## Support Resources

- Django Shell: `python manage.py shell`
- Database Inspection: `python manage.py dbshell`
- Clear Cache: `python manage.py shell` then `from django.core.cache import cache; cache.clear()`
- View Logs: `tail -f /tmp/django.log`

---

Happy Testing! 🚀
