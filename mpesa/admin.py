from django.contrib import admin
from .models import MpesaCredentials, StkPushRequest, MpesaTransaction, MpesaCallback, MpesaQueryStatus


@admin.register(MpesaCredentials)
class MpesaCredentialsAdmin(admin.ModelAdmin):
    list_display = ('business_shortcode', 'is_sandbox', 'is_active')
    fields = ('consumer_key', 'consumer_secret', 'business_shortcode', 'pass_key',
              'access_token_url', 'api_url', 'callback_url', 'is_active', 'is_sandbox')
    readonly_fields = ('access_token_url', 'api_url')


@admin.register(StkPushRequest)
class StkPushRequestAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('member__member_id', 'phone_number')
    readonly_fields = ('request_id', 'checkout_request_id', 'response_code', 'response_description', 'created_at')
    fieldsets = (
        ('Request Info', {
            'fields': ('request_id', 'member', 'deposit', 'amount', 'phone_number')
        }),
        ('Status', {
            'fields': ('status', 'checkout_request_id', 'response_code', 'response_description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'updated_at')
        }),
    )


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'member', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('transaction_id', 'member__member_id', 'phone_number')
    readonly_fields = ('transaction_id', 'mpesa_receipt_number', 'created_at')
    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction_id', 'member', 'phone_number', 'amount')
        }),
        ('M-Pesa Details', {
            'fields': ('merchant_request_id', 'checkout_request_id', 'mpesa_receipt_number')
        }),
        ('Status', {
            'fields': ('status', 'result_code', 'result_description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )


@admin.register(MpesaCallback)
class MpesaCallbackAdmin(admin.ModelAdmin):
    list_display = ('callback_id', 'callback_type', 'processed', 'created_at')
    list_filter = ('processed', 'callback_type', 'created_at')
    readonly_fields = ('callback_id', 'created_at', 'raw_body')


@admin.register(MpesaQueryStatus)
class MpesaQueryStatusAdmin(admin.ModelAdmin):
    list_display = ('query_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('query_id', 'created_at', 'queried_at')
