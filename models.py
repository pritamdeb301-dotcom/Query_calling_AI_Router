from sqlmodel import Field, SQLModel, create_engine, Session

class Patient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    phone_number: str
    created_at: str

class Appointment(SQLModel, table=True):  
    id: int | None = Field(default=None, primary_key=True)
    patient_id: int
    doctor_name: str = "Dr. Pratik Mozumder"
    appointment_time: str  # ISO format: YYYY-MM-DDTHH:MM:SS
    status: str  # 'pending', 'confirmed', 'cancelled'
    created_at: str