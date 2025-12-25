def test():
    domain = 'your-shop.myshopify.com'
    at = 'shpat_your_token_here'

    query = '''
    query GetProductByHandle($handle: String!) {
        productByHandle(handle: $handle) {
            id
        }
    }
    '''
    from . import client_context, client

    with client_context(shop_domain=domain, access_token=at):
        response = client.request(query=query, variables={"handle": "157056959955"})
    return response
