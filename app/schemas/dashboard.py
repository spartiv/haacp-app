from pydantic import BaseModel


class ControlStatusResponse(BaseModel):
    filled: bool
    has_deviation: bool | None


class AttentionItemResponse(BaseModel):
    label: str
    severity: str
    days: int


class DashboardResponse(BaseModel):
    daily_control: ControlStatusResponse
    monthly_control: ControlStatusResponse
    batches_this_month: int
    attention_items: list[AttentionItemResponse]
