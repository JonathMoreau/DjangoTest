from django.test import TestCase
from django.test.client import RequestFactory

from .auth import require_api_client
from .models import ApiClient


class ApiClientAuthTests(TestCase):
    def test_require_api_client_accepts_valid_bearer_token(self):
        client = ApiClient.objects.create(name="ERP", scopes=["orders:read"])
        token = client.rotate_secret()
        request = RequestFactory().get(
            "/api/orders/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        response = require_api_client(request, scopes=["orders:read"])

        self.assertIsNone(response)
        self.assertEqual(request.api_client.pk, client.pk)

    def test_require_api_client_rejects_missing_scope(self):
        client = ApiClient.objects.create(name="WMS", scopes=["orders:read"])
        token = client.rotate_secret()
        request = RequestFactory().post(
            "/api/orders/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        response = require_api_client(request, scopes=["orders:write"])

        self.assertEqual(response.status_code, 403)
