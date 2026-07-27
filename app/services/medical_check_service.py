import logging
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import MedicalCheck

logger = logging.getLogger(__name__)


class MedicalCheckNotFoundError(NotFoundError):
    code = "medical_check_not_found"
    message = "Medical check not found"


async def create_medical_check(
    db: AsyncSession, *, organization_id: uuid.UUID, employee_name: str, next_check_date: date
) -> MedicalCheck:
    medical_check = MedicalCheck(
        organization_id=organization_id,
        employee_name=employee_name,
        next_check_date=next_check_date,
    )
    db.add(medical_check)
    await db.commit()
    logger.info(
        "Medical check created: medical_check_id=%s organization_id=%s",
        medical_check.id,
        organization_id,
    )
    return medical_check


async def list_medical_checks(
    db: AsyncSession, *, organization_id: uuid.UUID
) -> list[MedicalCheck]:
    result = await db.execute(
        select(MedicalCheck)
        .where(MedicalCheck.organization_id == organization_id, MedicalCheck.deleted_at.is_(None))
        .order_by(MedicalCheck.next_check_date)
    )
    return list(result.scalars().all())


async def get_medical_check(
    db: AsyncSession, *, organization_id: uuid.UUID, medical_check_id: uuid.UUID
) -> MedicalCheck:
    result = await db.execute(
        select(MedicalCheck).where(
            MedicalCheck.id == medical_check_id,
            MedicalCheck.organization_id == organization_id,
            MedicalCheck.deleted_at.is_(None),
        )
    )
    medical_check = result.scalar_one_or_none()
    if medical_check is None:
        raise MedicalCheckNotFoundError
    return medical_check


async def update_medical_check(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    medical_check_id: uuid.UUID,
    employee_name: str | None = None,
    next_check_date: date | None = None,
) -> MedicalCheck:
    medical_check = await get_medical_check(
        db, organization_id=organization_id, medical_check_id=medical_check_id
    )
    if employee_name is not None:
        medical_check.employee_name = employee_name
    if next_check_date is not None:
        medical_check.next_check_date = next_check_date
    await db.commit()
    return medical_check


async def soft_delete_medical_check(
    db: AsyncSession, *, organization_id: uuid.UUID, medical_check_id: uuid.UUID
) -> None:
    medical_check = await get_medical_check(
        db, organization_id=organization_id, medical_check_id=medical_check_id
    )
    medical_check.deleted_at = datetime.now(UTC)
    await db.commit()
    logger.info(
        "Medical check deleted: medical_check_id=%s organization_id=%s",
        medical_check_id,
        organization_id,
    )
