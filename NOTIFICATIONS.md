# Notification System Documentation

This guide describes the comprehensive notification system built into KEPTO Youth Investors for managing user notifications across multiple channels and event types.

## Overview

The notification system provides:

- **Multiple Channels**: SMS, Push notifications, In-App, Email
- **Event-Driven**: Automatic notifications triggered by system events
- **User Preferences**: Granular control over notification settings
- **Tracking**: Full history of notifications sent and delivery status
- **Templates**: Reusable message templates with variable substitution

## Architecture

### Components

1. **Notification Channels** - Delivery methods (SMS, Push, In-App, Email)
2. **Event Types** - Categorized events that trigger notifications
3. **Templates** - Message content with placeholders
4. **Notifications** - Individual notification records
5. **User Preferences** - Per-user notification settings

### Data Flow

```
Event Occurs → Signal Triggered → Notification Service →
Check User Preferences → Send Notification → Track Delivery
```

## Database Models

### NotificationChannel
Defines available notification channels

```python
NotificationChannel.objects.all()
# Returns: SMS, Push Notification, In-App, Email
```

### NotificationTemplate
Reusable message templates

```python
template = NotificationTemplate.objects.create(
    name='deposit_approved',
    title='Deposit Approved',
    message='Your deposit of {amount} KES has been approved!',
    channels=[sms_channel, in_app_channel],
    is_active=True
)
```

### EventType
Categorizes events that trigger notifications

```python
EventType.objects.create(
    event_type='deposit_approved',
    notification_template=template
)
```

### Notification
Individual notification records

```python
notification = Notification.objects.create(
    member=member,
    event_type=event_type,
    channel=channel,
    title='Deposit Approved',
    message='Your deposit has been approved!',
    status='pending'
)
```

### UserNotificationPreference
User-specific notification settings

```python
prefs = UserNotificationPreference.objects.get(member=member)
print(prefs.receive_sms)  # True/False
print(prefs.notify_on_deposit)  # True/False
```

## Event Types

The system supports the following event types:

| Event Type | Description | Triggers | Default Channel |
|------------|-------------|----------|-----------------|
| `deposit_initiated` | Deposit payment started | Deposit created | In-App |
| `deposit_completed` | Payment received | M-Pesa callback | In-App |
| `deposit_approved` | Admin approved deposit | Deposit status changed | In-App |
| `deposit_rejected` | Admin rejected deposit | Deposit status changed | In-App |
| `lesson_available` | New lesson published | Lesson created | In-App |
| `lesson_completed` | User completed lesson | Progress saved | In-App |
| `savings_goal_reached` | Milestone achieved | Amount threshold reached | In-App |
| `announcement` | System announcement | Announcement published | In-App |
| `withdrawal_initiated` | Withdrawal requested | Withdrawal created | In-App |
| `withdrawal_completed` | Withdrawal processed | Withdrawal completed | In-App |

## Usage

### Sending Notifications Programmatically

#### Basic Notification

```python
from notifications.utils import NotificationService
from accounts.models import Member

member = Member.objects.get(member_id='12345678')

NotificationService.send_notification(
    member=member,
    event_type='announcement',
    title='New Opportunity',
    message='A new investment opportunity is available',
    channel_name='in_app'
)
```

#### Deposit Notification

```python
from notifications.utils import NotificationService
from savings.models import Deposit

deposit = Deposit.objects.get(id=1)

NotificationService.send_deposit_notification(
    member=deposit.member,
    deposit=deposit,
    status='approved'  # pending, approved, rejected
)
```

#### Lesson Notification

```python
NotificationService.send_lesson_notification(
    member=member,
    lesson_title='Personal Finance 101'
)
```

#### Milestone Notification

```python
NotificationService.send_milestone_notification(
    member=member,
    message='Congratulations! You have saved KES 10,000'
)
```

#### Announcement

```python
NotificationService.send_announcement_notification(
    member=member,
    announcement_title='Platform Maintenance',
    announcement_content='We will be down for maintenance on Saturday...'
)
```

### Tracking Notifications

#### Mark as Sent
```python
NotificationService.mark_as_sent(notification)
```

#### Mark as Delivered
```python
NotificationService.mark_as_delivered(notification)
```

#### Mark as Read
```python
NotificationService.mark_as_read(notification)
```

#### Get Unread Count
```python
count = NotificationService.get_unread_count(member)
```

#### Get Recent Notifications
```python
notifications = NotificationService.get_recent_notifications(member, limit=10)
```

## Signals and Auto-Triggers

### Deposit Signals

When a `Deposit` is created or updated, the system automatically:
1. Creates a notification record
2. Sends notification via configured channels
3. Updates notification status based on delivery

```python
# Automatically triggered when:
deposit = Deposit.objects.create(
    member=member,
    amount=500.00
)
# Sends: "Deposit Initiated" notification
```

### Member Signals

When a new `Member` is created:
1. Creates default `UserNotificationPreference`
2. Enables all notification channels by default
3. Enables notifications for all event types

## User Preferences API

### Get User Preferences

