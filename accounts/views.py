from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import SignUpForm
from .models import Industry, Institution


@login_required
def post_login_redirect(request):
    if hasattr(request.user, 'member'):
        return redirect('savings:dashboard')
    if request.user.is_staff:
        return redirect('adminpanel:dashboard')
    return redirect('pages:home')


def signup(request):
    if request.user.is_authenticated:
        return redirect('accounts:post_login_redirect')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # User + Member are saved together: if the Member can't be created,
            # no half-registered user is left behind (invisible to the admin panel).
            with transaction.atomic():
                user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('savings:dashboard')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {
        'form': form,
        'institutions': Institution.objects.values_list('name', flat=True),
        'industries': Industry.objects.values_list('name', flat=True),
    })


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'member': request.user.member})
