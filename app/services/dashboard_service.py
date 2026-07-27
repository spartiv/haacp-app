import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ControlPeriod
from app.services import (
    batch_service,
    control_record_service,
    equipment_service,
    medical_check_service,
)
from app.services.organization_service import get_organization_timezone

logger = logging.getLogger(__name__)

MEDICAL_CHECK_WARNING_WINDOW_DAYS = 14


class AttentionSeverity(StrEnum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


_SEVERITY_RANK = {
    AttentionSeverity.CRITICAL: 0,
    AttentionSeverity.WARNING: 1,
    AttentionSeverity.INFO: 2,
}


@dataclass(frozen=True)
class AttentionItem:
    label: str
    severity: AttentionSeverity
    days: int


@dataclass(frozen=True)
class ControlStatus:
    filled: bool
    has_deviation: bool | None


@dataclass(frozen=True)
class Dashboard:
    daily_control: ControlStatus
    monthly_control: ControlStatus
    batches_this_month: int
    attention_items: list[AttentionItem]


def _next_month_start(month_start: date) -> date:
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)
    return date(month_start.year, month_start.month + 1, 1)


async def get_dashboard(db: AsyncSession, *, organization_id: uuid.UUID) -> Dashboard:
    org_timezone = await get_organization_timezone(db, organization_id)
    today = datetime.now(UTC).astimezone(ZoneInfo(org_timezone)).date()
    month_start = today.replace(day=1)

    daily_record = await control_record_service.get_current_control(
        db, organization_id=organization_id, period=ControlPeriod.DAILY
    )
    monthly_record = await control_record_service.get_current_control(
        db, organization_id=organization_id, period=ControlPeriod.MONTHLY
    )
    batches_this_month = await batch_service.count_batches_in_period(
        db,
        organization_id=organization_id,
        start=month_start,
        end_exclusive=_next_month_start(month_start),
    )

    attention_items: list[AttentionItem] = []
    if daily_record is None:
        attention_items.append(
            AttentionItem(
                label="Щоденний контроль на сьогодні не заповнено",
                severity=AttentionSeverity.CRITICAL,
                days=-1,
            )
        )
    if monthly_record is None:
        attention_items.append(
            AttentionItem(
                label="Місячний контроль за поточний місяць не заповнено",
                severity=AttentionSeverity.CRITICAL,
                days=-1,
            )
        )

    equipment_list = await equipment_service.list_equipment(db, organization_id=organization_id)
    for eq in equipment_list:
        if eq.affects_product_safety and eq.attachment_id is None:
            attention_items.append(
                AttentionItem(
                    label=f"Немає документа для обладнання, що впливає на безпечність: «{eq.name}»",
                    severity=AttentionSeverity.WARNING,
                    days=999,
                )
            )

    medical_checks = await medical_check_service.list_medical_checks(
        db, organization_id=organization_id
    )
    for check in medical_checks:
        days_until = (check.next_check_date - today).days
        if days_until <= MEDICAL_CHECK_WARNING_WINDOW_DAYS:
            severity = AttentionSeverity.CRITICAL if days_until < 0 else AttentionSeverity.WARNING
            status_text = (
                "прострочено" if days_until < 0 else f"спливає {check.next_check_date.isoformat()}"
            )
            attention_items.append(
                AttentionItem(
                    label=f"Медогляд «{check.employee_name}» — {status_text}",
                    severity=severity,
                    days=days_until,
                )
            )

    # Sort by severity first (critical always above warning/info), then by
    # urgency within a severity — this is a deliberate improvement over the
    # design mockup, which sorted purely by `days` and could let a badly
    # overdue warning-level item outrank a critical one.
    attention_items.sort(key=lambda item: (_SEVERITY_RANK[item.severity], item.days))

    return Dashboard(
        daily_control=ControlStatus(
            filled=daily_record is not None,
            has_deviation=daily_record.has_deviation if daily_record else None,
        ),
        monthly_control=ControlStatus(
            filled=monthly_record is not None,
            has_deviation=monthly_record.has_deviation if monthly_record else None,
        ),
        batches_this_month=batches_this_month,
        attention_items=attention_items,
    )
