import enum

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin, pg_enum


class EventLogSchema(enum.StrEnum):
    STANDARD = "standard"
    WATER = "water"
    PESTS = "pests"


# The canonical event log catalog this app expects to exist. Production data
# is seeded once via an Alembic migration (which keeps its own frozen copy);
# this constant exists so tests can seed an equivalent table without
# depending on migration history.
EVENT_LOG_TYPES = (
    {
        "key": "glass",
        "name": "Бій скла-пластику",
        "schema": EventLogSchema.STANDARD,
        "icon_label": "СК",
    },
    {"key": "water", "name": "Проби води", "schema": EventLogSchema.WATER, "icon_label": "ПВ"},
    {
        "key": "filters",
        "name": "Заміна фільтрів",
        "schema": EventLogSchema.STANDARD,
        "icon_label": "ЗФ",
    },
    {"key": "eq", "name": "ТО обладнання", "schema": EventLogSchema.STANDARD, "icon_label": "ТО"},
    {
        "key": "visitors",
        "name": "Відвідувачі",
        "schema": EventLogSchema.STANDARD,
        "icon_label": "ВД",
    },
    {
        "key": "disinfect",
        "name": "Дезінфекція",
        "schema": EventLogSchema.STANDARD,
        "icon_label": "ДЗ",
    },
    {
        "key": "pests",
        "name": "Контроль шкідників",
        "schema": EventLogSchema.PESTS,
        "icon_label": "КШ",
    },
    {
        "key": "deratization",
        "name": "Дератизація/дезінсекція",
        "schema": EventLogSchema.PESTS,
        "icon_label": "ДР",
    },
    {
        "key": "chemBriefing",
        "name": "Інструктажі з хімії",
        "schema": EventLogSchema.STANDARD,
        "icon_label": "ІХ",
    },
)


class EventLogType(UUIDPrimaryKeyMixin, Base):
    """The fixed catalog of event log categories (glass breakage, water
    tests, pest control, ...). Global, not org-scoped, and not
    user-editable — seeded once by migration, same as Allergen."""

    __tablename__ = "event_log_types"

    key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    schema: Mapped[EventLogSchema] = mapped_column(
        pg_enum(EventLogSchema, "event_log_schema"), nullable=False
    )
    icon_label: Mapped[str] = mapped_column(String(10), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
