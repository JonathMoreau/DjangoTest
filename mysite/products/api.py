import json
from pathlib import Path

from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import CategoryApiForm, ProductApiForm
from .models import Category, Product

OPENAPI_SPEC_PATH = Path(__file__).resolve().parent / "openapi" / "products-api.yaml"

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def api_error(detail, *, status=400, errors=None):
    payload = {"detail": detail}
    if errors is not None:
        payload["errors"] = errors
    return JsonResponse(payload, status=status)


def parse_request_payload(request):
    content_type = request.content_type or ""

    if content_type.startswith("application/json"):
        if not request.body:
            return {}, request.FILES

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("Le corps JSON est invalide.") from exc

        if not isinstance(payload, dict):
            raise ValueError("Le corps JSON doit etre un objet.")
        return payload, request.FILES

    if content_type.startswith("multipart/form-data") or content_type.startswith(
        "application/x-www-form-urlencoded"
    ):
        return request.POST.dict(), request.FILES

    if request.body:
        raise TypeError(
            "Content-Type non supporte. Utilisez application/json ou multipart/form-data."
        )

    return {}, request.FILES


def parse_boolean(value, field_name):
    if isinstance(value, bool):
        return value

    if isinstance(value, int) and value in {0, 1}:
        return bool(value)

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in TRUE_VALUES:
            return True
        if normalized in FALSE_VALUES:
            return False

    raise ValueError(f"Le champ '{field_name}' doit etre un booleen.")


def serialize_form_errors(form):
    return form.errors.get_json_data(escape_html=False)


def serialize_category(category):
    return {
        "id": category.id,
        "name": category.name,
        "product_count": getattr(category, "product_count", category.products.count()),
    }


def build_image_url(request, product):
    if not product.image:
        return None
    return request.build_absolute_uri(product.image.url)


def serialize_product(request, product):
    return {
        "id": product.id,
        "category": {
            "id": product.category_id,
            "name": product.category.name,
        },
        "sku": product.sku,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "image_url": build_image_url(request, product),
        "price": f"{product.price:.2f}",
        "stock": product.stock,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }


def normalize_product_payload(payload, *, partial):
    normalized = dict(payload)

    if "category_id" in normalized and "category" not in normalized:
        normalized["category"] = normalized.pop("category_id")

    if "is_active" in normalized:
        normalized["is_active"] = parse_boolean(normalized["is_active"], "is_active")
    elif not partial:
        normalized["is_active"] = True

    if "clear_image" in normalized:
        normalized["clear_image"] = parse_boolean(
            normalized["clear_image"],
            "clear_image",
        )
    elif not partial:
        normalized["clear_image"] = False

    if not partial:
        normalized.setdefault("description", "")
        normalized.setdefault("stock", 0)

    return normalized


def build_category_form_data(payload, *, instance=None):
    return {
        "name": payload.get("name", instance.name if instance else None),
    }


def build_product_form_data(payload, *, instance=None):
    return {
        "category": payload.get("category", instance.category_id if instance else None),
        "sku": payload.get("sku", instance.sku if instance else None),
        "name": payload.get("name", instance.name if instance else None),
        "slug": payload.get("slug", instance.slug if instance else None),
        "description": payload.get(
            "description",
            instance.description if instance else "",
        ),
        "price": payload.get("price", instance.price if instance else None),
        "stock": payload.get("stock", instance.stock if instance else 0),
        "is_active": payload.get("is_active", instance.is_active if instance else True),
    }


def get_category(category_id):
    try:
        return Category.objects.annotate(product_count=Count("products")).get(pk=category_id)
    except Category.DoesNotExist:
        return None


def get_product(product_id):
    try:
        return Product.objects.select_related("category").get(pk=product_id)
    except Product.DoesNotExist:
        return None


