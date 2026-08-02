from django import forms

from pages.models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'contact_email', 'paybill_number', 'bank_account_details', 'whatsapp_group_link',
            'instagram_link', 'financial_literacy_video_url',
        ]
        widgets = {
            'contact_email': forms.EmailInput(attrs={'placeholder': 'hello@kepto.co.ke'}),
            'bank_account_details': forms.Textarea(attrs={'rows': 4}),
            'whatsapp_group_link': forms.URLInput(attrs={'placeholder': 'https://chat.whatsapp.com/...'}),
            'instagram_link': forms.URLInput(attrs={'placeholder': 'https://www.instagram.com/...'}),
            'financial_literacy_video_url': forms.URLInput(attrs={'placeholder': 'https://www.youtube.com/watch?v=...'}),
        }
