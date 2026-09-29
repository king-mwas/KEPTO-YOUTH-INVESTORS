from django.db import models
from django.contrib.auth.models import User
from accounts.models import Member


class NotificationChannel(models.Model):
    CHANNELS = [
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
        ('email', 'Email'),
    ]

    name = models.CharField(max_length=20, choices=CHANNELS, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_name_display()


class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    message = models.TextField(help_text="Use {variable} for placeholders")
    channels = models.ManyToManyField(NotificationChannel)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EventType(models.Model):
    DEPOSIT_INITIATED = 'deposit_initiated'
    DEPOSIT_COMPLETED = 'deposit_completed'
    DEPOSIT_APPROVED = 'deposit_approved'
    DEPOSIT_REJECTED = 'deposit_rejected'
    LESSON_AVAILABLE = 'lesson_available'
    LESSON_COMPLETED = 'lesson_completed'
    SAVINGS_GOAL_REACHED = 'savings_goal_reached'
    PROFILE_UPDATED = 'profile_updated'
    ANNOUNCEMENT = 'announcement'
    WITHDRAWAL_INITIATED = 'withdrawal_initiated'
    WITHDRAWAL_COMPLETED = 'withdrawal_completed'

    EVENT_TYPES = [
        (DEPOSIT_INITIATED, 'Deposit Initiated'),
        (DEPOSIT_COMPLETED, 'Deposit Completed'),
        (DEPOSIT_APPROVED, 'Deposit Approved'),
        (DEPOSIT_REJECTED, 'Deposit Rejected'),
        (LESSON_AVAILABLE, 'Lesson Available'),
        (LESSON_COMPLETED, 'Lesson Completed'),
        (SAVINGS_GOAL_REACHED, 'Savings Goal Reached'),
        (PROFILE_UPDATED, 'Profile Updated'),
        (ANNOUNCEMENT, 'Announcement'),
        (WITHDRAWAL_INITIATED, 'Withdrawal Initiated'),
        (WITHDRAWAL_COMPLETED, 'Withdrawal Completed'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, unique=True)
    notification_template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.get_event_type_display()


class Notification(models.Model):
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    FAILED = 'failed'
    READ = 'read'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SENT, 'Sent'),
        (DELIVERED, 'Delivered'),
        (FAILED, 'Failed'),
        (READ, 'Read'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notifications')
    event_type = models.ForeignKey(EventType, on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.ForeignKey(NotificationChannel, on_delete=models.SET_NULL, null=True, blank=True)

    title = models.CharField(max_length=200)
    message = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.member_id} - {self.title}"


class UserNotificationPreference(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='notification_preferences')

    receive_sms = models.BooleanField(default=True)
    receive_push = models.BooleanField(default=True)
    receive_in_app = models.BooleanField(default=True)
    receive_email = models.BooleanField(default=False)

    notify_on_deposit = models.BooleanField(default=True)
    notify_on_lessons = models.BooleanField(default=True)
    notify_on_announcements = models.BooleanField(default=True)
    notify_on_milestones = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.member.member_id}"
