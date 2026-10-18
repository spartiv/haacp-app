import uuid

from app.core.errors import DomainError


class ChecklistMismatchError(DomainError):
    """Raised when submitted answers don't exactly cover a checklist's
    current active item ids (missing, extra, or foreign item ids)."""

    status_code = 422
    code = "checklist_mismatch"
    message = "Answers must cover exactly the checklist's current items"


def validate_answer_ids(
    *,
    required_ids: set[uuid.UUID],
    answers: dict[uuid.UUID, bool],
    resource_label: str = "checklist's",
) -> None:
    if set(answers.keys()) != required_ids:
        raise ChecklistMismatchError(
            f"Answers must cover exactly the {resource_label} current checklist items"
        )


def has_deviation(answers: dict[uuid.UUID, bool]) -> bool:
    return any(not answer for answer in answers.values())