```python
prefs = member.notification_preferences

# Check channel preferences
prefs.receive_sms  # bool
prefs.receive_push  # bool
prefs.receive_in_app  # bool
prefs.receive_email  # bool

# Check event preferences
prefs.notify_on_deposit  # bool
prefs.notify_on_lessons  # bool
prefs.notify_on_announcements  # bool
prefs.notify_on_milestones  # bool
```

### Update User Preferences

```python
prefs = member.notification_preferences
prefs.receive_sms = False
prefs.notify_on_lessons = True
prefs.save()
```

## Admin Interface

### Managing Notifications

Go to **Django Admin** → **Notifications** to:

1. **View Notifications**
   - Filter by member, status, channel
   - See notification history
   - Track delivery status

2. **Configure Channels**
   - Enable/disable notification channels
   - Manage channel settings

3. **Create Templates**
   - Create reusable message templates
   - Add variable placeholders
   - Assign to channels
   - Activate/deactivate templates

4. **Event Configuration**
   - Map events to templates
   - Add new event types
   - Update notification behavior

5. **User Preferences**
   - Review per-user settings
   - Bulk update preferences
   - Reset to defaults

## Notification Status Flow

```
PENDING → SENT → DELIVERED → READ
              └→ FAILED
```

**Status Meanings**:
- **PENDING**: Created but not sent yet
- **SENT**: Sent to notification service
- **DELIVERED**: Successfully delivered to user
- **READ**: User has read the notification
- **FAILED**: Failed to send

## Best Practices

### 1. Use Meaningful Titles
```python
# Good
title = "Deposit Approved ✓"

# Avoid
title = "notification"
```

### 2. Keep Messages Concise
```python
# Good
message = "Your deposit of KES 500 has been approved!"

# Avoid
message = "We are writing to inform you that your deposit..."
```

### 3. Respect User Preferences
The notification service automatically checks preferences before sending. Always use `NotificationService` instead of creating notifications manually.

```python
# Good - respects preferences
NotificationService.send_notification(...)

# Avoid - bypasses preferences
Notification.objects.create(...)
```

### 4. Use Templates for Consistency
```python
# Create template once
template = NotificationTemplate.objects.create(
    name='deposit_approved',
    title='Deposit Approved',
    message='Your deposit of {amount} KES has been approved!',
)

# Reuse in code
```

### 5. Handle Errors Gracefully
```python
try:
    NotificationService.send_notification(...)
except Exception as e:
    logger.error(f"Failed to send notification: {e}")
    # Don't break the main process
```

## Frontend Integration

### Fetch Notifications (Future API)

```javascript
// Get user's notifications
const response = await fetch('/api/notifications/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const notifications = await response.json();
```

### Mark as Read

```javascript
await fetch(`/api/notifications/${id}/read/`, {
  method: 'PATCH',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### Update Preferences

```javascript
await fetch('/api/notifications/preferences/', {
  method: 'PATCH',
  body: JSON.stringify({
    receive_sms: false,
    notify_on_deposit: true
  })
});
```

## Monitoring and Debugging

### View Notification Logs

```bash
python manage.py tail --logname notifications
```

### Database Queries

```python
# All notifications for a member
member.notifications.all()

# Unread notifications
member.notifications.filter(status__in=['pending', 'sent', 'delivered'])

# By event type
member.notifications.filter(event_type__event_type='deposit_approved')

# By channel
member.notifications.filter(channel__name='in_app')

# Failed notifications
member.notifications.filter(status='failed')
```

### Check Delivery Status

```python
notification = Notification.objects.get(id=1)
print(f"Status: {notification.status}")
print(f"Sent at: {notification.sent_at}")
print(f"Delivered at: {notification.delivered_at}")
print(f"Read at: {notification.read_at}")
if notification.status == 'failed':
    print(f"Error: {notification.error_message}")
```

## Testing

### Create Test Notification

```python
from django.test import TestCase
from notifications.utils import NotificationService
from accounts.models import Member

class NotificationTest(TestCase):
    def test_deposit_notification(self):
        member = Member.objects.create(...)
        
        notification = NotificationService.send_notification(
            member=member,
            event_type='deposit_initiated',
            title='Test Deposit',
            message='Testing notification system',
            channel_name='in_app'
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.status, 'pending')
```

### Test Preferences

```python
def test_notification_preferences(self):
    member = Member.objects.create(...)
    prefs = member.notification_preferences
    
    # Update preferences
    prefs.receive_sms = False
    prefs.notify_on_deposit = False
    prefs.save()
    
    # Verify SMS notifications are blocked
    notification = NotificationService.send_notification(
        member=member,
        event_type='deposit_initiated',
        title='Test',
        message='Test',
        channel_name='sms'
    )
    
    # Should be None if preferences block it
    self.assertIsNone(notification)
```

## Future Enhancements

- [ ] SMS delivery via Africa's Talking or Twilio
- [ ] Email notifications via Celery tasks
- [ ] Push notifications via Firebase Cloud Messaging
- [ ] Notification digest emails (daily/weekly)
- [ ] Notification delivery retry mechanism
- [ ] Rich HTML email templates
- [ ] Notification webhooks for external integrations

## Support

For issues:
1. Check notification logs
2. Verify user preferences
3. Ensure templates are active
4. Review signal handlers
5. Test with admin interface

---

**Last Updated**: 2026-08-20
