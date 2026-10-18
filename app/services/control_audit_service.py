"""Write-side helpers for the append-only control audit log.

Shared by the per-item sheet workflow (control_sheet_service) and the legacy
full-sheet endpoints (control_record_service) so both log identically."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ControlAnswer,
    ControlAuditEvent,
    ControlAuditEventType,
    ControlItemStatus,
    ControlRecord,
    ControlRecordStatus,
)


def answer_status(answer: ControlAnswer | None) -> ControlItemStatus:
    if answer is None:
        return ControlItemStatus.PENDING
    return ControlItemStatus.PASS if answer.answer else ControlItemStatus.DEVIATION


def append_item_event(
    db: AsyncSession,
    *,
    record: ControlRecord,
    actor_user_id: uuid.UUID,
    item_id: uuid.UUID,
    previous_status: ControlItemStatus,
    new_status: ControlItemStatus,
    corrective_action: str | None,
    amendment_reason: str | None,
    numeric_value: Decimal | None = None,
    performed_by_user_id: uuid.UUID | None = None,
) -> ControlAuditEvent:
    """Logs one item state change. The event type follows the record's state
    at the time of the change: draft -> item_checked, submitted -> item_amended."""
    is_amendment = record.status == ControlRecordStatus.SUBMITTED
    event_type = (
        ControlAuditEventType.ITEM_AMENDED if is_amendment else ControlAuditEventType.ITEM_CHECKED
    )
    audit_event = ControlAuditEvent(
        organization_id=record.organization_id,
        control_record_id=record.id,
        control_checklist_item_id=item_id,
        event_type=event_type,
        previous_status=previous_status,
        new_status=new_status,
        numeric_value=numeric_value,
        corrective_action=corrective_action,
        amendment_reason=amendment_reason if is_amendment else None,
        actor_user_id=actor_user_id,
        performed_by_user_id=performed_by_user_id or actor_user_id,
    )
    db.add(audit_event)
    return audit_event


def submit_record(db: AsyncSession, *, record: ControlRecord, actor_user_id: uuid.UUID) -> None:
    """Marks a draft record as submitted and logs it. Callers check
    completeness first; this only performs the transition."""
    record.status = ControlRecordStatus.SUBMITTED
    record.submitted_at = datetime.now(UTC)
    record.submitted_by_user_id = actor_user_id
    record.signatory_user_id = actor_user_id
    db.add(
        ControlAuditEvent(
            organization_id=record.organization_id,
            control_record_id=record.id,
            control_checklist_item_id=None,
            event_type=ControlAuditEventType.RECORD_SUBMITTED,
            previous_status=None,
            new_status=None,
            corrective_action=None,
            amendment_reason=None,
            actor_user_id=actor_user_id,
        )
    )
