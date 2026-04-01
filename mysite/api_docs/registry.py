from dataclasses import dataclass

from django.urls import reverse

_REGISTERED_DOMAINS = {}


@dataclass(frozen=True)
class DomainApiDoc:
    slug: str
    title: str
    description: str
    spec_url_name: str

    @property
    def spec_url(self):
        return reverse(self.spec_url_name)

    @property
    def docs_url(self):
        return reverse("api_docs:domain-docs", args=[self.slug])


def register_domain(*, slug, title, description, spec_url_name):
    _REGISTERED_DOMAINS[slug] = DomainApiDoc(
        slug=slug,
        title=title,
        description=description,
        spec_url_name=spec_url_name,
    )


def get_registered_domains():
    return [
        _REGISTERED_DOMAINS[slug]
        for slug in sorted(_REGISTERED_DOMAINS, key=lambda key: _REGISTERED_DOMAINS[key].title)
    ]


def get_registered_domain(slug):
    return _REGISTERED_DOMAINS.get(slug)
