# Complete Deployment Guide - KEPTO STK Push

This guide covers the complete deployment of KEPTO with STK Push, notifications, and the new deposit UI.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Email Service Setup](#email-service-setup)
4. [SMS Service Setup](#sms-service-setup)
5. [Render Deployment](#render-deployment)
6. [Post-Deployment Setup](#post-deployment-setup)
7. [Testing](#testing)

---

## Prerequisites

- PostgreSQL 12+ (for production)
- Python 3.11+
- Git and GitHub account
- Safaricom Daraja API credentials
- Gmail account (for email notifications)
- Twilio account (for SMS notifications) - Optional
- Render account (for deployment)

---

## Local Development Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Update `.env` with your local configuration:
```
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST_PASSWORD=your_gmail_app_password
MPESA_SANDBOX=True
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Access at: `http://localhost:8000`

---

## Email Service Setup

### Gmail Configuration

**Get Gmail App Password:**

1. Enable 2-Factor Authentication on your Google account
2. Go to: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer"
4. Copy the 16-character password

**Update `.env`:**

```
EMAIL_HOST_USER=keptoinvestor@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
ADMIN_EMAIL=keptoinvestor@gmail.com
```

**Test Email:**

```python
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail(
...     'Test Email',
...     'This is a test email from KEPTO',
...     'keptoinvestor@gmail.com',
...     ['keptoinvestor@gmail.com'],
... )
```

### Alternative: SendGrid

1. Sign up at https://sendgrid.com
2. Create an API key
3. Install: `pip install sendgrid==6.10.0`
4. Update settings:
```python
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
```

---

## SMS Service Setup

### Twilio Configuration

**Get Twilio Credentials:**

1. Sign up at https://www.twilio.com
2. Get your Account SID and Auth Token
3. Provision a phone number
4. Get a Twilio phone number (e.g., +1234567890)

**Update `.env`:**

```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

**Test SMS:**

```python
python manage.py shell
>>> from twilio.rest import Client
>>> from django.conf import settings
>>> client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
>>> message = client.messages.create(
...     body='Hello from KEPTO!',
...     from_=settings.TWILIO_PHONE_NUMBER,
...     to='+254712345678'  # Test phone number
... )
>>> print(message.sid)
```

### Africa's Talking (Kenyan Alternative)

1. Sign up at https://africastalking.com
2. Get API Key
3. Install: `pip install africastalking`
4. Configure in settings

---

## Render Deployment

### Step 1: Prepare Repository

```bash
# Commit all changes
git add -A
git commit -m "feat: Complete deposit UI and deployment setup"
git push origin main
```

### Step 2: Create Render Service

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select `king-mwas/KEPTO-YOUTH-INVESTORS`

### Step 3: Configure Render

**Name**: `kepto-backend`

**Environment**: `Python 3.11`

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start Command:**
```bash
gunicorn core.wsgi:application
```

### Step 4: Add Environment Variables

In Render dashboard, add these environment variables:

```
DEBUG=False
ALLOWED_HOSTS=kepto-backend.onrender.com
SECRET_KEY=[generate a new one]
DATABASE_URL=postgresql://...  # Auto-filled by Render
MPESA_SANDBOX=True  # or False for production
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_BUSINESS_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://kepto-backend.onrender.com/api/mpesa/callback/
EMAIL_HOST_USER=keptoinvestor@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
ADMIN_EMAIL=keptoinvestor@gmail.com
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
CORS_ALLOWED_ORIGINS=https://kepto-backend.onrender.com
```

### Step 5: Deploy

1. Click "Deploy"
2. Wait for build to complete (5-10 minutes)
3. Access at: `https://kepto-backend.onrender.com`

### Step 6: Configure Database

Render automatically creates PostgreSQL. View connection string in:
- Dashboard → Database → Info

---

## Post-Deployment Setup

### 1. Create Admin User

```bash
# Connect to Render console
python manage.py createsuperuser
```

### 2. Configure M-Pesa Credentials

1. Visit: `https://your-domain.com/admin/mpesa/mpesacredentials/`
2. Add M-Pesa credentials
3. Update callback URL in Safaricom Daraja dashboard

### 4. Test Payment Flow

1. Create test account in admin
2. Navigate to: `/dashboard/deposit-page/`
3. Try STK Push (sandbox mode)
4. Try manual approval (paste message)

### 5. Monitor Logs

```bash
# View Render logs
# In Render dashboard: Logs tab
```

---

## Testing

### Test STK Push (Sandbox)

```bash
curl -X POST https://your-domain.com/api/mpesa/initiate-payment/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your_session" \
  -d '{"amount": 100.00}'
```

### Test Manual Approval

Use the Deposit Page UI:
1. Navigate to `/dashboard/deposit-page/`
2. Enter amount
3. Click "Manual Deposit (Admin Review)"
4. Paste payment details
5. Admin reviews in `/admin/savings/depositapprovalrequest/`

### Test Email Notifications

```python
python manage.py shell
>>> from savings.models import DepositApprovalRequest
>>> from accounts.models import Member
>>> member = Member.objects.first()
>>> req = DepositApprovalRequest.objects.create(
...     member=member,
...     amount=500,
...     message='Test payment details'
... )
# Email should be sent automatically
```

### Test Notifications

```python
>>> from notifications.utils import NotificationService
>>> NotificationService.send_notification(
...     member=member,
...     event_type='deposit_initiated',
...     title='Test Notification',
...     message='This is a test',
...     channel_name='in_app'
... )
```

---

## Troubleshooting

### 1. Database Connection Error

**Solution**: Verify DATABASE_URL in Render environment variables

### 2. Email Not Sending

**Solution**:
- Check Gmail App Password is correct
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Check Admin Email in settings
- Test with: `python manage.py shell` → test code above

### 3. STK Push Timeout

**Solution**:
- Verify M-Pesa credentials are correct
- Check callback URL is HTTPS
- Ensure Safaricom has callback URL registered

### 4. CORS Errors

**Solution**: Update CORS_ALLOWED_ORIGINS in environment variables

### 5. Build Fails

**Solution**:
- Check requirements.txt syntax
- Verify all dependencies are compatible
- View build logs in Render dashboard

---

## Production Checklist

- [ ] Switch MPESA_SANDBOX to False
- [ ] Update M-Pesa credentials to production keys
- [ ] Configure custom domain (DNS settings)
- [ ] Enable SSL/TLS certificate
- [ ] Set up database backups
- [ ] Configure error monitoring (Sentry)
- [ ] Set up log aggregation
- [ ] Test email/SMS delivery
- [ ] Load test with production traffic
- [ ] Create admin backup account
- [ ] Document admin procedures
- [ ] Set up 24/7 support
- [ ] Monitor transaction volumes

---

## Support

For issues during deployment:
1. Check Render logs: Dashboard → Logs
2. Verify environment variables
3. Test locally first: `python manage.py runserver`
4. Review error messages in admin panel
5. Contact support with error logs

---

**Last Updated**: August 20, 2026