@require_http_methods(["GET"])
def openapi_spec(request):
    content = OPENAPI_SPEC_PATH.read_text(encoding="utf-8")
    return HttpResponse(content, content_type="application/yaml; charset=utf-8")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def categories_collection(request):
    if request.method == "GET":
        categories = Category.objects.annotate(product_count=Count("products")).order_by(
            "name"
        )
        items = [serialize_category(category) for category in categories]
        return JsonResponse({"count": len(items), "items": items})

    try:
        payload, _files = parse_request_payload(request)
    except ValueError as exc:
        return api_error(str(exc), status=400)
    except TypeError as exc:
        return api_error(str(exc), status=415)

    form = CategoryApiForm(build_category_form_data(payload))
    if not form.is_valid():
        return api_error(
            "Les donnees envoyees sont invalides.",
            status=400,
            errors=serialize_form_errors(form),
        )

    category = form.save()
    return JsonResponse(serialize_category(category), status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
def category_detail(request, category_id):
    category = get_category(category_id)
    if category is None:
        return api_error("Categorie introuvable.", status=404)

    if request.method == "GET":
        return JsonResponse(serialize_category(category))

    if request.method == "DELETE":
        try:
            category.delete()
        except ProtectedError:
            return api_error(
                "Impossible de supprimer une categorie qui possede encore des produits.",
                status=409,
            )
        return HttpResponse(status=204)

    try:
        payload, _files = parse_request_payload(request)
    except ValueError as exc:
        return api_error(str(exc), status=400)
    except TypeError as exc:
        return api_error(str(exc), status=415)

    form = CategoryApiForm(
        build_category_form_data(payload, instance=category),
        instance=category,
    )
    if not form.is_valid():
        return api_error(
            "Les donnees envoyees sont invalides.",
            status=400,
            errors=serialize_form_errors(form),
        )

    updated_category = form.save()
    updated_category.product_count = category.product_count
    return JsonResponse(serialize_category(updated_category))


@csrf_exempt
@require_http_methods(["GET", "POST"])
def products_collection(request):
    if request.method == "GET":
        products = Product.objects.select_related("category").order_by("name")

        category_id = request.GET.get("category_id")
        if category_id:
            if not category_id.isdigit():
                return api_error("Le parametre 'category_id' doit etre un entier.", status=400)
            products = products.filter(category_id=int(category_id))

        is_active = request.GET.get("is_active")
        if is_active is not None:
            try:
                products = products.filter(is_active=parse_boolean(is_active, "is_active"))
            except ValueError as exc:
                return api_error(str(exc), status=400)

        in_stock = request.GET.get("in_stock")
        if in_stock is not None:
            try:
                has_stock = parse_boolean(in_stock, "in_stock")
            except ValueError as exc:
                return api_error(str(exc), status=400)
            products = products.filter(stock__gt=0) if has_stock else products.filter(stock=0)

        search = request.GET.get("search")
        if search:
            products = products.filter(
                Q(name__icontains=search)
                | Q(sku__icontains=search)
                | Q(slug__icontains=search)
            )

        items = [serialize_product(request, product) for product in products]
        return JsonResponse({"count": len(items), "items": items})

    try:
        payload, files = parse_request_payload(request)
        normalized_payload = normalize_product_payload(payload, partial=False)
    except ValueError as exc:
        return api_error(str(exc), status=400)
    except TypeError as exc:
        return api_error(str(exc), status=415)

    form = ProductApiForm(build_product_form_data(normalized_payload), files=files)
    if not form.is_valid():
        return api_error(
            "Les donnees envoyees sont invalides.",
            status=400,
            errors=serialize_form_errors(form),
        )

    product = form.save()
    product = Product.objects.select_related("category").get(pk=product.pk)
    return JsonResponse(serialize_product(request, product), status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
def product_detail(request, product_id):
    product = get_product(product_id)
    if product is None:
        return api_error("Produit introuvable.", status=404)

    if request.method == "GET":
        return JsonResponse(serialize_product(request, product))

    if request.method == "DELETE":
        product.delete()
        return HttpResponse(status=204)

    try:
        payload, files = parse_request_payload(request)
        normalized_payload = normalize_product_payload(payload, partial=True)
    except ValueError as exc:
        return api_error(str(exc), status=400)
    except TypeError as exc:
        return api_error(str(exc), status=415)

    clear_image = normalized_payload.pop("clear_image", False)
    if clear_image and files.get("image"):
        return api_error(
            "Utilisez soit 'clear_image', soit un nouveau fichier 'image', mais pas les deux.",
            status=400,
        )

    if clear_image:
        product.image = None

    form = ProductApiForm(
        build_product_form_data(normalized_payload, instance=product),
        files=files,
        instance=product,
    )
    if not form.is_valid():
        return api_error(
            "Les donnees envoyees sont invalides.",
            status=400,
            errors=serialize_form_errors(form),
        )

    updated_product = form.save()
    updated_product = Product.objects.select_related("category").get(pk=updated_product.pk)
    return JsonResponse(serialize_product(request, updated_product))
