import json
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from api_clients.auth import require_api_client
from products.models import Product

from .models import Order, OrderLine, OrderStatus

OPENAPI_SPEC_PATH = Path(__file__).resolve().parent / "openapi" / "orders-api.yaml"
User = get_user_model()


def api_error(detail, *, status=400, errors=None):
    payload = {"detail": detail}
    if errors is not None:
        payload["errors"] = errors
    return JsonResponse(payload, status=status)


def parse_request_payload(request):
    if not (request.content_type or "").startswith("application/json"):
        if request.body:
            raise TypeError("Content-Type non supporte. Utilisez application/json.")
        return {}

    if not request.body:
        return {}

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Le corps JSON est invalide.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Le corps JSON doit etre un objet.")
    return payload


def serialize_order(order):
    return {
        "id": order.id,
        "number": order.number,
        "customer": {
            "id": order.customer_id,
            "username": order.customer.username,
            "email": order.customer.email,
        },
        "status": order.status,
        "notes": order.notes,
        "total_quantity": order.total_quantity,
        "total_amount": f"{order.total_amount:.2f}",
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "lines": [
            {
                "id": line.id,
                "product_id": line.product_id,
                "product_name": line.product_name,
                "sku": line.sku_snapshot,
                "unit_price": f"{line.unit_price:.2f}",
                "quantity": line.quantity,
                "line_total": f"{line.total_amount:.2f}",
            }
            for line in order.lines.all()
        ],
    }


def get_order(order_id):
    try:
        return Order.objects.select_related("customer").prefetch_related("lines").get(pk=order_id)
    except Order.DoesNotExist:
        return None


def validate_lines(lines):
    if not isinstance(lines, list) or not lines:
        raise ValueError("Le champ 'lines' doit contenir au moins une ligne.")

    validated_lines = []
    for index, item in enumerate(lines, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"La ligne {index} doit etre un objet JSON.")

        product_id = item.get("product_id")
        quantity = item.get("quantity")

        if not isinstance(product_id, int):
            raise ValueError(f"La ligne {index} doit contenir un 'product_id' entier.")

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError(f"La ligne {index} doit contenir une 'quantity' positive.")

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist as exc:
            raise ValueError(f"Produit introuvable ou inactif pour la ligne {index}.") from exc

        validated_lines.append(
            {
                "product": product,
                "quantity": quantity,
                "unit_price": Decimal(product.price),
            }
        )

    return validated_lines


@require_http_methods(["GET"])
def openapi_spec(request):
    content = OPENAPI_SPEC_PATH.read_text(encoding="utf-8")
    return HttpResponse(content, content_type="application/yaml; charset=utf-8")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def orders_collection(request):
    auth_response = require_api_client(
        request,
        scopes=["orders:read"] if request.method == "GET" else ["orders:write"],
    )
    if auth_response is not None:
        return auth_response

    if request.method == "GET":
        orders = Order.objects.select_related("customer").prefetch_related("lines").order_by(
            "-created_at"
        )

        status = request.GET.get("status")
        if status:
            orders = orders.filter(status=status)

        search = request.GET.get("search")
        if search:
            orders = orders.filter(number__icontains=search)

        items = [serialize_order(order) for order in orders]
        return JsonResponse({"count": len(items), "items": items})

    try:
        payload = parse_request_payload(request)
        lines = validate_lines(payload.get("lines"))
    except ValueError as exc:
        return api_error(str(exc), status=400)
    except TypeError as exc:
        return api_error(str(exc), status=415)

    customer_id = payload.get("customer_id")
    if not isinstance(customer_id, int):
        return api_error("Le champ 'customer_id' doit etre un entier.", status=400)

    status = payload.get("status", OrderStatus.SUBMITTED)
    if status not in OrderStatus.values:
        return api_error("Le statut de commande est invalide.", status=400)

    try:
        customer = User.objects.get(pk=customer_id)
    except User.DoesNotExist:
        return api_error("Client introuvable.", status=404)

    order = Order.objects.create(
        customer=customer,
        notes=payload.get("notes", ""),
        status=status,
    )

    for line in lines:
        OrderLine.objects.create(
            order=order,
            product=line["product"],
            product_name=line["product"].name,
            sku_snapshot=line["product"].sku,
            quantity=line["quantity"],
            unit_price=line["unit_price"],
        )

    order = Order.objects.select_related("customer").prefetch_related("lines").get(pk=order.pk)
    return JsonResponse(serialize_order(order), status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def order_detail(request, order_id):
    auth_response = require_api_client(
        request,
        scopes=["orders:read"] if request.method == "GET" else ["orders:write"],
    )
    if auth_response is not None:
        return auth_response

    order = get_order(order_id)
    if order is None:
        return api_error("Commande introuvable.", status=404)

    if request.method == "GET":
        return JsonResponse(serialize_order(order))

    try:
        payload = parse_request_payload(request)
    except ValueError as exc:
        return api_error(str(exc), status=400)
    except TypeError as exc:
        return api_error(str(exc), status=415)

    fields_to_update = []

    status = payload.get("status")
    if status is not None:
        if status not in OrderStatus.values:
            return api_error("Le statut de commande est invalide.", status=400)
        order.status = status
        fields_to_update.append("status")

    notes = payload.get("notes")
    if notes is not None:
        order.notes = notes
        fields_to_update.append("notes")

    if not fields_to_update:
        return api_error("Aucune modification a appliquer.", status=400)

    fields_to_update.append("updated_at")
    order.save(update_fields=fields_to_update)
    order = get_order(order.id)
    return JsonResponse(serialize_order(order))
