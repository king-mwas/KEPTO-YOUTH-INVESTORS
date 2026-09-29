import logging
from datetime import datetime
from django.utils import timezone
from .models import Notification, NotificationChannel, EventType, UserNotificationPreference

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def send_notification(member, event_type, title, message, channel_name='in_app', context=None):
        try:
            user_prefs = UserNotificationPreference.objects.get(member=member)
        except UserNotificationPreference.DoesNotExist:
            user_prefs = UserNotificationPreference.objects.create(member=member)

        if not NotificationService._should_send(user_prefs, event_type, channel_name):
            logger.info(f"Notification skipped for {member.member_id}: preferences disabled")
            return None

        try:
            channel = NotificationChannel.objects.get(name=channel_name, is_active=True)
        except NotificationChannel.DoesNotExist:
            logger.warning(f"Channel {channel_name} not found or inactive")
            return None

        try:
            event = EventType.objects.get(event_type=event_type)
        except EventType.DoesNotExist:
            event = None

        notification = Notification.objects.create(
            member=member,
            event_type=event,
            channel=channel,
            title=title,
            message=message,
            status=Notification.PENDING,
        )

        logger.info(f"Notification created: {notification.id} for {member.member_id}")
        return notification

    @staticmethod
    def send_deposit_notification(member, deposit, status):
        event_type_map = {
            'pending': EventType.DEPOSIT_INITIATED,
            'approved': EventType.DEPOSIT_APPROVED,
            'rejected': EventType.DEPOSIT_REJECTED,
        }

        event_type = event_type_map.get(status, EventType.DEPOSIT_INITIATED)

        title_map = {
            'pending': 'Deposit Initiated',
            'approved': 'Deposit Approved ✓',
            'rejected': 'Deposit Rejected',
        }

        message_map = {
            'pending': f'Your deposit of KES {deposit.amount} has been initiated. Please complete the M-Pesa payment to confirm.',
            'approved': f'Your deposit of KES {deposit.amount} has been approved! The funds are now in your savings account.',
            'rejected': f'Your deposit of KES {deposit.amount} could not be processed. Please try again.',
        }

        title = title_map.get(status, 'Deposit Update')
        message = message_map.get(status, 'Your deposit status has been updated.')

        return NotificationService.send_notification(
            member=member,
            event_type=event_type,
            title=title,
            message=message,
            channel_name='in_app',
        )

    @staticmethod
    def send_lesson_notification(member, lesson_title):
        return NotificationService.send_notification(
            member=member,
            event_type=EventType.LESSON_AVAILABLE,
            title='New Lesson Available',
            message=f'A new lesson "{lesson_title}" is now available. Start learning today!',
            channel_name='in_app',
        )

    @staticmethod
    def send_milestone_notification(member, message):
        return NotificationService.send_notification(
            member=member,
            event_type=EventType.SAVINGS_GOAL_REACHED,
            title='🎉 Milestone Reached!',
            message=message,
            channel_name='in_app',
        )

    @staticmethod
    def send_announcement_notification(member, announcement_title, announcement_content):
        return NotificationService.send_notification(
            member=member,
            event_type=EventType.ANNOUNCEMENT,
            title=f'Announcement: {announcement_title}',
            message=announcement_content[:200],
            channel_name='in_app',
        )

    @staticmethod
    def _should_send(user_prefs, event_type, channel_name):
        if channel_name == 'sms' and not user_prefs.receive_sms:
            return False
        elif channel_name == 'push' and not user_prefs.receive_push:
            return False
        elif channel_name == 'in_app' and not user_prefs.receive_in_app:
            return False
        elif channel_name == 'email' and not user_prefs.receive_email:
            return False

        if 'deposit' in event_type and not user_prefs.notify_on_deposit:
            return False
        elif 'lesson' in event_type and not user_prefs.notify_on_lessons:
            return False
        elif event_type == EventType.ANNOUNCEMENT and not user_prefs.notify_on_announcements:
            return False
        elif 'savings_goal' in event_type and not user_prefs.notify_on_milestones:
            return False

        return True

    @staticmethod
    def mark_as_sent(notification):
        notification.status = Notification.SENT
        notification.sent_at = timezone.now()
        notification.save()
        logger.info(f"Notification marked as sent: {notification.id}")

    @staticmethod
    def mark_as_delivered(notification):
        notification.status = Notification.DELIVERED
        notification.delivered_at = timezone.now()
        notification.save()
        logger.info(f"Notification marked as delivered: {notification.id}")

    @staticmethod
    def mark_as_read(notification):
        notification.status = Notification.READ
        notification.read_at = timezone.now()
        notification.save()
        logger.info(f"Notification marked as read: {notification.id}")

    @staticmethod
    def get_unread_count(member):
        return Notification.objects.filter(
            member=member,
            status__in=[Notification.PENDING, Notification.SENT, Notification.DELIVERED]
        ).count()

    @staticmethod
    def get_recent_notifications(member, limit=10):
        return Notification.objects.filter(
            member=member
        ).order_by('-created_at')[:limit]
