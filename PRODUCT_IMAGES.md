# Product Images Support

## Overview

This implementation adds support for setting product images through the `ProxyProduct` interface in the Shopify SDK.

## Features

- **Optional Field**: The `images` field is optional, maintaining backward compatibility
- **Multiple Images**: Support for multiple image URLs per product
- **Automatic Handling**: Images are set automatically during product creation and updates
- **GraphQL Compliant**: Uses Shopify's `productCreateMedia` mutation following strictly typed GraphQL shapes
- **Hydration Support**: Images are loaded when fetching products from Shopify

## Usage

### Creating a Product with Images

```python
from shopify_sdk.common import ProxyProduct

# Create a product with images
product = ProxyProduct(
    sku='product-001',
    title='My Product',
    description_html='<p>Product description</p>',
    vendor='My Vendor',
    type='Product Type',
    tags=['new', 'featured'],
    price='29.99',
    quantity=10,
    images=[
        'https://cdn.example.com/product-image-1.jpg',
        'https://cdn.example.com/product-image-2.jpg',
        'https://cdn.example.com/product-image-3.jpg'
    ]
)

# Save the product
product_id = product.save()
```

### Updating a Product with Images

```python
from shopify_sdk.common import ProxyProduct

# Get existing product
product = ProxyProduct.get('existing-sku')

# Update images
product.images = [
    'https://cdn.example.com/new-image-1.jpg',
    'https://cdn.example.com/new-image-2.jpg'
]

# Save changes
product.update_or_create()
```

### Creating a Product without Images (Backward Compatible)

```python
from shopify_sdk.common import ProxyProduct

# Works exactly as before - no images field needed
product = ProxyProduct(
    sku='product-002',
    title='Product without Images',
    price='19.99',
    quantity=5
)

product_id = product.save()
```

## Implementation Details

### Architecture

1. **ProxyProduct** (`shopify_sdk/common/types.py`)
   - Added `images: Optional[list[str]]` field
   - Updated `hydrate()` method to load images from Product media

2. **GraphQL Types** (`shopify_sdk/gql/core/types/input_objects.py`)
   - Added `CreateMediaInput` with fields: `alt`, `mediaContentType`, `originalSource`
   - Added `ProductCreateMediaInput` for the mutation input

3. **Mutation** (`shopify_sdk/gql/mutations.py`)
   - Added `productCreateMedia` mutation class

4. **Media Module** (`shopify_sdk/common/product/media.py`)
   - `create_product_media()`: Core function to create media via GraphQL
   - `set_product_images()`: Helper function used by ProductCreate and ProductUpdate

5. **Product Flows** (`shopify_sdk/common/actions.py`)
   - ProductCreate: Calls `_set_images()` after creating product
   - ProductUpdate: Calls `_set_images()` after updating product

### Image URL Requirements

- Images must be publicly accessible URLs
- Supported formats: JPG, PNG, GIF, WebP (standard image formats supported by Shopify)
- HTTPS is recommended for security
- URLs must be valid and point to actual image files

### Error Handling

The implementation includes proper error handling:
- Invalid URLs will raise a `ValueError`
- Failed media creation will raise a `ValueError` with details
- Network errors are propagated from the GraphQL client

## Technical Notes

- The `productCreateMedia` mutation is called after product creation/update
- Media is associated with the product using the product ID
- Alt text is set to `None` by default (can be extended in future versions)
- Image order is preserved based on the list order

## Future Enhancements

Potential improvements for future versions:
1. Support for custom alt text per image
2. Image reordering capability
3. Selective image deletion
4. Image metadata (dimensions, file size, etc.)
5. Validation of image URLs before upload
