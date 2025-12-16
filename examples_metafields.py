#!/usr/bin/env python
"""Example script demonstrating metafields usage with ProxyProduct

This script shows how to:
1. Create a product with metafields
2. Update a product's metafields
3. Read metafields from an existing product
"""

from shopify_sdk.common import ProxyProduct


# Example 1: Create a new product with metafields
def example_create_with_metafields():
    """Create a new product with custom metafields"""
    
    product = ProxyProduct(
        sku='blue-tshirt-001',
        title='Premium Blue T-Shirt',
        description_html='<p>A comfortable cotton t-shirt in blue.</p>',
        vendor='Fashion Co',
        type='Apparel',
        tags=['clothing', 'tshirt', 'blue'],
        price='29.99',
        quantity=100,
        seo_title='Blue T-Shirt - Comfortable Cotton',
        seo_description='Premium quality blue t-shirt made from 100% cotton'
    )

    product.add_metafield(
        namespace='custom',
        key='material',
        type='single_line_text_field',
        value='100% Cotton'
    )
    product.add_metafield(
        namespace='custom',
        key='care_instructions',
        type='multi_line_text_field',
        value='Machine wash cold. Tumble dry low.'
    )
    product.add_metafield(
        namespace='inventory',
        key='warehouse_location',
        type='single_line_text_field',
        value='Aisle 3, Shelf B'
    )
    
    # This will create the product in Shopify with the metafields
    product_id = product.save()
    print(f"Created product with ID: {product_id}")
    
    return product


# Example 2: Update an existing product's metafields
def example_update_metafields():
    """Update metafields on an existing product"""
    
    # Fetch existing product by SKU
    product = ProxyProduct.get(sku='blue-tshirt-001')
    
    # For demonstration, create a mock product
    product = ProxyProduct(sku='blue-tshirt-001', title='Premium Blue T-Shirt')
    product.add_metafield(
        namespace='custom',
        key='material',
        type='single_line_text_field',
        value='100% Cotton'
    )
    
    # Add new metafield
    product.add_metafield(
        namespace='custom',
        key='size_chart',
        type='url',
        value='https://example.com/size-chart'
    )
    
    # Update existing metafield by replacing the list
    existing_metafields = list(product.metafields or [])
    product.clear_metafields()
    for mf in existing_metafields:
        if mf.key == 'material':
            product.add_metafield(
                namespace=mf.namespace,
                key=mf.key,
                type=mf.type,
                value='100% Organic Cotton',  # Updated value
                id=mf.id,
            )
        else:
            product.add_metafield(
                namespace=mf.namespace,
                key=mf.key,
                type=mf.type,
                value=mf.value,
                id=mf.id,
            )
    
    # This will update the product in Shopify
    product_id = product.update_or_create()
    print(f"Updated product with ID: {product_id}")
    
    return product


# Example 3: Read metafields from an existing product
def example_read_metafields():
    """Fetch and display metafields from an existing product"""
    
    # Fetch product by SKU - this will include metafields
    product = ProxyProduct.get(sku='blue-tshirt-001')
    
    # For demonstration, create a mock product
    # product = ProxyProduct(
    #     sku='blue-tshirt-001',
    #     title='Premium Blue T-Shirt',
    #     metafields=[
    #         MetafieldInput(
    #             id='gid://shopify/Metafield/1',
    #             namespace='custom',
    #             key='material',
    #             type='single_line_text_field',
    #             value='100% Cotton'
    #         ),
    #         MetafieldInput(
    #             id='gid://shopify/Metafield/2',
    #             namespace='custom',
    #             key='care_instructions',
    #             type='multi_line_text_field',
    #             value='Machine wash cold. Tumble dry low.'
    #         )
    #     ]
    # )
    
    if product.metafields:
        print(f"\nMetafields for '{product.title}':")
        for mf in product.metafields:
            print(f"  - {mf.namespace}.{mf.key}: {mf.value}")
    else:
        print(f"\nNo metafields found for '{product.title}'")
    
    return product


# Example 4: Create or update with metafields
def example_update_or_create_with_metafields():
    """Use update_or_create to handle both new and existing products"""
    
    product = ProxyProduct(
        sku='green-tshirt-002',
        title='Eco-Friendly Green T-Shirt',
        description_html='<p>Made from recycled materials.</p>',
        vendor='EcoWear',
        type='Apparel',
        tags=['clothing', 'tshirt', 'green', 'eco-friendly'],
        price='34.99',
        quantity=50
    )

    product.add_metafield(
        namespace='sustainability',
        key='recycled_content',
        type='number_decimal',
        value='95.5'
    )
    product.add_metafield(
        namespace='sustainability',
        key='carbon_neutral',
        type='boolean',
        value='true'
    )
    product.add_metafield(
        namespace='custom',
        key='material',
        type='single_line_text_field',
        value='Recycled Polyester'
    )
    
    # This will create if new, or update if exists (based on SKU)
    product.update_or_create()
    product.hydrate()
    print(product.metafields)
    
    return product


if __name__ == '__main__':
    print("=" * 70)
    print("ProxyProduct Metafields Examples")
    print("=" * 70)
    
    print("\n--- Example 1: Create product with metafields ---")
    p1 = example_create_with_metafields()
    print(f"✓ Product: {p1.title}")
    print(f"  SKU: {p1.sku}")
    print(f"  Metafields: {len(p1.metafields)} custom fields")
    
    print("\n--- Example 2: Update metafields ---")
    p2 = example_update_metafields()
    print(f"✓ Product: {p2.title}")
    print(f"  Updated metafields: {len(p2.metafields)} fields")
    
    print("\n--- Example 3: Read metafields ---")
    p3 = example_read_metafields()
    
    print("\n--- Example 4: Update or create with metafields ---")
    p4 = example_update_or_create_with_metafields()
    print(f"✓ Product: {p4.title}")
    print(f"  SKU: {p4.sku}")
    print(f"  Metafields: {len(p4.metafields)} custom fields")
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print("\nNote: Commented out API calls (save(), update_or_create()) require")
    print("Shopify API credentials. Uncomment them to use with a real store.")
