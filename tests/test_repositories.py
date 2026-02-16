import pytest
from app.repositories.product import ProductRepository


@pytest.mark.asyncio
async def test_create_and_get_product(db_session):
    # Prepare data
    repo = ProductRepository(db_session)
    product_data = {
        "name": "Test Widget",
        "sku": "TEST-SKU-001",
        "price": 100.00,
        "stock_quantity": 10,
    }

    # Run code
    new_product = await repo.create(product_data)

    # Assert results
    assert new_product.id is not None
    assert new_product.name == "Test Widget"
    assert new_product.sku == "TEST-SKU-001"

    # Verify Custom Method
    fetched_product = await repo.get_by_sku("TEST-SKU-001")
    assert fetched_product is not None
    assert fetched_product.id == new_product.id
