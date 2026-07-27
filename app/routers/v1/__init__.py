from fastapi import APIRouter

from app.routers.v1.attachments import router as attachments_router
from app.routers.v1.auth import router as auth_router
from app.routers.v1.controls import router as controls_router
from app.routers.v1.dashboard import router as dashboard_router
from app.routers.v1.directories import router as directories_router
from app.routers.v1.equipment import router as equipment_router
from app.routers.v1.event_logs import router as event_logs_router
from app.routers.v1.health import router as health_router
from app.routers.v1.invites import router as invites_router
from app.routers.v1.products import router as products_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(invites_router)
api_router.include_router(products_router)
api_router.include_router(attachments_router)
api_router.include_router(equipment_router)
api_router.include_router(directories_router)
api_router.include_router(event_logs_router)
api_router.include_router(controls_router)
api_router.include_router(dashboard_router)
