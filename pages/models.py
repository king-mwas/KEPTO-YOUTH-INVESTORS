import re

from django.db import models

YOUTUBE_ID_RE = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([\w-]{11})')


class SiteSettings(models.Model):
    """Singleton (always pk=1) holding admin-editable, member-facing settings."""

    contact_email = models.EmailField(blank=True, help_text='Public contact email shown on the site.')
    paybill_number = models.CharField(max_length=20, blank=True, help_text='M-Pesa Paybill number for deposits.')
    bank_account_details = models.TextField(
        blank=True,
        help_text='e.g. Bank Name: XYZ Bank\nAccount Name: KEPTO Sacco\nAccount Number: 1234567890',
    )
    whatsapp_group_link = models.URLField(blank=True, help_text='Invite link to the members WhatsApp group. Also shown as the public contact WhatsApp link.')
    instagram_link = models.URLField(blank=True, help_text="Link to KEPTO's Instagram profile.")
    financial_literacy_video_url = models.URLField(blank=True, help_text='YouTube link for the financial literacy class.')
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def youtube_embed_url(self):
        match = YOUTUBE_ID_RE.search(self.financial_literacy_video_url or '')
        return f'https://www.youtube.com/embed/{match.group(1)}' if match else None

    def __str__(self):
        return 'Site Settings'


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} <{self.email}>"
