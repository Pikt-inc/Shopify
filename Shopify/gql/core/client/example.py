from .wrapper import ShopifyClientWrapper

def test():
    domain = 'quickstart-5dd1aca4.myshopify.com'
    at = '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'

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