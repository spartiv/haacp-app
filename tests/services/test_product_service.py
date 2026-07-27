import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import auth_service, product_service


async def _signup_owner(db_session: AsyncSession, **overrides: str) -> uuid.UUID:
    defaults = {
        "email": f"owner-{uuid.uuid4().hex}@polton.ua",
        "password": "supersecret123",
        "full_name": "Olena Polishchuk",
        "organization_name": "Polton",
    }
    defaults.update(overrides)
    result = await auth_service.signup(db_session, **defaults)  # type: ignore[arg-type]
    assert result.organization_id is not None
    return result.organization_id


async def test_create_and_get_product(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)

    product = await product_service.create_product(
        db_session, organization_id=org_id, name="Масло вершкове 82%"
    )

    fetched = await product_service.get_product(
        db_session, organization_id=org_id, product_id=product.id
    )
    assert fetched.name == "Масло вершкове 82%"


async def test_get_product_not_found_in_other_org(db_session: AsyncSession) -> None:
    org_a = await _signup_owner(db_session)
    org_b = await _signup_owner(db_session)
    product = await product_service.create_product(
        db_session, organization_id=org_a, name="Product A"
    )

    with pytest.raises(product_service.ProductNotFoundError):
        await product_service.get_product(db_session, organization_id=org_b, product_id=product.id)


async def test_list_products_excludes_soft_deleted(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    keep = await product_service.create_product(db_session, organization_id=org_id, name="Keep")
    remove = await product_service.create_product(db_session, organization_id=org_id, name="Remove")
    await product_service.soft_delete_product(
        db_session, organization_id=org_id, product_id=remove.id
    )

    products = await product_service.list_products(db_session, organization_id=org_id)

    assert [p.id for p in products] == [keep.id]


async def test_soft_delete_product_then_get_raises_not_found(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    product = await product_service.create_product(db_session, organization_id=org_id, name="X")

    await product_service.soft_delete_product(
        db_session, organization_id=org_id, product_id=product.id
    )

    with pytest.raises(product_service.ProductNotFoundError):
        await product_service.get_product(db_session, organization_id=org_id, product_id=product.id)


async def test_add_checklist_items_increments_position(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    product = await product_service.create_product(db_session, organization_id=org_id, name="X")

    first = await product_service.add_checklist_item(
        db_session, organization_id=org_id, product_id=product.id, label="Question 1"
    )
    second = await product_service.add_checklist_item(
        db_session, organization_id=org_id, product_id=product.id, label="Question 2"
    )

    assert first.position == 0
    assert second.position == 1


async def test_list_checklist_items_orders_by_position_and_excludes_removed(
    db_session: AsyncSession,
) -> None:
    org_id = await _signup_owner(db_session)
    product = await product_service.create_product(db_session, organization_id=org_id, name="X")
    first = await product_service.add_checklist_item(
        db_session, organization_id=org_id, product_id=product.id, label="First"
    )
    second = await product_service.add_checklist_item(
        db_session, organization_id=org_id, product_id=product.id, label="Second"
    )
    await product_service.remove_checklist_item(
        db_session, organization_id=org_id, product_id=product.id, item_id=first.id
    )

    items = await product_service.list_checklist_items(
        db_session, organization_id=org_id, product_id=product.id
    )

    assert [i.id for i in items] == [second.id]


async def test_update_checklist_item_label(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    product = await product_service.create_product(db_session, organization_id=org_id, name="X")
    item = await product_service.add_checklist_item(
        db_session, organization_id=org_id, product_id=product.id, label="Old label"
    )

    updated = await product_service.update_checklist_item(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        item_id=item.id,
        label="New label",
    )

    assert updated.label == "New label"


async def test_update_unknown_checklist_item_raises(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    product = await product_service.create_product(db_session, organization_id=org_id, name="X")

    with pytest.raises(product_service.ChecklistItemNotFoundError):
        await product_service.update_checklist_item(
            db_session,
            organization_id=org_id,
            product_id=product.id,
            item_id=uuid.uuid4(),
            label="New label",
        )
