# Shopify SDK - Product Metafields Support

## Overview

The Shopify SDK now supports reading and writing metafields for products through the `ProxyProduct` interface. Metafields allow you to store additional custom data for products that isn't part of the standard Shopify product model.

## Features

- ✅ Create products with metafields
- ✅ Update product metafields
- ✅ Read metafields from existing products
- ✅ Support for all metafield types (text, number, boolean, URL, etc.)
- ✅ Type-safe implementation with Pydantic models

## Usage

### Creating a Product with Metafields

```python
from shopify_sdk.common import ProxyProduct
from shopify_sdk.gql.core.types import MetafieldInput

product = ProxyProduct(
    sku='blue-tshirt-001',
    title='Premium Blue T-Shirt',
    description_html='<p>A comfortable cotton t-shirt.</p>',
    vendor='Fashion Co',
    type='Apparel',
    price='29.99',
    quantity=100,
    metafields=[
        MetafieldInput(
            namespace='custom',
            key='material',
            type='single_line_text_field',
            value='100% Cotton'
        ),
        MetafieldInput(
            namespace='custom',
            key='care_instructions',
            type='multi_line_text_field',
            value='Machine wash cold. Tumble dry low.'
        )
    ]
)

# Save the product (creates it in Shopify)
product_id = product.save()
```

### Reading Metafields from an Existing Product

```python
from shopify_sdk.common import ProxyProduct

# Fetch product by SKU - metafields are automatically included
product = ProxyProduct.get(sku='blue-tshirt-001')

# Access metafields
if product.metafields:
    for mf in product.metafields:
        print(f"{mf.namespace}.{mf.key}: {mf.value}")
```

### Updating Product Metafields

```python
from shopify_sdk.common import ProxyProduct
from shopify_sdk.gql.core.types import MetafieldInput

# Get existing product
product = ProxyProduct.get(sku='blue-tshirt-001')

# Initialize metafields list if None
if product.metafields is None:
    product.metafields = []

# Add a new metafield
product.metafields.append(
    MetafieldInput(
        namespace='custom',
        key='size_chart',
        type='url',
        value='https://example.com/size-chart'
    )
)

# Update the product
product_id = product.update_or_create()
```

### Updating Existing Metafield Values

```python
# Update an existing metafield's value
product.metafields = [
    mf if mf.key != 'material' else MetafieldInput(
        id=mf.id,  # Include ID when updating
        namespace=mf.namespace,
        key=mf.key,
        type=mf.type,
        value='100% Organic Cotton'  # New value
    )
    for mf in product.metafields
]

product.update_or_create()
```

## MetafieldInput Structure

The `MetafieldInput` class has the following fields:

- `id` (Optional[str]): The metafield ID. Required when updating, omit when creating new.
- `namespace` (str): The namespace for the metafield (e.g., 'custom', 'inventory').
- `key` (str): The key/name for the metafield.
- `type` (str): The type of the metafield (see supported types below).
- `value` (str): The value of the metafield (as a string).

## Supported Metafield Types

Shopify supports various metafield types:

- `single_line_text_field` - Single line of text
- `multi_line_text_field` - Multiple lines of text
- `number_integer` - Integer number
- `number_decimal` - Decimal number
- `boolean` - True/false value (stored as string "true" or "false")
- `date` - Date value
- `date_time` - Date and time value
- `url` - URL value
- `json` - JSON data
- And many more...

Refer to [Shopify's metafield documentation](https://shopify.dev/docs/api/admin-graphql/latest/enums/MetafieldType) for the complete list.

## Examples

See `examples_metafields.py` for comprehensive examples of:
- Creating products with metafields
- Updating metafields
- Reading metafields
- Using `update_or_create()` with metafields

## API Reference

### ProxyProduct

The `ProxyProduct` class now includes:

```python
class ProxyProduct(BaseModel):
    # ... existing fields ...
    metafields: Optional[list[MetafieldInput]] = Field(default=None)
```

### Methods that Support Metafields

- `ProxyProduct.save()` - Creates a new product with metafields
- `ProxyProduct.update_or_create()` - Creates or updates product with metafields
- `ProxyProduct.get(sku)` - Fetches product including metafields
- `ProxyProduct.hydrate(product)` - Populates ProxyProduct from Product object including metafields

## Notes

- Metafields are optional - you can create/update products without them
- When updating existing metafields, include the `id` field
- When creating new metafields, omit the `id` field
- Metafield values are always strings, even for numbers and booleans
- Use appropriate namespaces to organize your metafields (e.g., 'custom', 'inventory', 'sustainability')

## Testing

Run the example script to see metafields in action:

```bash
python examples_metafields.py
```

Run the test script:

```bash
python /tmp/test_metafields.py
```
