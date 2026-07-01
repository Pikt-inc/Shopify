from .wrapper import ShopifyClientWrapper

def test():
    domain = 'quickstart-5dd1aca4.myshopify.com'
    at = 'replace-with-shopify-admin-access-token'

    query = '''
    query GetProductByHandle($handle: String!) {
        productByHandle(handle: $handle) {
            id
        }
    }
    '''
    scw = ShopifyClientWrapper(shop_domain=domain, access_token=at)
    client = scw.client
    response = client.request(query=query, variables={"handle": "157056959955"})
    return response