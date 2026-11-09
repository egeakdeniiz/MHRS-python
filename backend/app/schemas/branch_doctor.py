from pydantic import BaseModel

# --- Branch (Branş) Şemaları ---
class BranchBase(BaseModel):
    name: str

class BranchCreate(BranchBase):
    pass

class BranchResponse(BranchBase):
    id: int

    class Config:
        from_attributes = True


# --- Doctor (Doktor) Şemaları ---
class DoctorBase(BaseModel):
    full_name: str
    branch_id: int

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    id: int
    branch: BranchResponse # Doktorun hangi branşta olduğunu detaylı gösterir

    class Config:
        from_attributes = True