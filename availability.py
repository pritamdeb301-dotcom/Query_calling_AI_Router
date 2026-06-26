"""Webhook for checking appointment slot availability.

Expected request JSON:
```json
{ "desired_time": "2026-07-01T14:00:00" }
```
The endpoint verifies that no confirmed or pending appointment exists for that exact time.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from sqlmodel import select
from app.database.session import get_session
from app.database.models import Appointment

router = APIRouter()

class AvailabilityRequest(BaseModel):
    desired_time: datetime = Field(..., description="ISO‑8601 datetime of the requested slot")

class AvailabilityResponse(BaseModel):
    available: bool
    conflicting_appointment_id: int | None = None

@router.post("/check-availability", response_model=AvailabilityResponse)
async def check_availability(payload: AvailabilityRequest):
    with get_session() as session:
        stmt = select(Appointment).where(
            Appointment.appointment_time == payload.desired_time.isoformat(),
            Appointment.status.in_(["pending", "confirmed"]),
        )
        result = session.exec(stmt).first()
        if result:
            return AvailabilityResponse(available=False, conflicting_appointment_id=result.id)
        return AvailabilityResponse(available=True)
