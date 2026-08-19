from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

kenyan_phone_validator = RegexValidator(
    regex=r'^0\d{9}$',
    message='Enter a valid 10-digit phone number starting with 0 (e.g. 0712345678).',
)

# Freeform display name: letters, numbers, spaces and . _ , - only (Instagram-ish),
# 1-30 chars. The "@" the UI shows is just a prefix, never stored.
display_name_validator = RegexValidator(
    regex=r'^[A-Za-z0-9 ._,\-]{1,30}$',
    message='Use 1–30 characters: letters, numbers, spaces and . _ , - only.',
)

# Level thresholds — kept here so views/templates never hard-code them.
KES_PER_LEVEL = 1000
INVESTMENT_LEVEL = 10   # KES 10,000 saved across 10+ deposits
LOANS_LEVEL = 25        # KES 25,000 saved across 25+ deposits


class Institution(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Industry(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'industries'

    def __str__(self):
        return self.name


class Member(models.Model):
    STUDENT = 'student'
    PROFESSIONAL = 'professional'
    MEMBER_TYPE_CHOICES = [
        (STUDENT, 'Student'),
        (PROFESSIONAL, 'Working Professional'),
    ]

    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='member')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)

    # Kenyan mobile number, e.g. 0712345678. The Member ID is the last 8 digits
    # (i.e. the number with its 07/01 network prefix stripped) — unique enough
    # to identify a member and used as the primary lookup key in the admin panel.
    phone_number = models.CharField(max_length=10, unique=True, validators=[kenyan_phone_validator])
    member_id = models.CharField(max_length=8, unique=True, editable=False, blank=True)

    member_type = models.CharField(max_length=20, choices=MEMBER_TYPE_CHOICES)

    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    year_of_study = models.PositiveSmallIntegerField(null=True, blank=True)

    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    business_name = models.CharField(max_length=150, blank=True)

    # --- profile customisation (member-editable from the dashboard) ---
    display_name = models.CharField(
        max_length=30, blank=True, validators=[display_name_validator],
        help_text='What you want to be called on your dashboard.',
    )
    savings_goal = models.DecimalField(
        max_digits=10, decimal_places=2, default=10000,
        help_text='Your personal savings target, in KES.',
    )
    avatar_preset = models.CharField(max_length=20, blank=True)  # e.g. "av1"; blank if a photo is used
    avatar_image = models.ImageField(upload_to='avatars/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.member_id = self.phone_number[2:]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member_id} ({self.user.get_username()})"

    # ------------------------------------------------------------------ display

    @property
    def label(self):
        """Name shown on the dashboard — the chosen display name, else username."""
        return self.display_name or self.user.get_username()

    @property
    def initials(self):
        source = (self.display_name or self.user.get_username()).strip()
        parts = [p for p in source.replace('.', ' ').replace('_', ' ').split() if p]
        if not parts:
            return '?'
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @property
    def avatar_url(self):
        """Uploaded photo wins; else the chosen preset; else None (fall back to initials)."""
        if self.avatar_image:
            return self.avatar_image.url
        if self.avatar_preset:
            return f'{settings.STATIC_URL}avatars/{self.avatar_preset}.svg'
        return None

    # ------------------------------------------------------------- savings/levels

    @property
    def balance(self):
        from savings.models import Deposit  # local import avoids a circular import
        total = self.deposits.filter(status=Deposit.APPROVED).aggregate(
            total=models.Sum('amount'))['total']
        return total or 0

    @property
    def approved_deposit_count(self):
        from savings.models import Deposit
        return self.deposits.filter(status=Deposit.APPROVED).count()

    @property
    def level(self):
        """Level is driven by savings (KES 1,000 = 1 level) but *gated* by the
        number of approved deposits, so a single large deposit can't rocket
        someone to Level 10. You must save the money AND make the deposits."""
        savings_level = int(self.balance // KES_PER_LEVEL)
        return min(savings_level, self.approved_deposit_count)

    @property
    def investment_unlocked(self):
        return self.level >= INVESTMENT_LEVEL

    @property
    def loans_unlocked(self):
        return self.level >= LOANS_LEVEL

    # ------------------------------------------------------------- investments

    @property
    def savings_committed(self):
        """Savings currently tied up in share-capital investments (pending or
        active) — this is money that can't be committed again."""
        from investments.models import Investment
        total = self.investments.filter(
            source=Investment.SAVINGS,
            status__in=[Investment.PENDING, Investment.ACTIVE],
        ).aggregate(t=models.Sum('amount'))['t']
        return total or 0

    @property
    def savings_available(self):
        """Savings a member could still move into share capital."""
        return self.balance - self.savings_committed

    @property
    def total_invested(self):
        from investments.models import Investment
        total = self.investments.filter(status=Investment.ACTIVE).aggregate(
            t=models.Sum('amount'))['t']
        return total or 0

    @property
    def total_investment_returns(self):
        from investments.models import Investment, InvestmentReturn
        total = InvestmentReturn.objects.filter(
            investment__member=self, investment__status=Investment.ACTIVE,
        ).aggregate(t=models.Sum('amount'))['t']
        return total or 0

    @property
    def next_level_hint(self):
        """What's still needed to reach the next level — whichever of the two
        gates (more savings or more deposits) is currently the blocker."""
        target = self.level + 1
        kes_needed = max(0, target * KES_PER_LEVEL - int(self.balance))
        deposits_needed = max(0, target - self.approved_deposit_count)
        if kes_needed and deposits_needed:
            return f'Save KES {kes_needed:,} more and make {deposits_needed} more deposit(s)'
        if kes_needed:
            return f'Save KES {kes_needed:,} more to reach Level {target}'
        if deposits_needed:
            return f'Make {deposits_needed} more deposit(s) to claim Level {target}'
        return f'Level {target} ready!'
