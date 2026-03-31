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
