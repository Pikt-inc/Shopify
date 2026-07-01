from __future__ import annotations

from shopify_sdk import client, client_context


def run_with_env_fallback() -> None:
    """Use SHOPIFY_* env vars loaded by the SDK."""
    query = """
    query GetShopName {
        shop {
            name
        }
    }
    """
    response = client.request(query=query, variables={})
    print(response.data)


def run_with_context_override() -> None:
    """Override shop domain and token within a context."""
    query = """
    query GetShopName {
        shop {
            name
        }
    }
    """
    with client_context(
        shop_domain="your-shop.myshopify.com",
        access_token="replace-with-shopify-admin-access-token",
    ):
        response = client.request(query=query, variables={})
        print(response.data)


if __name__ == "__main__":
    # Uncomment one of the following lines to run.
    run_with_env_fallback()
    run_with_context_override()
    pass
