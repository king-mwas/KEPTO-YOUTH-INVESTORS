from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

kenyan_phone_validator = RegexValidator(
    regex=r'^0\d{9}$',
    message='Enter a valid 10-digit phone number starting with 0 (e.g. 0712345678).',
)


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

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.member_id = self.phone_number[2:]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member_id} ({self.user.get_username()})"
