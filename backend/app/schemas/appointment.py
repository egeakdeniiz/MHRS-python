from pydantic import BaseModel

class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: str  

class AppointmentResponse(BaseModel):
    id: int
    user_id: int
    doctor_id: int
    appointment_date: str
    status: str

    class Config:
        from_attributes = True