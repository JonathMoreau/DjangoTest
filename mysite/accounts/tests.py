from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountsViewTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}",
        )

    def test_register_creates_user_and_logs_user_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "marie",
                "first_name": "Marie",
                "last_name": "Durand",
                "email": "marie@example.com",
                "password1": "ComplexPass123",
                "password2": "ComplexPass123",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            User.objects.filter(username="marie", email="marie@example.com").exists()
        )
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertContains(response, "Bonjour Marie")

    def test_login_redirects_to_dashboard(self):
        User.objects.create_user(username="nora", password="ComplexPass123")

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "nora",
                "password": "ComplexPass123",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertContains(response, "Bonjour nora")
