import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class CatalogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.audio = Category.objects.create(name="Audio")
        cls.photo = Category.objects.create(name="Photo")

        cls.active_audio_product = Product.objects.create(
            category=cls.audio,
            sku="SKU-001",
            name="Casque Studio",
            slug="casque-studio",
            description="Un casque confortable pour le quotidien.",
            price=Decimal("149.90"),
            stock=12,
            is_active=True,
        )
        Product.objects.create(
            category=cls.audio,
            sku="SKU-002",
            name="Produit inactif",
            slug="produit-inactif",
            description="Ne doit pas apparaitre.",
            price=Decimal("19.90"),
            stock=0,
            is_active=False,
        )

    def test_catalog_page_renders_active_products(self):
        response = self.client.get(reverse("products:catalog"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/catalog.html")
        self.assertContains(response, "Casque Studio")
        self.assertNotContains(response, "Produit inactif")
        self.assertContains(response, "Audio")
        self.assertContains(response, "Photo")
        self.assertEqual([product.name for product in response.context["products"]], ["Casque Studio"])

    def test_catalog_page_filters_by_category(self):
        photo_product = Product.objects.create(
            category=self.photo,
            sku="SKU-003",
            name="Reflex Nova",
            slug="reflex-nova",
            description="Boitier photo compact.",
            price=Decimal("599.00"),
            stock=5,
            is_active=True,
        )

        response = self.client.get(
            reverse("products:catalog"),
            {"category": self.photo.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_category"], self.photo)
        self.assertEqual(response.context["products"], [photo_product])


class ProductsApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.audio = Category.objects.create(name="Audio")
        cls.photo = Category.objects.create(name="Photo")
        cls.product = Product.objects.create(
            category=cls.audio,
            sku="SKU-API-001",
            name="Casque API",
            slug="casque-api",
            description="Produit expose par l'API.",
            price=Decimal("149.90"),
            stock=12,
            is_active=True,
        )

    def test_openapi_spec_is_served(self):
        response = self.client.get(reverse("products:api-openapi"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "openapi: 3.0.3")
        self.assertContains(response, "/api/products/")

    def test_categories_collection_returns_counts(self):
        response = self.client.get(reverse("products:api-categories"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["items"][0]["name"], "Audio")
        self.assertEqual(payload["items"][0]["product_count"], 1)

    def test_create_category(self):
        response = self.client.post(
            reverse("products:api-categories"),
            data=json.dumps({"name": "Gaming"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Category.objects.filter(name="Gaming").exists())

    def test_delete_category_is_blocked_when_products_exist(self):
        response = self.client.delete(
            reverse("products:api-category-detail", args=[self.audio.id])
        )

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Category.objects.filter(pk=self.audio.id).exists())

    def test_create_product(self):
        response = self.client.post(
            reverse("products:api-products"),
            data=json.dumps(
                {
                    "category_id": self.photo.id,
                    "sku": "SKU-API-002",
                    "name": "Reflex API",
                    "slug": "reflex-api",
                    "description": "Produit cree via JSON.",
                    "price": "599.00",
                    "stock": 5,
                    "is_active": True,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["category"]["name"], "Photo")
        self.assertTrue(Product.objects.filter(sku="SKU-API-002").exists())

    def test_products_filtering_and_update(self):
        Product.objects.create(
            category=self.photo,
            sku="SKU-API-003",
            name="Camera API",
            slug="camera-api",
            description="Produit de test pour le filtrage.",
            price=Decimal("899.00"),
            stock=0,
            is_active=False,
        )

        list_response = self.client.get(
            reverse("products:api-products"),
            {"category_id": self.audio.id, "in_stock": "true"},
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["count"], 1)
        self.assertEqual(list_response.json()["items"][0]["sku"], self.product.sku)

        update_response = self.client.patch(
            reverse("products:api-product-detail", args=[self.product.id]),
            data=json.dumps({"stock": 8, "is_active": False}),
            content_type="application/json",
        )

        self.assertEqual(update_response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertFalse(self.product.is_active)

    def test_delete_product(self):
        response = self.client.delete(
            reverse("products:api-product-detail", args=[self.product.id])
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Product.objects.filter(pk=self.product.id).exists())
