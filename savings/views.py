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
from .models import Deposit

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

    announcements = Announcement.objects.filter(is_active=True)[:5]

    return render(request, 'savings/dashboard.html', {
        'member': member,
        'balance': balance,
        'deposits': deposits,
        'this_month': this_month,
        'announcements': announcements,
        'profile_form': ProfileForm(instance=member),
        'chart_data': chart_data,
        'avatar_presets': AVATAR_PRESETS,
        'investment_level': INVESTMENT_LEVEL,
        'loans_level': LOANS_LEVEL,
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
