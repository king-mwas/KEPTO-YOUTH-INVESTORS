from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MpesaTransaction
from notifications.utils import NotificationService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MpesaTransaction)
def notify_transaction_completion(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        member = instance.member

        if instance.status == MpesaTransaction.SUCCESS:
            NotificationService.send_notification(
                member=member,
                event_type='deposit_completed',
                title='Payment Successful ✓',
                message=f'Your payment of KES {instance.amount} has been received. Your deposit will be reviewed shortly.',
                channel_name='in_app',
            )
            logger.info(f"Success notification sent for transaction {instance.transaction_id}")

        elif instance.status == MpesaTransaction.FAILED:
            NotificationService.send_notification(
                member=member,
                event_type='deposit_rejected',
                title='Payment Failed',
                message=f'Your payment of KES {instance.amount} could not be processed. Please try again.',
                channel_name='in_app',
            )
            logger.info(f"Failure notification sent for transaction {instance.transaction_id}")

    except Exception as e:
        logger.error(f"Error sending transaction notification: {str(e)}")
