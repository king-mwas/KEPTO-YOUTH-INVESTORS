from decimal import Decimal

from django import forms

from .models import Deposit


class DepositAmountForm(forms.ModelForm):
    class Meta:
        model = Deposit
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '1', 'step': '1', 'placeholder': 'e.g. 500'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= Decimal('0'):
            raise forms.ValidationError('Enter an amount greater than zero.')
        return amount


class DepositConfirmForm(forms.ModelForm):
    class Meta:
        model = Deposit
        fields = ['transaction_code', 'proof']
        widgets = {
            'transaction_code': forms.TextInput(attrs={'placeholder': 'e.g. QGT7X9YABC'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('transaction_code') and not cleaned_data.get('proof'):
            raise forms.ValidationError('Enter your M-Pesa transaction code or upload proof of payment.')
        return cleaned_data
