from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin

# The canonical list this app expects in the `allergens` table, in display
# order. Production data is seeded once via an Alembic migration (which
# keeps its own frozen copy, as migrations should); this constant exists so
# tests can seed an equivalent table without depending on migration history.
LEGAL_ALLERGENS = (
    "Глютен (зернові)",
    "Ракоподібні",
    "Яйця",
    "Риба",
    "Арахіс",
    "Соя",
    "Молоко",
    "Горіхи",
    "Селера",
    "Гірчиця",
    "Насіння кунжуту",
    "Діоксид сірки/сульфіти",
    "Люпин",
    "Молюски",
)


class Allergen(UUIDPrimaryKeyMixin, Base):
    """The fixed 14-item legal allergen list (Law of Ukraine №771/97-ВР).
    Global, not org-scoped, and not user-editable — seeded once by migration.
    Each organization's per-allergen 'present' toggle lives in
    OrganizationAllergenStatus."""

    __tablename__ = "allergens"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
