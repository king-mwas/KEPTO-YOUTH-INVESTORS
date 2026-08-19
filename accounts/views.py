from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, SignUpForm
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
            user = form.save()
            login(request, user)
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


@login_required
def update_profile(request):
    """Handle the inline profile-edit form on the dashboard (display name,
    savings goal, avatar). POST-only; always returns to the dashboard."""
    member = request.user.member
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
        else:
            # Surface the first error so the member knows what to fix.
            first_error = next(iter(form.errors.values()))[0]
            messages.error(request, first_error)
    return redirect('savings:dashboard')
