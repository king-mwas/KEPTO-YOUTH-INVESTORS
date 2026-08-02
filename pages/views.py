from django.contrib import messages
from django.shortcuts import redirect, render

from announcements.models import Announcement

from .forms import ContactForm


def home(request):
    announcements = Announcement.objects.filter(is_active=True)[:5]
    return render(request, 'pages/home.html', {'announcements': announcements})


def about(request):
    return render(request, 'pages/about.html')


def entrepreneurship(request):
    return render(request, 'pages/entrepreneurship.html')


def savings(request):
    return render(request, 'pages/savings.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for reaching out — we'll get back to you soon.")
            return redirect('pages:contact')
    else:
        form = ContactForm()
    return render(request, 'pages/contact.html', {'form': form})
