import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import allergen_service, auth_service


async def _signup_owner(db_session: AsyncSession) -> uuid.UUID:
    result = await auth_service.signup(
        db_session,
        email=f"owner-{uuid.uuid4().hex}@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    assert result.organization_id is not None
    return result.organization_id


async def test_signup_auto_seeds_all_14_legal_allergens(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)

    rows = await allergen_service.list_allergen_statuses(db_session, organization_id=org_id)

    assert len(rows) == 14
    assert all(status.present is False for _, status in rows)
    positions = [allergen.position for allergen, _ in rows]
    assert positions == sorted(positions)


async def test_set_allergen_presence_toggles_the_flag(db_session: AsyncSession) -> None:
    org_id = await _signup_owner(db_session)
    rows = await allergen_service.list_allergen_statuses(db_session, organization_id=org_id)
    milk_allergen_id = rows[6][0].id  # 'Молоко' per the seeded order

    allergen, status = await allergen_service.set_allergen_presence(
        db_session, organization_id=org_id, allergen_id=milk_allergen_id, present=True
    )

    assert allergen.name == "Молоко"
    assert status.present is True

    refreshed = await allergen_service.list_allergen_statuses(db_session, organization_id=org_id)
    milk_row = next(s for a, s in refreshed if a.id == milk_allergen_id)
    assert milk_row.present is True


async def test_set_allergen_presence_not_found_for_unknown_allergen(
    db_session: AsyncSession,
) -> None:
    org_id = await _signup_owner(db_session)

    with pytest.raises(allergen_service.AllergenStatusNotFoundError):
        await allergen_service.set_allergen_presence(
            db_session, organization_id=org_id, allergen_id=uuid.uuid4(), present=True
        )


async def test_allergen_presence_is_independent_per_organization(db_session: AsyncSession) -> None:
    # Allergen rows are global (shared across orgs), but each org's
    # presence toggle for that same allergen must stay independent.
    org_a = await _signup_owner(db_session)
    org_b = await _signup_owner(db_session)
    rows = await allergen_service.list_allergen_statuses(db_session, organization_id=org_a)
    allergen_id = rows[0][0].id

    await allergen_service.set_allergen_presence(
        db_session, organization_id=org_a, allergen_id=allergen_id, present=True
    )

    org_a_rows = await allergen_service.list_allergen_statuses(db_session, organization_id=org_a)
    org_b_rows = await allergen_service.list_allergen_statuses(db_session, organization_id=org_b)
    assert next(s.present for a, s in org_a_rows if a.id == allergen_id) is True
    assert next(s.present for a, s in org_b_rows if a.id == allergen_id) is False
