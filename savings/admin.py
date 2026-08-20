from django.contrib import admin
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Deposit, DepositApprovalRequest


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


@admin.register(DepositApprovalRequest)
class DepositApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status', 'created_at']
    search_fields = ['member__member_id', 'member__user__username', 'message']
    readonly_fields = ['created_at', 'reviewed_at', 'reviewed_by', 'message']
    actions = ['approve_requests', 'reject_requests']

    fieldsets = (
        ('Request Info', {
            'fields': ('member', 'amount', 'message')
        }),
        ('Review', {
            'fields': ('status', 'admin_note')
        }),
        ('Metadata', {
            'fields': ('created_at', 'reviewed_at', 'reviewed_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.action(description='Approve selected requests & create deposits')
    def approve_requests(self, request, queryset):
        from notifications.utils import NotificationService

        count = 0
        for req in queryset.filter(status=DepositApprovalRequest.PENDING):
            # Create deposit
            deposit = Deposit.objects.create(
                member=req.member,
                amount=req.amount,
                status=Deposit.APPROVED,
                transaction_code=f"MANUAL-{req.id}",
                admin_note=f"Approved from manual request #{req.id}",
                reviewed_by=request.user,
                reviewed_at=timezone.now(),
            )

            # Mark request as approved
            req.status = DepositApprovalRequest.APPROVED
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()

            # Notify member
            NotificationService.send_notification(
                member=req.member,
                event_type='deposit_approved',
                title='Deposit Approved ✓',
                message=f'Your deposit of KES {req.amount} has been approved and added to your account.',
                channel_name='in_app',
            )

            # Send email notification
            try:
                send_mail(
                    subject='Deposit Approved - KEPTO',
                    message=f'Your deposit of KES {req.amount} has been approved and added to your savings account.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[req.member.user.email] if req.member.user.email else [],
                    fail_silently=True,
                )
            except:
                pass

            count += 1

        self.message_user(request, f"Approved {count} deposit request(s) and created deposits.")

    @admin.action(description='Reject selected requests')
    def reject_requests(self, request, queryset):
        from notifications.utils import NotificationService

        count = 0
        for req in queryset.filter(status=DepositApprovalRequest.PENDING):
            req.status = DepositApprovalRequest.REJECTED
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()

            # Notify member
            NotificationService.send_notification(
                member=req.member,
                event_type='deposit_rejected',
                title='Deposit Request Rejected',
                message=f'Your deposit request of KES {req.amount} could not be verified. Please contact support.',
                channel_name='in_app',
            )

            count += 1

        self.message_user(request, f"Rejected {count} deposit request(s).")
