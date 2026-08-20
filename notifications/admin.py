from django.contrib import admin
from .models import (NotificationChannel, NotificationTemplate, EventType,
                     Notification, UserNotificationPreference)


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('get_name_display', 'is_active')
    list_filter = ('is_active',)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'title')
    filter_horizontal = ('channels',)


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('get_event_type_display', 'notification_template')
    search_fields = ('event_type',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('member', 'title', 'status', 'created_at')
    list_filter = ('status', 'channel', 'created_at')
    search_fields = ('member__member_id', 'title', 'message')
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'delivered_at', 'read_at')
    fieldsets = (
        ('Notification Info', {
            'fields': ('member', 'event_type', 'channel', 'title', 'message')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'delivered_at', 'read_at')
        }),
    )


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('member', 'receive_sms', 'receive_push', 'receive_in_app', 'receive_email')
    list_filter = ('receive_sms', 'receive_push', 'receive_in_app', 'receive_email')
    search_fields = ('member__member_id',)
    fieldsets = (
        ('Notification Channels', {
            'fields': ('receive_sms', 'receive_push', 'receive_in_app', 'receive_email')
        }),
        ('Event Preferences', {
            'fields': ('notify_on_deposit', 'notify_on_lessons', 'notify_on_announcements', 'notify_on_milestones')
        }),
    )
