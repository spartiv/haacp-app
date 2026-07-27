import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChecklistItem, Product
from app.services import auth_service, batch_service, product_service


async def _signup_owner(db_session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    result = await auth_service.signup(
        db_session,
        email=f"owner-{uuid.uuid4().hex}@polton.ua",
        password="supersecret123",
        full_name="Olena Polishchuk",
        organization_name="Polton",
    )
    assert result.organization_id is not None
    return result.organization_id, result.user.id


async def _make_product_with_checklist(
    db_session: AsyncSession, org_id: uuid.UUID, labels: list[str]
) -> tuple[Product, list[ChecklistItem]]:
    product = await product_service.create_product(
        db_session, organization_id=org_id, name="Cheese"
    )
    items = [
        await product_service.add_checklist_item(
            db_session, organization_id=org_id, product_id=product.id, label=label
        )
        for label in labels
    ]
    return product, items


async def test_record_batch_with_all_yes_has_no_deviation(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1", "Q2"])

    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="B-001",
        name=None,
        production_date=date(2026, 7, 20),
        answers={items[0].id: True, items[1].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )

    assert batch.has_deviation is False


async def test_record_batch_with_a_no_answer_flags_deviation(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1", "Q2"])

    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="B-002",
        name=None,
        production_date=date(2026, 7, 20),
        answers={items[0].id: True, items[1].id: False},
        deviation_note="Mold found",
        corrective_action="Discarded batch",
        signatory_user_id=user_id,
    )

    assert batch.has_deviation is True
    answers = await batch_service.list_batch_answers(db_session, batch_id=batch.id)
    assert {a.checklist_item_id: a.answer for a in answers} == {
        items[0].id: True,
        items[1].id: False,
    }


async def test_record_batch_rejects_missing_answer(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1", "Q2"])

    with pytest.raises(batch_service.ChecklistMismatchError):
        await batch_service.record_batch(
            db_session,
            organization_id=org_id,
            product_id=product.id,
            number="B-003",
            name=None,
            production_date=date(2026, 7, 20),
            answers={items[0].id: True},
            deviation_note=None,
            corrective_action=None,
            signatory_user_id=user_id,
        )


async def test_record_batch_rejects_answer_for_foreign_checklist_item(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1"])

    with pytest.raises(batch_service.ChecklistMismatchError):
        await batch_service.record_batch(
            db_session,
            organization_id=org_id,
            product_id=product.id,
            number="B-004",
            name=None,
            production_date=date(2026, 7, 20),
            answers={items[0].id: True, uuid.uuid4(): True},
            deviation_note=None,
            corrective_action=None,
            signatory_user_id=user_id,
        )


async def test_list_batches_orders_newest_first_and_excludes_deleted(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1"])
    older = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="OLD",
        name=None,
        production_date=date(2026, 7, 1),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )
    newer = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="NEW",
        name=None,
        production_date=date(2026, 7, 20),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )
    removed = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="REMOVED",
        name=None,
        production_date=date(2026, 7, 25),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )
    await batch_service.soft_delete_batch(db_session, organization_id=org_id, batch_id=removed.id)

    batches = await batch_service.list_batches(
        db_session, organization_id=org_id, product_id=product.id
    )

    assert [b.id for b in batches] == [newer.id, older.id]


async def test_edit_batch_snapshots_previous_state_to_history(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1"])
    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="B-005",
        name="Original name",
        production_date=date(2026, 7, 20),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )

    edited = await batch_service.edit_batch(
        db_session,
        organization_id=org_id,
        batch_id=batch.id,
        edited_by_user_id=user_id,
        number="B-005-CORRECTED",
    )

    assert edited.number == "B-005-CORRECTED"
    history = await batch_service.get_batch_history(
        db_session, organization_id=org_id, batch_id=batch.id
    )
    assert len(history) == 1
    assert history[0].snapshot["number"] == "B-005"
    assert history[0].snapshot["name"] == "Original name"
    assert history[0].edited_by_user_id == user_id


async def test_edit_batch_partial_update_leaves_other_fields_untouched(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1"])
    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="B-006",
        name="Keep me",
        production_date=date(2026, 7, 20),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )

    edited = await batch_service.edit_batch(
        db_session,
        organization_id=org_id,
        batch_id=batch.id,
        edited_by_user_id=user_id,
        deviation_note="Now noted",
    )

    assert edited.name == "Keep me"
    assert edited.number == "B-006"
    assert edited.deviation_note == "Now noted"


async def test_edit_batch_updates_name_date_and_corrective_action(
    db_session: AsyncSession,
) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1"])
    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="B-011",
        name="Old name",
        production_date=date(2026, 7, 20),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )

    edited = await batch_service.edit_batch(
        db_session,
        organization_id=org_id,
        batch_id=batch.id,
        edited_by_user_id=user_id,
        name="New name",
        production_date=date(2026, 7, 22),
        corrective_action="Retrained staff",
    )

    assert edited.name == "New name"
    assert edited.production_date == date(2026, 7, 22)
    assert edited.corrective_action == "Retrained staff"


async def test_edit_batch_answers_recomputes_deviation(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1"])
    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="B-007",
        name=None,
        production_date=date(2026, 7, 20),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )
    assert batch.has_deviation is False

    edited = await batch_service.edit_batch(
        db_session,
        organization_id=org_id,
        batch_id=batch.id,
        edited_by_user_id=user_id,
        answers={items[0].id: False},
    )

    assert edited.has_deviation is True
    answers = await batch_service.list_batch_answers(db_session, batch_id=batch.id)
    assert len(answers) == 1
    assert answers[0].answer is False


async def test_edit_batch_rejects_mismatched_answers(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1", "Q2"])
    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="B-008",
        name=None,
        production_date=date(2026, 7, 20),
        answers={items[0].id: True, items[1].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )

    with pytest.raises(batch_service.ChecklistMismatchError):
        await batch_service.edit_batch(
            db_session,
            organization_id=org_id,
            batch_id=batch.id,
            edited_by_user_id=user_id,
            answers={items[0].id: True},
        )


async def test_get_batch_not_found_for_wrong_org(db_session: AsyncSession) -> None:
    org_a, user_id = await _signup_owner(db_session)
    org_b, _ = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_a, ["Q1"])
    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_a,
        product_id=product.id,
        number="B-009",
        name=None,
        production_date=date(2026, 7, 20),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )

    with pytest.raises(batch_service.BatchNotFoundError):
        await batch_service.get_batch(db_session, organization_id=org_b, batch_id=batch.id)


async def test_soft_delete_batch_then_get_raises_not_found(db_session: AsyncSession) -> None:
    org_id, user_id = await _signup_owner(db_session)
    product, items = await _make_product_with_checklist(db_session, org_id, ["Q1"])
    batch = await batch_service.record_batch(
        db_session,
        organization_id=org_id,
        product_id=product.id,
        number="B-010",
        name=None,
        production_date=date(2026, 7, 20),
        answers={items[0].id: True},
        deviation_note=None,
        corrective_action=None,
        signatory_user_id=user_id,
    )

    await batch_service.soft_delete_batch(db_session, organization_id=org_id, batch_id=batch.id)

    with pytest.raises(batch_service.BatchNotFoundError):
        await batch_service.get_batch(db_session, organization_id=org_id, batch_id=batch.id)
