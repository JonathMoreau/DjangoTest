from django.http import Http404
from django.shortcuts import render

from .registry import get_registered_domain, get_registered_domains


def index(request):
    return render(
        request,
        "api_docs/index.html",
        {"domains": get_registered_domains()},
    )


def domain_docs(request, domain_slug):
    domain = get_registered_domain(domain_slug)
    if domain is None:
        raise Http404("Documentation API introuvable.")

    return render(
        request,
        "api_docs/domain_detail.html",
        {
            "domain": domain,
            "domains": get_registered_domains(),
        },
    )
