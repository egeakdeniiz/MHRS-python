from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import Appointment, Doctor, User
from app.schemas.appointment import AppointmentCreate, AppointmentResponse

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate, user_id: int, db: Session = Depends(get_db)):
    """Belirtilen doktor ve tarih için yeni bir MHRS randevusu oluşturur."""
    # Kullanıcı kontrolü
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    
    # Doktor kontrolü
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doktor bulunamadı.")
    
    new_appointment = Appointment(
        user_id=user_id,
        doctor_id=appointment.doctor_id,
        appointment_date=appointment.appointment_date,
        status="Active"
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return new_appointment

@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(user_id: int, db: Session = Depends(get_db)):
    """Belirli bir kullanıcının aldığı tüm randevuları listeler."""
    return db.query(Appointment).filter(Appointment.user_id == user_id).all()