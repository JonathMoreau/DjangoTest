from django.test import TestCase
from django.urls import reverse


class ApiDocsViewTests(TestCase):
    def test_docs_index_lists_registered_domains(self):
        response = self.client.get(reverse("api_docs:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "api_docs/index.html")
        self.assertContains(response, "Catalogue produits")
        self.assertContains(response, reverse("api_docs:domain-docs", args=["products"]))

    def test_domain_docs_page_uses_registered_openapi_spec(self):
        response = self.client.get(reverse("api_docs:domain-docs", args=["products"]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "api_docs/domain_detail.html")
        self.assertContains(response, reverse("products:api-openapi"))
        self.assertContains(response, "Catalogue produits")
