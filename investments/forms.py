from decimal import Decimal

from django import forms

from .models import Investment, InvestmentOption


class InvestForm(forms.Form):
    """A member committing money to one option. `member` and `option` are
    passed in so we can enforce the money rules for this specific case."""

    amount = forms.DecimalField(min_value=Decimal('1'), max_digits=12, decimal_places=2)
    reference = forms.CharField(max_length=60, required=False)

    def __init__(self, *args, member=None, option=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.member = member
        self.option = option

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if self.option.funded_from_savings:
            available = self.member.savings_available
            if amount > available:
                raise forms.ValidationError(
                    f'You can commit at most KES {available:,.0f} from your savings '
                    f'(the rest is already committed or not yet saved).'
                )
        return amount

    def save(self):
        source = (Investment.SAVINGS if self.option.funded_from_savings
                  else Investment.NEW_DEPOSIT)
        return Investment.objects.create(
            member=self.member,
            option=self.option,
            amount=self.cleaned_data['amount'],
            source=source,
            reference=self.cleaned_data.get('reference', ''),
            status=Investment.PENDING,
        )
