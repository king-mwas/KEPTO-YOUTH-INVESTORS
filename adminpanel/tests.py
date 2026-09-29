from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Member

SIGNUP_DATA = {
    'username': 'newstudent', 'email': 'new@example.com', 'phone_number': '0712000111',
    'password1': 'Str0ng!Pass', 'password2': 'Str0ng!Pass',
    'member_type': 'student', 'institution': 'JKUAT', 'year_of_study': '2',
}


@override_settings(ALLOWED_HOSTS=['testserver'])
class PendingMembersTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'x')

    def test_signup_appears_in_pending_members(self):
        self.client.post(reverse('accounts:signup'), SIGNUP_DATA)
        self.client.logout()
        self.client.force_login(self.admin)
        response = self.client.get(reverse('adminpanel:members_pending'))
        self.assertContains(response, '12000111')
        self.assertEqual(Member.objects.get().status, Member.PENDING)

    def test_failed_member_save_rolls_back_user(self):
        with mock.patch.object(Member, 'save', side_effect=RuntimeError('boom')):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse('accounts:signup'), SIGNUP_DATA)
        self.assertFalse(User.objects.filter(username='newstudent').exists())

    def test_incomplete_signup_is_listed_and_removable(self):
        orphan = User.objects.create_user('orphan', 'o@example.com', 'x')
        self.client.force_login(self.admin)
        response = self.client.get(reverse('adminpanel:members_pending'))
        self.assertContains(response, 'orphan')
        self.assertNotContains(response, '>boss<')

        self.client.post(reverse('adminpanel:members_pending'),
                         {'action': 'remove_incomplete', 'user_id': orphan.pk})
        self.assertFalse(User.objects.filter(pk=orphan.pk).exists())
