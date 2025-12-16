from shopify_sdk.common import update_product, ProxyProduct

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
product_id = pp.id
print(f"Product created or updated with ID: {product_id}")
