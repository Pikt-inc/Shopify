def test_public_top_level_imports_remain_available() -> None:
    import shopify_sdk
    import shopify_sdk.common
    import shopify_sdk.gql
    from shopify_sdk import client, client_context, store
    from shopify_sdk.common import ProxyProduct, create_product
    from shopify_sdk.common.resolver import ProductIdSkuResolver
    from shopify_sdk.managers.map import MapManager
    from shopify_sdk.webhooks import WebhookDeliveryParser
    from shopify_sdk.webhooks import WebhookSubscriptionCreateRequest

    assert shopify_sdk.store is store
    assert callable(client_context)
    assert client is not None
    assert ProxyProduct.__name__ == "ProxyProduct"
    assert callable(create_product)
    assert ProductIdSkuResolver.__name__ == "ProductIdSkuResolver"
    assert MapManager.__name__ == "MapManager"
    assert hasattr(shopify_sdk.gql, "products")
    assert WebhookDeliveryParser.__name__ == "WebhookDeliveryParser"
    assert WebhookSubscriptionCreateRequest.__name__ == "WebhookSubscriptionCreateRequest"
    assert hasattr(store, "webhooks")


def test_public_common_resolver_module_imports() -> None:
    import shopify_sdk.common.resolver as resolver_module

    assert hasattr(resolver_module, "ProductIdSkuResolver")
