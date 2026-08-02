from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from announcements.models import Announcement
from accounts.models import Member

from .forms import DepositAmountForm, DepositConfirmForm
from .models import Deposit


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
