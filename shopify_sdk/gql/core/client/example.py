def test():
    domain = "your-shop.myshopify.com"
    at = "replace-with-shopify-admin-access-token"
    api_version = "2025-10"

    query = """
    query GetProductByHandle($handle: String!) {
        productByHandle(handle: $handle) {
            id
        }
    }
    """
    from . import client_context, client

    with client_context(shop_domain=domain, access_token=at, api_version=api_version):
        response = client.request(query=query, variables={"handle": "157056959955"})
    return response
