import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from api_clients.models import ApiClient
from products.models import Category, Product

from .models import Order, OrderStatus

User = get_user_model()


class OrderFrontTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="lea", password="ComplexPass123")
        cls.other_user = User.objects.create_user(username="marc", password="ComplexPass123")
        category = Category.objects.create(name="Bureautique")
        cls.product = Product.objects.create(
            category=category,
            sku="ORD-001",
            name="Clavier mecanique",
            slug="clavier-mecanique",
            price=Decimal("129.00"),
            stock=10,
            is_active=True,
        )

    def test_order_list_requires_login(self):
        response = self.client.get(reverse("orders:list"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('orders:list')}",
        )

    def test_order_create_creates_order_for_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("orders:create"),
            {
                "notes": "Livraison le matin",
                "lines-TOTAL_FORMS": "2",
                "lines-INITIAL_FORMS": "0",
                "lines-MIN_NUM_FORMS": "1",
                "lines-MAX_NUM_FORMS": "1000",
                "lines-0-product": str(self.product.id),
                "lines-0-quantity": "2",
                "lines-1-product": "",
                "lines-1-quantity": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(customer=self.user)
        self.assertEqual(order.lines.count(), 1)
        self.assertContains(response, order.number)
        self.assertContains(response, "258.00")

    def test_order_list_is_scoped_to_current_user(self):
        Order.objects.create(customer=self.user)
        Order.objects.create(customer=self.other_user)

        self.client.force_login(self.user)
        response = self.client.get(reverse("orders:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["orders"]), 1)


class OrderApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="sophie",
            email="sophie@example.com",
            password="ComplexPass123",
        )
        category = Category.objects.create(name="Expedition")
        cls.product = Product.objects.create(
            category=category,
            sku="ORD-API-001",
            name="Etiqueteuse",
            slug="etiqueteuse",
            price=Decimal("89.90"),
            stock=30,
            is_active=True,
        )
        cls.reader = ApiClient.objects.create(name="ERP Reader", scopes=["orders:read"])
        cls.reader_token = cls.reader.rotate_secret()
        cls.writer = ApiClient.objects.create(
            name="ERP Writer",
            scopes=["orders:read", "orders:write"],
        )
        cls.writer_token = cls.writer.rotate_secret()

    def test_openapi_spec_is_served(self):
        response = self.client.get(reverse("orders:api-openapi"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/api/orders/")
        self.assertContains(response, "orders:read")

    def test_orders_api_requires_bearer_token(self):
        response = self.client.get(reverse("orders:api-orders"))

        self.assertEqual(response.status_code, 401)

    def test_orders_api_lists_items_for_client_with_read_scope(self):
        Order.objects.create(customer=self.user)

        response = self.client.get(
            reverse("orders:api-orders"),
            HTTP_AUTHORIZATION=f"Bearer {self.reader_token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_orders_api_create_requires_write_scope(self):
        response = self.client.post(
            reverse("orders:api-orders"),
            data=json.dumps(
                {
                    "customer_id": self.user.id,
                    "notes": "Commande API",
                    "lines": [{"product_id": self.product.id, "quantity": 1}],
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.reader_token}",
        )

        self.assertEqual(response.status_code, 403)

    def test_orders_api_create_and_patch_with_write_scope(self):
        create_response = self.client.post(
            reverse("orders:api-orders"),
            data=json.dumps(
                {
                    "customer_id": self.user.id,
                    "status": OrderStatus.SUBMITTED,
                    "notes": "Commande machine",
                    "lines": [{"product_id": self.product.id, "quantity": 3}],
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.writer_token}",
        )

        self.assertEqual(create_response.status_code, 201)
        order_id = create_response.json()["id"]
        self.assertEqual(create_response.json()["total_amount"], "269.70")

        patch_response = self.client.patch(
            reverse("orders:api-order-detail", args=[order_id]),
            data=json.dumps({"status": OrderStatus.PREPARING}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.writer_token}",
        )

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["status"], OrderStatus.PREPARING)
