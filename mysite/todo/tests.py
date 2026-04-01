from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Task

User = get_user_model()


class TaskViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username="alice",
            password="ComplexPass123",
        )
        cls.bob = User.objects.create_user(
            username="bob",
            password="ComplexPass123",
        )

    def test_task_list_requires_login(self):
        response = self.client.get(reverse("task_list"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('task_list')}",
        )

    def test_task_list_is_scoped_to_authenticated_user(self):
        Task.objects.create(owner=self.alice, title="Tache Alice")
        Task.objects.create(owner=self.bob, title="Tache Bob")

        self.client.force_login(self.alice)
        response = self.client.get(reverse("task_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tache Alice")
        self.assertNotContains(response, "Tache Bob")

    def test_post_creates_task_for_current_user(self):
        self.client.force_login(self.alice)

        response = self.client.post(reverse("task_list"), {"title": "Preparation colis"})

        self.assertRedirects(response, reverse("task_list"))
        self.assertTrue(
            Task.objects.filter(owner=self.alice, title="Preparation colis").exists()
        )

    def test_toggle_task_rejects_access_to_another_user_task(self):
        other_task = Task.objects.create(owner=self.bob, title="Confidentiel")

        self.client.force_login(self.alice)
        response = self.client.post(reverse("toggle_task", args=[other_task.id]))

        self.assertEqual(response.status_code, 404)

    def test_toggle_task_updates_current_user_task(self):
        task = Task.objects.create(owner=self.alice, title="Relancer client")

        self.client.force_login(self.alice)
        response = self.client.post(reverse("toggle_task", args=[task.id]))

        self.assertRedirects(response, reverse("task_list"))
        task.refresh_from_db()
        self.assertTrue(task.is_done)
