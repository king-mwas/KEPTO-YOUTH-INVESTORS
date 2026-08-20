# M-Pesa STK Push Integration Guide

This document provides comprehensive instructions for setting up and using the M-Pesa Daraja API integration for STK Push payments and the notification system in KEPTO Youth Investors.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup Instructions](#setup-instructions)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [API Endpoints](#api-endpoints)
6. [Notification System](#notification-system)
7. [Database Models](#database-models)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before implementing STK Push integration, ensure you have:

1. **Safaricom Developer Account**: Register at [Safaricom Daraja](https://developer.safaricom.co.ke/)
2. **M-Pesa API Credentials**:
   - Consumer Key
   - Consumer Secret
   - Business Shortcode (Paybill/Till Number)
   - Pass Key (for STK Push)
3. **Public Callback URL**: Your application must be accessible via HTTPS with a public domain
4. **Python 3.11+** and Django 5.1+

---

## Setup Instructions

### 1. Install Dependencies

All required packages are already in `requirements.txt`. Install them:

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root based on `.env.example`:

```bash
cp .env.example .env
```

Update the `.env` file with your M-Pesa credentials:

```
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_BUSINESS_SHORTCODE=123456
MPESA_PASSKEY=your_passkey
MPESA_SANDBOX=True  # Set to False for production
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback/
```

### 3. Database Migration

Run migrations to create the necessary database tables:

```bash
python manage.py migrate
```

This will create tables for:
- M-Pesa credentials
- STK Push requests
- M-Pesa transactions
- Notification channels and templates
- Notifications and user preferences

### 4. Configure M-Pesa Credentials via Admin Panel

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Go to `http://localhost:8000/admin/`

3. Navigate to **M-Pesa > M-Pesa Credentials**

4. Create a new credential entry with:
   - Consumer Key: Your API consumer key
   - Consumer Secret: Your API consumer secret
   - Business Shortcode: Your M-Pesa business shortcode
   - Pass Key: Your M-Pesa pass key
   - Callback URL: Your public HTTPS callback URL
   - Is Sandbox: Check if using sandbox (development)
   - Is Active: Check to enable

### 5. Initialize Notification Templates (Optional)

Go to **Notifications** in the admin panel to set up:
- Notification Channels (SMS, Push, In-App, Email)
- Notification Templates with message content
- Event Types mapping to templates

---

## Configuration

### M-Pesa API Endpoints

The system uses the following Daraja API endpoints:

- **Token Endpoint** (Sandbox): `https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials`
- **STK Push** (Sandbox): `https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest`
- **Query Status** (Sandbox): `https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query`

For production, replace `sandbox.safaricom.co.ke` with `api.safaricom.co.ke`.

### CORS Configuration

If your frontend is on a different domain, update `CORS_ALLOWED_ORIGINS` in `.env`:

```
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

## Usage

### Initiating an STK Push Payment

**Endpoint**: `POST /api/mpesa/initiate-payment/`

**Requirements**: User must be logged in

**Request Body**:
```json
{
  "amount": 100.00
}
```

**Response**:
```json
{
  "success": true,
  "message": "STK Push initiated. Please enter your M-Pesa PIN.",
  "request_id": "uuid-here",
  "checkout_request_id": "checkout-id-here"
}
```

**Example (JavaScript/Fetch)**:
```javascript
const response = await fetch('/api/mpesa/initiate-payment/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    amount: 100.00
  })
});

const data = await response.json();
if (data.success) {
  console.log('STK Push sent to your phone');
  // Optionally poll for status
}
```

### Querying Transaction Status

**Endpoint**: `GET /api/mpesa/query-status/<request_id>/`

**Requirements**: User must be logged in and the request must belong to them

**Response**:
```json
{
  "success": true,
  "status": {
    "ResponseCode": "0",
    "ResponseDescription": "The service request has been accepted successfully"
  }
}
```

### M-Pesa Callback Processing

**Endpoint**: `POST /api/mpesa/callback/` (Configured in M-Pesa Dashboard)

This endpoint:
1. Receives transaction callbacks from M-Pesa
2. Validates the callback
3. Updates transaction status
4. Triggers notifications
5. Updates deposit status if applicable

**Callback Handling**:
- Processes payment confirmations
- Updates transaction records
- Sends notifications to users
- Automatically approves deposits (if transaction successful)

---

## API Endpoints

### M-Pesa Integration Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---|
| POST | `/api/mpesa/initiate-payment/` | Initiate STK Push | Yes |
| POST | `/api/mpesa/callback/` | Receive M-Pesa callbacks | No* |
| GET | `/api/mpesa/query-status/<id>/` | Query payment status | Yes |

*Callback endpoint is open but validates requests internally

### Notification Endpoints (Future)

These endpoints will be added for frontend notification management:
- `GET /api/notifications/` - List user notifications
- `PATCH /api/notifications/<id>/read/` - Mark as read
- `GET /api/notifications/preferences/` - Get user preferences
- `PATCH /api/notifications/preferences/` - Update preferences

---

## Notification System

### Architecture

The notification system consists of:

1. **Notification Channels**: SMS, Push, In-App, Email
2. **Event Types**: Deposit, Lesson, Milestone, Announcement events
3. **Templates**: Reusable message templates with placeholders
4. **User Preferences**: Per-user notification settings

### Supported Events

- `deposit_initiated` - Deposit payment initiated
- `deposit_completed` - Payment received successfully
- `deposit_approved` - Deposit approved by admin
- `deposit_rejected` - Deposit rejected
- `lesson_available` - New lesson published
- `lesson_completed` - User completed a lesson
- `savings_goal_reached` - Milestone achievement
- `announcement` - System announcement
- `withdrawal_initiated` - Withdrawal requested
- `withdrawal_completed` - Withdrawal processed

### Sending Notifications Programmatically

```python
from notifications.utils import NotificationService
from accounts.models import Member

member = Member.objects.get(member_id='12345678')

# Send deposit notification
NotificationService.send_deposit_notification(
    member=member,
    deposit=deposit_object,
    status='approved'
)

# Send milestone notification
NotificationService.send_milestone_notification(
    member=member,
    message='You have reached KES 5,000 in savings!'
)

# Send announcement
NotificationService.send_announcement_notification(
    member=member,
    announcement_title='New Course Available',
    announcement_content='Check out our new personal finance course'
)

# Mark as read
from notifications.models import Notification
notification = Notification.objects.get(id=1)
NotificationService.mark_as_read(notification)
```

### User Preferences

Users can manage their notification preferences in the admin panel or via API. Preferences include:

- **Channel Preferences**: Enable/disable SMS, Push, In-App, Email
- **Event Preferences**: Enable/disable notifications for deposits, lessons, announcements, milestones

---

## Database Models

### MpesaCredentials
Stores M-Pesa API credentials (one per environment)

Fields:
- `consumer_key` - API consumer key
- `consumer_secret` - API consumer secret
- `business_shortcode` - M-Pesa business shortcode
- `pass_key` - STK Push pass key
- `access_token_url` - OAuth token endpoint
- `api_url` - STK Push endpoint
- `callback_url` - Callback URL
- `is_active` - Active status
- `is_sandbox` - Sandbox/Production flag

### StkPushRequest
Tracks STK Push requests

Fields:
- `request_id` - Unique UUID
- `member` - FK to Member
- `deposit` - FK to Deposit (optional)
- `amount` - Transaction amount
- `phone_number` - M-Pesa phone number
- `status` - pending, sent, expired, completed, cancelled
- `checkout_request_id` - M-Pesa checkout ID
- `response_code` - API response code
- `expires_at` - Request expiration time

### MpesaTransaction
Records completed transactions

Fields:
- `transaction_id` - Unique transaction ID
- `stk_push_request` - FK to StkPushRequest
- `member` - FK to Member
- `amount` - Transaction amount
- `status` - success, failed, pending
- `result_code` - M-Pesa result code
- `mpesa_receipt_number` - M-Pesa receipt
- `completed_at` - Completion timestamp

### MpesaCallback
Logs all M-Pesa callbacks

Fields:
- `callback_id` - Unique UUID
- `transaction` - FK to MpesaTransaction
- `callback_type` - Type of callback
- `raw_body` - Raw JSON response
- `processed` - Processing status

### Notification Models
- `NotificationChannel` - SMS, Push, In-App, Email
- `NotificationTemplate` - Message templates
- `EventType` - Event categorization
- `Notification` - Individual notifications
- `UserNotificationPreference` - User settings

---

## Troubleshooting

### Common Issues

#### 1. "No active M-Pesa credentials found"
**Solution**: Ensure M-Pesa credentials are created in admin panel and `is_active` is checked.

#### 2. "Access token request failed"
**Solution**: Verify credentials are correct. Test in Daraja portal first.

#### 3. Callback not received
**Solution**:
- Ensure callback URL is HTTPS and publicly accessible
- Verify firewall allows M-Pesa IP ranges
- Check Django logs for errors
- Confirm callback URL in admin panel matches what's registered in Daraja

#### 4. "Checkout request ID not found"
**Solution**: This usually indicates a callback from a stale STK request. Ensure requests don't expire.

#### 5. Notifications not sending
**Solution**:
- Check user notification preferences
- Verify notification templates are active
- Check Django logs for signal errors
- Ensure `notifications` app is in `INSTALLED_APPS`

### Debugging

Enable detailed logging by updating settings:

```python
LOGGING = {
    'loggers': {
        'mpesa': {'level': 'DEBUG'},
        'notifications': {'level': 'DEBUG'},
    }
}
```

View logs:
```bash
python manage.py runserver 2>&1 | grep -E "mpesa|notifications"
```

---

## Production Deployment

### Pre-Production Checklist

- [ ] Switch `MPESA_SANDBOX=False` in production environment
- [ ] Update M-Pesa credentials to production keys
- [ ] Ensure callback URL uses production domain (HTTPS)
- [ ] Test end-to-end with real transactions on staging
- [ ] Set up database backups
- [ ] Configure error monitoring (Sentry, etc.)
- [ ] Set up logging and alerts
- [ ] Review security settings in Django admin

### Environment Variables

For production, set these securely (not in `.env`):
- `MPESA_CONSUMER_KEY`
- `MPESA_CONSUMER_SECRET`
- `MPESA_PASSKEY`
- `SECRET_KEY`

### SSL/TLS

- Ensure your domain has a valid SSL certificate
- M-Pesa callbacks require HTTPS
- Use security middleware in production

---

## Resources

- [Safaricom Daraja API Documentation](https://developer.safaricom.co.ke/apis)
- [M-Pesa STK Push Guide](https://developer.safaricom.co.ke/docs)
- [Django Signals Documentation](https://docs.djangoproject.com/en/5.1/topics/signals/)

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django logs
3. Verify M-Pesa credentials in Daraja portal
4. Test callback URL accessibility
5. Contact Safaricom Daraja support
