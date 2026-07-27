import uuid

from pydantic import BaseModel


class AllergenStatusResponse(BaseModel):
    allergen_id: uuid.UUID
    name: str
    position: int
    present: bool


class AllergenPresenceUpdateRequest(BaseModel):
    present: bool
