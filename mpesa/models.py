from django.db import models
from accounts.models import Member
from savings.models import Deposit
import uuid


class MpesaCredentials(models.Model):
    consumer_key = models.CharField(max_length=500)
    consumer_secret = models.CharField(max_length=500)
    business_shortcode = models.CharField(max_length=20)
    pass_key = models.CharField(max_length=500)
    access_token_url = models.URLField(default='https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials')
    api_url = models.URLField(default='https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest')
    callback_url = models.URLField(help_text="URL where M-Pesa will send transaction callbacks")
    is_active = models.BooleanField(default=True)
    is_sandbox = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "M-Pesa Credentials"

    def __str__(self):
        return f"M-Pesa Config (Sandbox: {self.is_sandbox})"


class StkPushRequest(models.Model):
    PENDING = 'pending'
    SENT = 'sent'
    EXPIRED = 'expired'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SENT, 'Sent'),
        (EXPIRED, 'Expired'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='stk_push_requests')
    deposit = models.OneToOneField(Deposit, on_delete=models.CASCADE, null=True, blank=True, related_name='stk_push_request')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=20)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    checkout_request_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    response_code = models.CharField(max_length=10, blank=True)
    response_description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"STK Push {self.request_id} - {self.member.member_id}"


class MpesaTransaction(models.Model):
    SUCCESS = 'success'
    FAILED = 'failed'
    PENDING = 'pending'

    STATUS_CHOICES = [
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
        (PENDING, 'Pending'),
    ]

    transaction_id = models.CharField(max_length=100, unique=True)
    stk_push_request = models.OneToOneField(StkPushRequest, on_delete=models.CASCADE, related_name='mpesa_transaction', null=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='mpesa_transactions')

    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    result_code = models.CharField(max_length=10)
    result_description = models.TextField()

    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True)

    receipt_number = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.member.member_id}"


class MpesaCallback(models.Model):
    callback_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction = models.ForeignKey(MpesaTransaction, on_delete=models.CASCADE, related_name='callbacks', null=True, blank=True)

    callback_type = models.CharField(max_length=50)
    raw_body = models.JSONField()

    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Callback {self.callback_id} - {self.callback_type}"


class MpesaQueryStatus(models.Model):
    INITIATED = 'initiated'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = [
        (INITIATED, 'Initiated'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    query_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    stk_push_request = models.ForeignKey(StkPushRequest, on_delete=models.CASCADE, related_name='status_queries')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=INITIATED)
    response_code = models.CharField(max_length=10, blank=True)
    response_description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    queried_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Query {self.query_id} - {self.stk_push_request.member.member_id}"
