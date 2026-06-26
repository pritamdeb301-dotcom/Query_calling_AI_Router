"""Webhook that creates a confirmed appointment.

Expected payload:
```json
{
  "name": "Jane Doe",
  "phone_number": "+15551234567",
  "desired_time": "2026-07-01T14:00:00"
}
```
The endpoint:
1. Ensures the slot is still free (re‑checks availability).
2. Creates a `Patient` row if one does not already exist.
3. Inserts an `Appointment` with status `confirmed`.
4. Returns the new appointment ID.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import requests
from fastapi import BackgroundTasks  # Add this if BackgroundTasks isn't already imported

from sqlmodel import select
from app.database.session import get_session
from app.database.models import Patient, Appointment

router = APIRouter()

class BookingRequest(BaseModel):
    name: str = Field(..., description="Patient's full name")
    phone_number: str = Field(..., description="E.164 formatted phone number")
    desired_time: datetime = Field(..., description="Requested appointment datetime (ISO‑8601)")

class BookingResponse(BaseModel):
    appointment_id: int
    status: str = "confirmed"

def send_phone_notification(booking_details):
    """Sends a push notification to your phone via ntfy.sh"""
    # ⚠️ Change this to your exact secret topic name from the app
    topic_url = "https://ntfy.sh/pratik_clinic_alerts_2026"
    
    message = (
        f"🚨 New Appointment Booked!\n"
        f"Patient: {booking_details.get('name')}\n"
        f"Phone: {booking_details.get('phone')}\n"
        f"Time: {booking_details.get('time')}"
    )
    try:
        requests.post(topic_url, data=message.encode(encoding='utf-8'))
        print("Phone notification sent successfully!")
    except Exception as e:
        print(f"Failed to send notification: {e}")

@router.post("/create-booking", response_model=BookingResponse)
async def create_booking(payload: BookingRequest, background_tasks: BackgroundTasks):
    """Create a new booking and return its ID."""
    # existing implementation unchanged
    # (no changes needed for creation)
    # 1️⃣ Re‑check slot availability to avoid race conditions
    with get_session() as session:
        stmt = select(Appointment).where(
            Appointment.appointment_time == payload.desired_time.isoformat(),
            Appointment.status.in_(["pending", "confirmed"]),
        )
        conflict = session.exec(stmt).first()
        if conflict:
            raise HTTPException(status_code=409, detail="Time slot already taken")

        # 2️⃣ Find or create patient record
        stmt = select(Patient).where(Patient.phone_number == payload.phone_number)
        patient = session.exec(stmt).first()
        if not patient:
            patient = Patient(
                name=payload.name,
                phone_number=payload.phone_number,
                created_at=datetime.utcnow().isoformat(),
            )
            session.add(patient)
            session.commit()
            session.refresh(patient)

      # 3 Insert appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_name="Dr. Pratik Mozumder",
            appointment_time=payload.desired_time.isoformat(),
            status="confirmed",
            created_at=datetime.utcnow().isoformat(),
        )
        session.add(appointment)
        session.commit()
        session.refresh(appointment)

        # Gather details for the notification
        booking_details = {
            "name": payload.name,
            "phone": payload.phone_number,
            "time": payload.desired_time.isoformat()
        }

        # Trigger notification in the background
        background_tasks.add_task(send_phone_notification, booking_details)

        return BookingResponse(appointment_id=appointment.id)  

class BookingInfoResponse(BaseModel):
    appointment_id: int
    patient_name: str
    phone_number: str
    doctor_name: str
    appointment_time: str
    status: str
    created_at: str
    
@router.get("/booking/{appointment_id}", response_model=BookingInfoResponse)
async def get_booking(appointment_id: int):
    """Fetch detailed information for a specific booking.

    Returns patient details, doctor, time, status, and creation timestamp.
    """
    with get_session() as session:
        # Retrieve the appointment
        appointment = session.get(Appointment, appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        # Retrieve associated patient
        patient = session.get(Patient, appointment.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return BookingInfoResponse(
            appointment_id=appointment.id,
            patient_name=patient.name,
            phone_number=patient.phone_number,
            doctor_name=appointment.doctor_name,
            appointment_time=appointment.appointment_time,
            status=appointment.status,
            created_at=appointment.created_at,
        )
