from django.contrib import admin
from django.db.models import Q
from django.utils import timezone

from .models import Deposit


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'status', 'transaction_code', 'created_at', 'reviewed_by']
    list_filter = ['status']
    search_fields = ['member__member_id', 'member__user__username', 'transaction_code']
    readonly_fields = ['created_at', 'reviewed_at', 'reviewed_by']
    actions = ['approve_deposits', 'reject_deposits']

    @admin.action(description='Approve selected deposits')
    def approve_deposits(self, request, queryset):
        unconfirmed = Q(transaction_code='') & (Q(proof='') | Q(proof__isnull=True))
        confirmed = queryset.filter(status=Deposit.PENDING).exclude(unconfirmed)
        count = confirmed.update(status=Deposit.APPROVED, reviewed_by=request.user, reviewed_at=timezone.now())
        skipped = queryset.filter(status=Deposit.PENDING).count() - count
        self.message_user(request, f"Approved {count} deposit(s).")
        if skipped:
            self.message_user(request, f"Skipped {skipped} deposit(s) with no transaction code or proof yet.")

    @admin.action(description='Reject selected deposits')
    def reject_deposits(self, request, queryset):
        count = queryset.filter(status=Deposit.PENDING).update(
            status=Deposit.REJECTED, reviewed_by=request.user, reviewed_at=timezone.now(),
        )
        self.message_user(request, f"Rejected {count} deposit(s).")
