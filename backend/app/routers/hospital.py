from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
 
from app.core.database import get_db
from app.models import Branch, Doctor
from app.schemas.branch_doctor import BranchCreate, BranchResponse, DoctorCreate, DoctorResponse
 
router = APIRouter(
    prefix="/hospital",
    tags=["Hospital & Doctors"]
)
 
@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(branch: BranchCreate, db: Session = Depends(get_db)):
    db_branch = db.query(Branch).filter(Branch.name == branch.name).first()
    if db_branch:
        raise HTTPException(status_code=400, detail="Bu branş zaten mevcut.")
    new_branch = Branch(name=branch.name)
    db.add(new_branch)
    db.commit()
    db.refresh(new_branch)
    return new_branch
 
@router.get("/branches", response_model=List[BranchResponse])
def get_branches(db: Session = Depends(get_db)):
    return db.query(Branch).all()
 
@router.post("/doctors", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    branch = db.query(Branch).filter(Branch.id == doctor.branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Belirtilen branş bulunamadı.")
    new_doctor = Doctor(full_name=doctor.full_name, branch_id=doctor.branch_id)
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return new_doctor
 
@router.get("/doctors", response_model=List[DoctorResponse])
def get_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()
