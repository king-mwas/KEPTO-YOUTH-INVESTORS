from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from announcements.models import Announcement
from accounts.forms import ProfileForm
from accounts.models import INVESTMENT_LEVEL, LOANS_LEVEL, Member

from .forms import DepositAmountForm, DepositConfirmForm
from .models import Deposit, DepositApprovalRequest

# Preset avatar ids shipped as static SVGs (static/avatars/av1.svg …).
AVATAR_PRESETS = ['av1', 'av2', 'av3', 'av4', 'av5', 'av6']


def _month_start(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _balance_series(deposits, granularity):
    """Cumulative account balance at the end of each recent period. `deposits`
    is a list of (created_at, amount) for APPROVED deposits, sorted or not.
    Returns [{'label': str, 'value': float}, …] oldest → newest."""
    now = timezone.localtime()
    points = []

    if granularity == 'weekly':
        # Last 12 weeks, each point = end of that week.
        ends = [now - timedelta(weeks=(11 - i)) for i in range(12)]
        fmt = lambda d: d.strftime('%d %b')
    elif granularity == 'yearly':
        ends = [now.replace(year=now.year - (4 - i), month=12, day=31, hour=23,
                            minute=59, second=59) for i in range(5)]
        fmt = lambda d: d.strftime('%Y')
    else:  # monthly — last 12 months
        ends = []
        anchor = _month_start(now)
        for i in range(12):
            m = anchor.month - (11 - i)
            y = anchor.year
            while m <= 0:
                m += 12
                y -= 1
            # end of that month ≈ start of next month
            nm, ny = (m + 1, y) if m < 12 else (1, y + 1)
            ends.append(now.replace(year=ny, month=nm, day=1, hour=0, minute=0,
                                    second=0, microsecond=0) - timedelta(seconds=1))
        fmt = lambda d: d.strftime('%b')

    for end in ends:
        cumulative = sum(float(a) for (c, a) in deposits if c <= end)
        points.append({'label': fmt(end), 'value': round(cumulative, 2)})
    return points


@login_required
def dashboard(request):
    member = request.user.member
    approved = member.deposits.filter(status=Deposit.APPROVED)
    balance = approved.aggregate(total=Sum('amount'))['total'] or 0
    deposits = member.deposits.all()

    # This-month total (approved).
    month_start = _month_start(timezone.localtime())
    this_month = approved.filter(created_at__gte=month_start).aggregate(
        total=Sum('amount'))['total'] or 0

    # Balance-over-time chart data (all three granularities; JS toggles them).
    approved_pairs = list(approved.values_list('created_at', 'amount'))
    chart_data = {
        'weekly': _balance_series(approved_pairs, 'weekly'),
        'monthly': _balance_series(approved_pairs, 'monthly'),
        'yearly': _balance_series(approved_pairs, 'yearly'),
        'goal': float(member.savings_goal),
    }
    approved_deposits = member.deposits.filter(status=Deposit.APPROVED)
    balance = approved_deposits.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    deposits = member.deposits.all()[:10]
    total_deposits = approved_deposits.count()

    # This month
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_deposits = approved_deposits.filter(created_at__gte=month_start)
    this_month_amount = this_month_deposits.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    this_month_count = this_month_deposits.count()

    # Goal progress
    goal_amount = member.savings_goal
    goal_pct = 0
    goal_remaining = None
    if goal_amount and goal_amount > 0:
        goal_pct = min(100, int((balance / goal_amount) * 100))
        goal_remaining = max(Decimal('0'), goal_amount - balance)

    # Gamification: level = 1 + (approved deposits / 3)
    level = 1 + (total_deposits // 3)
    deposits_to_next_level = 3 - (total_deposits % 3)

    # Streak: count consecutive weeks with at least one deposit
    streak_weeks = _calculate_streak(approved_deposits)

    # Initials for avatar
    initials = (member.user.first_name[:1] + (member.user.last_name[:1] if member.user.last_name else '')).upper() or member.user.username[:2].upper()
    display_name = member.user.first_name or member.user.username

    announcements = Announcement.objects.filter(is_active=True)[:5]

    return render(request, 'savings/dashboard.html', {
        'member': member,
        'balance': balance,
        'deposits': deposits,
        'this_month': this_month,
        'total_deposits': total_deposits,
        'this_month_amount': this_month_amount,
        'this_month_count': this_month_count,
        'goal_amount': goal_amount,
        'goal_label': member.savings_goal_label,
        'goal_pct': goal_pct,
        'goal_remaining': goal_remaining,
        'level': level,
        'deposits_to_next_level': deposits_to_next_level,
        'streak_weeks': streak_weeks,
        'initials': initials,
        'display_name': display_name,
        'announcements': announcements,
        'profile_form': ProfileForm(instance=member),
        'chart_data': chart_data,
        'avatar_presets': AVATAR_PRESETS,
        'investment_level': INVESTMENT_LEVEL,
        'loans_level': LOANS_LEVEL,
    })


def _calculate_streak(approved_deposits):
    weeks = set()
    for d in approved_deposits.order_by('-created_at'):
        year, week, _ = d.created_at.isocalendar()
        weeks.add((year, week))
    if not weeks:
        return 0
    now = timezone.now()
    current_year, current_week, _ = now.isocalendar()
    streak = 0
    y, w = current_year, current_week
    while (y, w) in weeks:
        streak += 1
        # go to previous week
        prev = timezone.datetime(y, 1, 1) + timedelta(weeks=w - 2)
        y, w, _ = prev.isocalendar()
    return streak


@login_required
def set_goal(request):
    member = request.user.member
    if request.method == 'POST':
        raw = request.POST.get('goal_amount', '0') or '0'
        cleaned = raw.replace(',', '').replace(' ', '').strip()
        label = request.POST.get('goal_label', '').strip()[:100]
        try:
            amount = Decimal(cleaned)
            if amount > 0:
                member.savings_goal = amount
                member.savings_goal_label = label
                member.save()
                messages.success(request, f'Goal set: KES {amount:,.0f}{" for " + label if label else ""}!')
            else:
                member.savings_goal = None
                member.savings_goal_label = ''
                member.save()
                messages.info(request, 'Savings goal cleared.')
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Please enter a valid amount (numbers only, e.g. 10000 or 10,000).')
    return redirect('savings:dashboard')


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
