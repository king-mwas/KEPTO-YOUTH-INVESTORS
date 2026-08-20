from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

from accounts.models import Member


class DepositApprovalRequest(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='approval_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    message = models.TextField(help_text="Proof of payment or transaction details")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    admin_note = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_approval_requests',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.member_id} - KES {self.amount} (Request)"


class Deposit(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    transaction_code = models.CharField(max_length=50, blank=True)
    proof = models.FileField(upload_to='deposit_proofs/', blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    admin_note = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_deposits',
    )

    class Meta:
        ordering = ['-created_at']

    @property
    def is_confirmed(self):
        return bool(self.transaction_code or self.proof)

    def __str__(self):
        return f"{self.member.member_id} - KES {self.amount} ({self.status})"
