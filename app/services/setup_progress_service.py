"""HACCP implementation progress: which onboarding steps an organization has
completed, derived on the fly from data that already exists (no stored flags,
so the result can never drift from reality)."""

import uuid
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Chemical,
    ControlChecklistItem,
    ControlPeriod,
    ControlRecord,
    ControlRecordStatus,
    Equipment,
    MedicalCheck,
    Membership,
    MembershipStatus,
    Product,
)


class SetupStepKey(StrEnum):
    DAILY_CHECKLIST = "daily_checklist"
    MONTHLY_CHECKLIST = "monthly_checklist"
    EQUIPMENT = "equipment"
    CHEMICALS = "chemicals"
    MEDICAL_CHECKS = "medical_checks"
    PRODUCTS = "products"
    TEAM = "team"
    FIRST_DAILY_SUBMITTED = "first_daily_submitted"


# Order = the recommended order of doing the setup.
_STEP_LABELS: dict[SetupStepKey, str] = {
    SetupStepKey.DAILY_CHECKLIST: "Налаштовано щоденний чек-лист",
    SetupStepKey.MONTHLY_CHECKLIST: "Налаштовано місячний чек-лист",
    SetupStepKey.EQUIPMENT: "Додано обладнання",
    SetupStepKey.CHEMICALS: "Додано мийні та дезінфікуючі засоби",
    SetupStepKey.MEDICAL_CHECKS: "Внесено медичні книжки працівників",
    SetupStepKey.PRODUCTS: "Додано продукцію",
    SetupStepKey.TEAM: "Запрошено хоча б одного колегу",
    SetupStepKey.FIRST_DAILY_SUBMITTED: "Подано перший щоденний аркуш",
}

# The team step needs the owner plus at least one more active member.
_TEAM_MIN_MEMBERS = 2


@dataclass(frozen=True)
class SetupStep:
    key: SetupStepKey
    label: str
    done: bool
    count: int


@dataclass(frozen=True)
class SetupProgress:
    completed: int
    total: int
    steps: list[SetupStep]


def _count(*where: ColumnElement[bool], entity: type) -> ColumnElement[int]:
    return select(func.count()).select_from(entity).where(*where).scalar_subquery()


async def get_setup_progress(db: AsyncSession, *, organization_id: uuid.UUID) -> SetupProgress:
    def checklist(period: ControlPeriod) -> ColumnElement[int]:
        return _count(
            ControlChecklistItem.organization_id == organization_id,
            ControlChecklistItem.period == period,
            ControlChecklistItem.deleted_at.is_(None),
            entity=ControlChecklistItem,
        )

    # One round trip: every count is a scalar subquery.
    row = (
        await db.execute(
            select(
                checklist(ControlPeriod.DAILY),
                checklist(ControlPeriod.MONTHLY),
                _count(
                    Equipment.organization_id == organization_id,
                    Equipment.deleted_at.is_(None),
                    entity=Equipment,
                ),
                _count(
                    Chemical.organization_id == organization_id,
                    Chemical.deleted_at.is_(None),
                    entity=Chemical,
                ),
                _count(
                    MedicalCheck.organization_id == organization_id,
                    MedicalCheck.deleted_at.is_(None),
                    entity=MedicalCheck,
                ),
                _count(
                    Product.organization_id == organization_id,
                    Product.deleted_at.is_(None),
                    entity=Product,
                ),
                _count(
                    Membership.organization_id == organization_id,
                    Membership.status == MembershipStatus.ACTIVE,
                    entity=Membership,
                ),
                _count(
                    ControlRecord.organization_id == organization_id,
                    ControlRecord.period == ControlPeriod.DAILY,
                    ControlRecord.status == ControlRecordStatus.SUBMITTED,
                    ControlRecord.deleted_at.is_(None),
                    entity=ControlRecord,
                ),
            )
        )
    ).one()
    counts: dict[SetupStepKey, int] = dict(zip(_STEP_LABELS, row, strict=True))

    steps = [
        SetupStep(
            key=key,
            label=label,
            done=counts[key] >= (_TEAM_MIN_MEMBERS if key is SetupStepKey.TEAM else 1),
            count=counts[key],
        )
        for key, label in _STEP_LABELS.items()
    ]
    return SetupProgress(completed=sum(step.done for step in steps), total=len(steps), steps=steps)
