from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from savings.models import Deposit
from announcements.models import Announcement
from .utils import NotificationService
from accounts.models import Member
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Deposit)
def notify_deposit_status_change(sender, instance, created, **kwargs):
    try:
        if created:
            NotificationService.send_deposit_notification(
                member=instance.member,
                deposit=instance,
                status='pending',
            )
            logger.info(f"Deposit initiated notification sent for {instance.member.member_id}")
        else:
            NotificationService.send_deposit_notification(
                member=instance.member,
                deposit=instance,
                status=instance.status,
            )
            logger.info(f"Deposit {instance.status} notification sent for {instance.member.member_id}")

    except Exception as e:
        logger.error(f"Error sending deposit notification: {str(e)}")


@receiver(post_save, sender=Member)
def create_user_notification_preferences(sender, instance, created, **kwargs):
    if created:
        try:
            from .models import UserNotificationPreference
            UserNotificationPreference.objects.get_or_create(member=instance)
            logger.info(f"Notification preferences created for {instance.member_id}")
        except Exception as e:
            logger.error(f"Error creating notification preferences: {str(e)}")
