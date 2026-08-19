from decimal import Decimal

from django.conf import settings
from django.db import models

from accounts.models import Member


class InvestmentOption(models.Model):
    """An admin-managed thing members can invest in (Share Capital, bonds,
    T-bills, stock/shares, liquidity pool, money-market fund, …)."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    # Optional advertised return, % per annum. Blank for variable options
    # (stock, liquidity pool) where there's no fixed rate.
    annual_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Advertised return, % per annum. Leave blank if variable.',
    )
    about = models.TextField(
        blank=True,
        help_text="What the money is used for — e.g. a group project. Shown to members.",
    )
    # Share Capital is bought from a member's savings; everything else is
    # funded by a fresh investment deposit.
    funded_from_savings = models.BooleanField(
        default=False,
        help_text='If on, members buy this using their existing savings (e.g. Share Capital). '
                  'If off, it is funded by a new investment deposit.',
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Investment(models.Model):
    """A member's stake in one option. Admin-approved before it goes active;
    returns are recorded by staff over time."""

    PENDING = 'pending'
    ACTIVE = 'active'
    REJECTED = 'rejected'
    CLOSED = 'closed'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACTIVE, 'Active'),
        (REJECTED, 'Rejected'),
        (CLOSED, 'Closed'),
    ]

    SAVINGS = 'savings'
    NEW_DEPOSIT = 'new_deposit'
    SOURCE_CHOICES = [
        (SAVINGS, 'From savings'),
        (NEW_DEPOSIT, 'New investment deposit'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='investments')
    option = models.ForeignKey(InvestmentOption, on_delete=models.PROTECT, related_name='investments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES)
    reference = models.CharField(max_length=60, blank=True, help_text='M-Pesa code / note for a new deposit.')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    admin_note = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_investments',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.member_id} · {self.option.name} · KES {self.amount} ({self.status})"

    @property
    def total_returns(self):
        return self.returns.aggregate(t=models.Sum('amount'))['t'] or Decimal('0')

    @property
    def current_value(self):
        return self.amount + self.total_returns

    @property
    def counts_against_savings(self):
        """Money committed out of savings that is still tied up."""
        return self.source == self.SAVINGS and self.status in (self.PENDING, self.ACTIVE)


class InvestmentReturn(models.Model):
    """A real return/payout an admin records against an active investment."""

    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='returns')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recorded_returns',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"KES {self.amount} on {self.investment_id}"
