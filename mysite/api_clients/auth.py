from functools import wraps

from django.http import JsonResponse

from .models import ApiClient


def api_error(detail, *, status):
    return JsonResponse({"detail": detail}, status=status)


def authenticate_api_client(request):
    header = request.META.get("HTTP_AUTHORIZATION", "").strip()
    if not header.startswith("Bearer "):
        return None

    token = header[7:].strip()
    if "." not in token:
        return None

    client_id, raw_secret = token.split(".", 1)
    if not client_id or not raw_secret:
        return None

    try:
        client = ApiClient.objects.get(client_id=client_id, is_active=True)
    except ApiClient.DoesNotExist:
        return None

    if not client.check_secret(raw_secret):
        return None

    client.mark_used()
    return client


def require_api_client(request, *, scopes):
    client = authenticate_api_client(request)
    if client is None:
        return api_error(
            "Authentification M2M requise. Utilisez un jeton Bearer valide.",
            status=401,
        )

    if not client.has_scopes(scopes):
        return api_error(
            "Le client API ne possede pas les scopes necessaires.",
            status=403,
        )

    request.api_client = client
    return None


def api_client_required(*required_scopes):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            response = require_api_client(request, scopes=required_scopes)
            if response is not None:
                return response
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
