from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Industry, Institution, Member
from pages.models import SiteSettings
from savings.models import Deposit

from .forms import SiteSettingsForm

# A pending deposit is only ready for admin review once the member has
# actually submitted a transaction code or proof of payment.
UNCONFIRMED = Q(transaction_code='') & (Q(proof='') | Q(proof__isnull=True))


def _group_breakdown(model, relation_name):
    groups = []
    for obj in model.objects.all():
        member_count = Member.objects.filter(**{relation_name: obj}, status=Member.APPROVED).count()
        if member_count == 0:
            continue
        total_capital = Deposit.objects.filter(
            **{f'member__{relation_name}': obj}, status=Deposit.APPROVED,
        ).aggregate(total=Sum('amount'))['total'] or 0
        groups.append({'name': obj.name, 'member_count': member_count, 'total_capital': total_capital})
    groups.sort(key=lambda g: -g['total_capital'])
    return groups


@staff_member_required
def dashboard(request):
    total_capital = Deposit.objects.filter(status=Deposit.APPROVED).aggregate(total=Sum('amount'))['total'] or 0
    total_members = Member.objects.filter(status=Member.APPROVED).count()
    pending_members_count = Member.objects.filter(status=Member.PENDING).count()
    pending_deposits_count = Deposit.objects.filter(status=Deposit.PENDING).exclude(UNCONFIRMED).count()

    institution_groups = _group_breakdown(Institution, 'institution')
    industry_groups = _group_breakdown(Industry, 'industry')

    monthly = list(
        Deposit.objects.filter(status=Deposit.APPROVED, reviewed_at__isnull=False)
        .annotate(month=TruncMonth('reviewed_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    running_total = 0
    growth = []
    for row in monthly:
        running_total += row['total']
        growth.append({'month': row['month'], 'added': row['total'], 'cumulative': running_total})
    max_cumulative = growth[-1]['cumulative'] if growth else 0
    for row in growth:
        row['bar_pct'] = (row['cumulative'] / max_cumulative * 100) if max_cumulative else 0

    return render(request, 'adminpanel/dashboard.html', {
        'total_capital': total_capital,
        'total_members': total_members,
        'pending_members_count': pending_members_count,
        'pending_deposits_count': pending_deposits_count,
        'institution_groups': institution_groups,
        'industry_groups': industry_groups,
        'growth': growth,
    })


@staff_member_required
def members_pending(request):
    if request.method == 'POST':
        member = get_object_or_404(Member, pk=request.POST.get('member_id'))
        action = request.POST.get('action')
        if action == 'approve':
            member.status = Member.APPROVED
            member.save()
            messages.success(request, f"{member.member_id} approved.")
        elif action == 'reject':
            member.status = Member.REJECTED
            member.save()
            member.user.is_active = False
            member.user.save()
            messages.success(request, f"{member.member_id} rejected.")
        return redirect('adminpanel:members_pending')

    members = Member.objects.filter(status=Member.PENDING).select_related('user', 'institution', 'industry')
    return render(request, 'adminpanel/members_pending.html', {'members': members})


@staff_member_required
def deposits_pending(request):
    if request.method == 'POST':
        deposit = get_object_or_404(Deposit, pk=request.POST.get('deposit_id'))
        action = request.POST.get('action')
        if action == 'approve':
            if not deposit.is_confirmed:
                messages.error(request, "Can't approve — the member hasn't submitted a transaction code or proof yet.")
            else:
                deposit.status = Deposit.APPROVED
                deposit.reviewed_by = request.user
                deposit.reviewed_at = timezone.now()
                deposit.save()
                messages.success(request, f"Approved KES {deposit.amount} for {deposit.member.member_id}.")
        elif action == 'reject':
            deposit.status = Deposit.REJECTED
            deposit.reviewed_by = request.user
            deposit.reviewed_at = timezone.now()
            deposit.save()
            messages.success(request, f"Rejected deposit for {deposit.member.member_id}.")
        return redirect('adminpanel:deposits_pending')

    deposits = Deposit.objects.filter(status=Deposit.PENDING).select_related('member', 'member__user')
    return render(request, 'adminpanel/deposits_pending.html', {'deposits': deposits})


@staff_member_required
def site_settings(request):
    settings_obj = SiteSettings.load()

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site settings updated.')
            return redirect('adminpanel:site_settings')
    else:
        form = SiteSettingsForm(instance=settings_obj)

    return render(request, 'adminpanel/site_settings.html', {'form': form})


@staff_member_required
def member_search(request):
    query = request.GET.get('q', '').strip()
    member = None
    balance = 0
    deposits = []

    if query:
        member = Member.objects.filter(member_id=query).select_related('user', 'institution', 'industry').first()
        if member:
            balance = member.deposits.filter(status=Deposit.APPROVED).aggregate(total=Sum('amount'))['total'] or 0
            deposits = member.deposits.all()
        else:
            messages.error(request, f"No member found with Member ID '{query}'.")

    return render(request, 'adminpanel/member_search.html', {
        'query': query, 'member': member, 'balance': balance, 'deposits': deposits,
    })
