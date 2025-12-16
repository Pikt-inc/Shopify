from shopify_sdk.common import update_product, ProxyProduct
from shopify_sdk.common import (
    archive_product_by_sku,
    ProductActionResponse
)
from shopify_sdk.common import set_order_line_item_tracking
from shopify_sdk.common import get_orders_from_last_n_days
from shopify_sdk.gql.core.types import Order


pp = ProxyProduct(
    sku='skookey-19999',
    title='GOOBER Plush Toy',
    description_html='<p>Created via update_or_create_product script.</p>',
    vendor='Demo Vendor',
    type='Demo Type',
    tags=['demo', 'script'],
    price='39.99',
    quantity=2,
    seo_description='A cuddly GOOBER plush toy for all ages.',
    seo_title='GOOBER Plush Toy - Cuddly and Fun'
)
pp.save()
res = archive_product_by_sku('skookey-19999')
print(res)
order = get_orders_from_last_n_days(15)
print(order)