import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Industry, Institution, Member

PHONE_RE = re.compile(r'^0\d{9}$')
USERNAME_RE = re.compile(r'^[A-Za-z0-9@._]+$')


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. your Instagram handle'}),
        help_text='You can use letters, numbers, and @ . _ (Tip: use your Instagram handle for easy remembering)',
    )
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        label='Phone Number',
        max_length=10,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 0712345678', 'inputmode': 'numeric'}),
        help_text='Your Member ID is generated from this number.',
    )
    member_type = forms.ChoiceField(choices=Member.MEMBER_TYPE_CHOICES, widget=forms.HiddenInput)

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not USERNAME_RE.match(username):
            raise forms.ValidationError(
                'Username can only contain letters, numbers, and these symbols: @ . _'
            )
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken. Try another one.')
        return username

    institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'list': 'institution-options', 'placeholder': 'Start typing your school...'}),
    )
    year_of_study = forms.IntegerField(required=False, min_value=1, max_value=7)

    industry = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'list': 'industry-options', 'placeholder': 'Start typing your industry...'}),
    )
    business_name = forms.CharField(required=False, max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not PHONE_RE.match(phone):
            raise forms.ValidationError('Enter a valid 10-digit phone number starting with 0 (e.g. 0712345678).')
        if Member.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('An account with this phone number already exists.')

        member_id = phone[2:]
        if Member.objects.filter(member_id=member_id).exists():
            raise forms.ValidationError('This phone number maps to a Member ID that is already in use — please double-check the number.')

        return phone

    def clean(self):
        cleaned_data = super().clean()
        member_type = cleaned_data.get('member_type')

        if member_type == Member.STUDENT:
            if not cleaned_data.get('institution'):
                self.add_error('institution', 'Please tell us which school you attend.')
            if not cleaned_data.get('year_of_study'):
                self.add_error('year_of_study', 'Please tell us which year of study you are in.')
        elif member_type == Member.PROFESSIONAL:
            if not cleaned_data.get('industry'):
                self.add_error('industry', 'Please tell us which industry you work in.')
            if not cleaned_data.get('business_name'):
                self.add_error('business_name', 'Please tell us the name of your business/employer.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            self._create_member(user)
        return user

    def _create_member(self, user):
        member_type = self.cleaned_data['member_type']
        member = Member(user=user, member_type=member_type, phone_number=self.cleaned_data['phone_number'])

        if member_type == Member.STUDENT:
            institution_name = self.cleaned_data['institution'].strip()
            institution, _ = Institution.objects.get_or_create(name=institution_name)
            member.institution = institution
            member.year_of_study = self.cleaned_data['year_of_study']
        else:
            industry_name = self.cleaned_data['industry'].strip()
            industry, _ = Industry.objects.get_or_create(name=industry_name)
            member.industry = industry
            member.business_name = self.cleaned_data['business_name'].strip()

        member.save()
        return member
