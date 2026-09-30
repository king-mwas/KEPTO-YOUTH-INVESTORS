from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import INVESTMENT_LEVEL

from .forms import InvestForm
from .models import Investment, InvestmentOption


@login_required
def home(request):
    """Member investment page. Locked below Level 10; otherwise shows the
    options and the member's own investments."""
    member = request.user.member
    if not member.investment_unlocked:
        return render(request, 'investments/locked.html', {
            'member': member,
            'investment_level': INVESTMENT_LEVEL,
        })

    options = InvestmentOption.objects.filter(is_active=True)
    investments = member.investments.select_related('option').all()

    return render(request, 'investments/home.html', {
        'member': member,
        'options': options,
        'investments': investments,
    })


@login_required
def invest(request, slug):
    """Handle the invest form for one option."""
    member = request.user.member
    if not member.investment_unlocked:
        messages.warning(request, 'Reach Level 10 to unlock investments.')
        return redirect('savings:dashboard')

    option = get_object_or_404(InvestmentOption, slug=slug, is_active=True)

    if request.method == 'POST':
        form = InvestForm(request.POST, member=member, option=option)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Your KES {form.cleaned_data["amount"]:,.0f} into {option.name} '
                f'is pending admin approval.',
            )
            return redirect('investments:home')
        messages.error(request, next(iter(form.errors.values()))[0])

    return redirect('investments:home')
