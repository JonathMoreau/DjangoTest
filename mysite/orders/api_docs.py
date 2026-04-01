from api_docs.registry import register_domain

register_domain(
    slug="orders",
    title="Commandes",
    description="Commandes clients, lignes de commande et endpoints API securises pour les integrations.",
    spec_url_name="orders:api-openapi",
)
