import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_membership
from app.db.session import get_db_session
from app.models import Membership
from app.schemas.dashboard import (
    AttentionItemResponse,
    ControlStatusResponse,
    DashboardResponse,
    SetupProgressResponse,
    SetupStepResponse,
)
from app.services import dashboard_service, setup_progress_service

router = APIRouter(prefix="/organizations/{organization_id}", tags=["dashboard"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AnyMember = Annotated[Membership, Depends(require_membership())]


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> DashboardResponse:
    dashboard = await dashboard_service.get_dashboard(db, organization_id=organization_id)

    return DashboardResponse(
        daily_control=ControlStatusResponse(
            filled=dashboard.daily_control.filled,
            has_deviation=dashboard.daily_control.has_deviation,
        ),
        monthly_control=ControlStatusResponse(
            filled=dashboard.monthly_control.filled,
            has_deviation=dashboard.monthly_control.has_deviation,
        ),
        batches_this_month=dashboard.batches_this_month,
        attention_items=[
            AttentionItemResponse(label=item.label, severity=item.severity.value, days=item.days)
            for item in dashboard.attention_items
        ],
    )


@router.get("/setup-progress", response_model=SetupProgressResponse)
async def get_setup_progress(
    organization_id: uuid.UUID, db: DbSession, _: AnyMember
) -> SetupProgressResponse:
    progress = await setup_progress_service.get_setup_progress(db, organization_id=organization_id)
    return SetupProgressResponse(
        completed=progress.completed,
        total=progress.total,
        steps=[
            SetupStepResponse(
                key=step.key.value, label=step.label, done=step.done, count=step.count
            )
            for step in progress.steps
        ],
    )
