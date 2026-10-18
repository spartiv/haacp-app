import logging
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Batch, BatchAnswer, BatchHistory
from app.services import organization_service
from app.services.checklist_validation import ChecklistMismatchError as ChecklistMismatchError
from app.services.checklist_validation import has_deviation as compute_has_deviation
from app.services.checklist_validation import validate_answer_ids
from app.services.product_service import list_checklist_items

logger = logging.getLogger(__name__)


class BatchNotFoundError(NotFoundError):
    code = "batch_not_found"
    message = "Batch not found"


async def _validate_answers(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    answers: dict[uuid.UUID, bool],
) -> None:
    active_items = await list_checklist_items(
        db, organization_id=organization_id, product_id=product_id
    )
    validate_answer_ids(
        required_ids={item.id for item in active_items},
        answers=answers,
        resource_label="product's",
    )


async def list_batch_answers(db: AsyncSession, *, batch_id: uuid.UUID) -> list[BatchAnswer]:
    result = await db.execute(select(BatchAnswer).where(BatchAnswer.batch_id == batch_id))
    return list(result.scalars().all())


async def list_batch_answers_by_batch_ids(
    db: AsyncSession, *, batch_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[BatchAnswer]]:
    """Single-query counterpart to list_batch_answers for rendering a list
    of batches, so callers don't issue one query per batch."""
    if not batch_ids:
        return {}
    result = await db.execute(select(BatchAnswer).where(BatchAnswer.batch_id.in_(batch_ids)))
    answers_by_batch_id: dict[uuid.UUID, list[BatchAnswer]] = {
        batch_id: [] for batch_id in batch_ids
    }
    for answer in result.scalars().all():
        answers_by_batch_id[answer.batch_id].append(answer)
    return answers_by_batch_id


def _snapshot(batch: Batch, answers: list[BatchAnswer]) -> dict[str, Any]:
    return {
        "number": batch.number,
        "name": batch.name,
        "production_date": batch.production_date.isoformat(),
        "has_deviation": batch.has_deviation,
        "deviation_note": batch.deviation_note,
        "corrective_action": batch.corrective_action,
        "performed_by_user_id": (
            str(batch.performed_by_user_id) if batch.performed_by_user_id else None
        ),
        "answers": [
            {"checklist_item_id": str(a.checklist_item_id), "answer": a.answer} for a in answers
        ],
    }


async def record_batch(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    number: str,
    name: str | None,
    production_date: date,
    answers: dict[uuid.UUID, bool],
    deviation_note: str | None,
    corrective_action: str | None,
    signatory_user_id: uuid.UUID,
    performed_by_user_id: uuid.UUID | None = None,
) -> Batch:
    await _validate_answers(
        db, organization_id=organization_id, product_id=product_id, answers=answers
    )
    performer = await organization_service.resolve_performer(
        db,
        organization_id=organization_id,
        performer_user_id=performed_by_user_id,
        actor_user_id=signatory_user_id,
    )
    has_deviation = compute_has_deviation(answers)

    batch = Batch(
        organization_id=organization_id,
        product_id=product_id,
        number=number,
        name=name,
        production_date=production_date,
        has_deviation=has_deviation,
        deviation_note=deviation_note,
        corrective_action=corrective_action,
        signatory_user_id=signatory_user_id,
        performed_by_user_id=performer,
    )
    db.add(batch)
    await db.flush()

    for checklist_item_id, answer in answers.items():
        db.add(BatchAnswer(batch_id=batch.id, checklist_item_id=checklist_item_id, answer=answer))

    await db.commit()
    logger.info(
        "Batch recorded: batch_id=%s product_id=%s has_deviation=%s",
        batch.id,
        product_id,
        has_deviation,
    )
    return batch


async def list_batches(
    db: AsyncSession, *, organization_id: uuid.UUID, product_id: uuid.UUID | None = None
) -> list[Batch]:
    query = select(Batch).where(
        Batch.organization_id == organization_id, Batch.deleted_at.is_(None)
    )
    if product_id is not None:
        query = query.where(Batch.product_id == product_id)
    result = await db.execute(query.order_by(Batch.production_date.desc()))
    return list(result.scalars().all())


async def count_batches_in_period(
    db: AsyncSession, *, organization_id: uuid.UUID, start: date, end_exclusive: date
) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Batch)
        .where(
            Batch.organization_id == organization_id,
            Batch.deleted_at.is_(None),
            Batch.production_date >= start,
            Batch.production_date < end_exclusive,
        )
    )
    return result.scalar_one()


async def _replace_answers(
    db: AsyncSession,
    *,
    batch: Batch,
    current_answers: list[BatchAnswer],
    answers: dict[uuid.UUID, bool],
) -> None:
    for existing_answer in current_answers:
        await db.delete(existing_answer)
    await db.flush()
    for checklist_item_id, answer in answers.items():
        db.add(BatchAnswer(batch_id=batch.id, checklist_item_id=checklist_item_id, answer=answer))
    batch.has_deviation = compute_has_deviation(answers)


async def get_batch(db: AsyncSession, *, organization_id: uuid.UUID, batch_id: uuid.UUID) -> Batch:
    result = await db.execute(
        select(Batch).where(
            Batch.id == batch_id,
            Batch.organization_id == organization_id,
            Batch.deleted_at.is_(None),
        )
    )
    batch = result.scalar_one_or_none()
    if batch is None:
        raise BatchNotFoundError
    return batch


async def edit_batch(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    batch_id: uuid.UUID,
    edited_by_user_id: uuid.UUID,
    number: str | None = None,
    name: str | None = None,
    production_date: date | None = None,
    answers: dict[uuid.UUID, bool] | None = None,
    deviation_note: str | None = None,
    corrective_action: str | None = None,
) -> Batch:
    batch = await get_batch(db, organization_id=organization_id, batch_id=batch_id)
    current_answers = await list_batch_answers(db, batch_id=batch.id)

    db.add(
        BatchHistory(
            batch_id=batch.id,
            snapshot=_snapshot(batch, current_answers),
            edited_by_user_id=edited_by_user_id,
        )
    )

    if number is not None:
        batch.number = number
    if name is not None:
        batch.name = name
    if production_date is not None:
        batch.production_date = production_date
    if deviation_note is not None:
        batch.deviation_note = deviation_note
    if corrective_action is not None:
        batch.corrective_action = corrective_action

    if answers is not None:
        await _validate_answers(
            db, organization_id=organization_id, product_id=batch.product_id, answers=answers
        )
        await _replace_answers(db, batch=batch, current_answers=current_answers, answers=answers)

    await db.commit()
    logger.info("Batch edited: batch_id=%s edited_by_user_id=%s", batch_id, edited_by_user_id)
    return batch


async def soft_delete_batch(
    db: AsyncSession, *, organization_id: uuid.UUID, batch_id: uuid.UUID
) -> None:
    batch = await get_batch(db, organization_id=organization_id, batch_id=batch_id)
    batch.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info("Batch deleted: batch_id=%s organization_id=%s", batch_id, organization_id)


async def get_batch_history(
    db: AsyncSession, *, organization_id: uuid.UUID, batch_id: uuid.UUID
) -> list[BatchHistory]:
    await get_batch(db, organization_id=organization_id, batch_id=batch_id)
    result = await db.execute(
        select(BatchHistory)
        .where(BatchHistory.batch_id == batch_id)
        .order_by(BatchHistory.created_at.desc())
    )
    return list(result.scalars().all())
