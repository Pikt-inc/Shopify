from typing import Sequence

from shopify_sdk import client
from shopify_sdk.gql import productUnpublish, productVariants
from shopify_sdk.gql.core.types import ProductPublicationInput, ProductUnpublishInput
from .types import ProductActionResponse


def _lookup_product_publications_by_sku(
    sku: str,
    publication_page_size: int,
) -> tuple[str, list[str], str | None]:
    """Return (product_id, publication_ids, product_title) for the first variant matching sku."""
    search_query = f"sku:{sku}"
    variant_connection = productVariants(
        first=1,
        query=search_query,
        field_inclusions={
            "ProductVariant": {"sku", "product"},
            "Product": {"id", "title", "resourcePublications"},
            "ResourcePublication": {"publication"},
            "Publication": {"id", "name"},
        },
        field_exclusions={
            "ResourcePublicationConnection": {"edges"},
        },
        connection_arguments={
            "resourcePublications": {"first": publication_page_size},
        },
    ).execute(client=client)

    if not variant_connection or not getattr(variant_connection, "nodes", None):
        raise ValueError(f"No product variant found for SKU '{sku}'.")

    variant = variant_connection.nodes[0]
    product = getattr(variant, "product", None)
    if not product or not getattr(product, "id", None):
        raise ValueError(f"Product lookup for SKU '{sku}' returned no product id.")

    product_id = product.id

    publication_ids: list[str] = []
    resource_pubs = getattr(product, "resourcePublications", None)
    nodes = getattr(resource_pubs, "nodes", None) if resource_pubs else []
    for node in nodes or []:
        publication = getattr(node, "publication", None)
        pub_id = getattr(publication, "id", None)
        if pub_id:
            publication_ids.append(pub_id)

    return product_id, publication_ids, getattr(product, "title", None)


def unpublish_product_by_sku(
    sku: str,
    *,
    publication_ids: Sequence[str] | None = None,
    publication_page_size: int = 20,
) -> ProductActionResponse:
    """
    Unpublish a product by SKU using Shopify's productUnpublish mutation.

    If publication_ids is omitted, the helper unpublishes the product from every
    publication currently attached to it (fetched via resourcePublications).
    Shopify docs: https://shopify.dev/docs/api/admin-graphql/2026-07/mutations/productUnpublish
    """
    success = False
    message: str | None = None
    try:
        if publication_page_size < 1:
            raise ValueError("publication_page_size must be at least 1.")

        product_id, existing_publications, product_title = (
            _lookup_product_publications_by_sku(
                sku=sku,
                publication_page_size=publication_page_size,
            )
        )
        target_publications = (
            list(publication_ids)
            if publication_ids is not None
            else existing_publications
        )

        if not target_publications:
            label = product_title or product_id
            raise ValueError(
                f"No publications found for product '{label}' tied to SKU '{sku}'."
            )

        unpublish_input = ProductUnpublishInput(
            id=product_id,
            productPublications=[
                ProductPublicationInput(publicationId=pub_id)
                for pub_id in target_publications
            ],
        )
        result = productUnpublish(input=unpublish_input).execute(client=client)
        success = bool(result and getattr(result, "product", None))
        if not success:
            label = product_title or product_id
            message = f"Failed to unpublish product '{label}' for SKU '{sku}'."
    except Exception as e:
        success = False
        message = str(e)
    return ProductActionResponse(
        action="unpublish",
        success=success,
        message=message,
        sku=sku,
    )
