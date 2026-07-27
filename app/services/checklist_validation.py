import uuid


class ChecklistMismatchError(Exception):
    """Raised when submitted answers don't exactly cover a checklist's
    current active item ids (missing, extra, or foreign item ids)."""


def validate_answer_ids(*, required_ids: set[uuid.UUID], answers: dict[uuid.UUID, bool]) -> None:
    if set(answers.keys()) != required_ids:
        raise ChecklistMismatchError


def has_deviation(answers: dict[uuid.UUID, bool]) -> bool:
    return any(not answer for answer in answers.values())
