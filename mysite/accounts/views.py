from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import AccountAuthenticationForm, AccountRegistrationForm


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = AccountAuthenticationForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = AccountRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:dashboard")
    else:
        form = AccountRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    links = [
        {
            "title": "Catalogue",
            "description": "Acceder a la vitrine produits cote utilisateur.",
            "url": reverse("products:catalog"),
            "label": "Ouvrir le catalogue",
        },
        {
            "title": "Mes taches",
            "description": "Retrouver votre espace de travail relie a votre session.",
            "url": reverse("task_list"),
            "label": "Ouvrir todo",
        },
        {
            "title": "API docs",
            "description": "Parcourir les specifications OpenAPI par domaine metier.",
            "url": reverse("api_docs:index"),
            "label": "Voir la documentation",
        },
    ]

    if request.user.is_staff:
        links.append(
            {
                "title": "Administration",
                "description": "Acceder au back-office Django pour gerer les donnees.",
                "url": reverse("admin:index"),
                "label": "Ouvrir l'admin",
            }
        )

    return render(
        request,
        "accounts/dashboard.html",
        {"links": links},
    )


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect("products:catalog")
