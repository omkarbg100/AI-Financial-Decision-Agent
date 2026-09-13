from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class ExtractedAmount(BaseModel):
    amount: Optional[float] = Field(description="The numerical amount extracted from the image. Null if no amount is found.")

class EventStatus(BaseModel):
    action: Literal["cancelled", "amended", "confirmed", "none"] = Field(description="Action indicated by the message regarding the financial event.")
    new_amount: Optional[float] = Field(description="If amended, the new amount specified. Null otherwise.")
    new_date: Optional[str] = Field(description="If amended, the new date specified in YYYY-MM-DD format. Null otherwise.")
    reason: Optional[str] = Field(description="Reason for the action, if any.")

class OutputRow(BaseModel):
    request_id: str
    amount_safe_to_pay: float
    affordability_status: Literal["affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"]
    recommended_payment_method: Literal["full_payment", "partial_payment", "installments", "wait", "not_recommended"]
    payment_plan: str
    earliest_date_for_full_payment: str
    spending_changes_needed: str
    decision_explanation: str
