import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings

from announcements.models import Announcement
from accounts.models import Member
from notifications.utils import NotificationService

from .forms import DepositAmountForm, DepositConfirmForm
from .models import Deposit, DepositApprovalRequest


@login_required
def dashboard(request):
    member = request.user.member
    balance = member.deposits.filter(status=Deposit.APPROVED).aggregate(total=Sum('amount'))['total'] or 0
    deposits = member.deposits.all()
    announcements = Announcement.objects.filter(is_active=True)[:5]
    return render(request, 'savings/dashboard.html', {
        'balance': balance,
        'deposits': deposits,
        'announcements': announcements,
        'member': member,
    })


@login_required
def deposit_new(request):
    member = request.user.member
    if member.status != Member.APPROVED:
        messages.warning(request, "Your membership is still pending admin approval — you'll be able to deposit once it's approved.")
        return redirect('savings:dashboard')

    if request.method == 'POST':
        form = DepositAmountForm(request.POST)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.member = member
            deposit.save()
            return redirect('savings:deposit_confirm', pk=deposit.pk)
    else:
        form = DepositAmountForm()
    return render(request, 'savings/deposit_new.html', {'form': form})


@login_required
def deposit_confirm(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk, member=request.user.member)

    if deposit.status != Deposit.PENDING:
        messages.info(request, 'This deposit has already been reviewed.')
        return redirect('savings:dashboard')

    if request.method == 'POST':
        form = DepositConfirmForm(request.POST, request.FILES, instance=deposit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment confirmation submitted — your deposit is now pending admin review.')
            return redirect('savings:dashboard')
    else:
        form = DepositConfirmForm(instance=deposit)

    return render(request, 'savings/deposit_confirm.html', {
        'form': form,
        'deposit': deposit,
    })


@login_required
def deposit_page(request):
    member = request.user.member
    if member.status != Member.APPROVED:
        messages.warning(request, "Your membership is pending approval. Please wait for admin confirmation.")
        return redirect('savings:dashboard')

    return render(request, 'savings/deposit_page.html', {
        'member': member,
        'member_id': member.member_id,
        'phone': member.phone_number,
    })


@login_required
@require_POST
def initiate_stk_push(request):
    try:
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))

        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        member = request.user.member

        # Create deposit
        deposit = Deposit.objects.create(
            member=member,
            amount=amount,
            status=Deposit.PENDING,
        )

        # Send notification
        NotificationService.send_notification(
            member=member,
            event_type='deposit_initiated',
            title='Deposit Initiated',
            message=f'Your deposit of KES {amount} has been initiated. Please complete the M-Pesa payment.',
            channel_name='in_app',
        )

        # Trigger STK Push
        from mpesa.utils import MpesaAPIClient
        try:
            client = MpesaAPIClient()
            stk_request = client.initiate_stk_push(
                member=member,
                amount=amount,
                phone_number=member.phone_number,
                deposit=deposit,
            )

            return JsonResponse({
                'success': True,
                'message': 'STK Push sent to your phone. Please enter your M-Pesa PIN.',
                'request_id': str(stk_request.request_id),
                'deposit_id': deposit.id,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def submit_approval_request(request):
    try:
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        message = data.get('message', '').strip()

        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        if not message or len(message) < 10:
            return JsonResponse({'error': 'Please provide payment details (minimum 10 characters)'}, status=400)

        member = request.user.member

        # Create approval request
        approval_req = DepositApprovalRequest.objects.create(
            member=member,
            amount=amount,
            message=message,
            status=DepositApprovalRequest.PENDING,
        )

        # Notify admins
        admin_email = settings.ADMIN_EMAIL
        try:
            send_mail(
                subject=f'New Deposit Approval Request - {member.member_id} (KES {amount})',
                message=f'''
Member: {member.user.get_full_name() or member.user.username} ({member.member_id})
Phone: {member.phone_number}
Amount: KES {amount}

Payment Details:
{message}

Please review and approve/reject this request in the admin panel.

Link: /admin/savings/depositapprovalrequest/{approval_req.id}/change/
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email notification error: {e}")

        # Send notification to member
        NotificationService.send_notification(
            member=member,
            event_type='deposit_initiated',
            title='Deposit Request Submitted',
            message=f'Your deposit request of KES {amount} has been submitted for admin approval.',
            channel_name='in_app',
        )

        return JsonResponse({
            'success': True,
            'message': 'Your deposit request has been submitted for admin approval.',
            'request_id': approval_req.id,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
