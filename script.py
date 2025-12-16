from shopify_sdk.common import ProxyProduct


pp = ProxyProduct(
    sku='999000111',
    title='GOOBER Plush Toy',
    description_html='<p>Created via update_or_create_product script.</p>',
    vendor='Demo Vendor',
    type='Demo Type',
    tags=['demo', 'script'],
    price='39.99',
    quantity=1,
    seo_description='A cuddly GOOBER plush toy for all ages.',
    seo_title='GOOBER Plush Toy - Cuddly and Fun',
    images=[
        'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/640px-PNG_transparency_demonstration_1.png'
    ]
)
pp.update_or_create()
