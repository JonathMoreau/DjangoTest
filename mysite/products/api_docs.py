from api_docs.registry import register_domain

register_domain(
    slug="products",
    title="Catalogue produits",
    description="Categories, produits et exposition de la spec OpenAPI du catalogue.",
    spec_url_name="products:api-openapi",
)
