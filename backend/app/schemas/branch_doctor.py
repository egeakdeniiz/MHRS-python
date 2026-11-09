from pydantic import BaseModel

class BranchBase(BaseModel):
    name: str

class BranchCreate(BranchBase):
    pass

class BranchResponse(BranchBase):
    id: int

    class Config:
        from_attributes = True


class DoctorBase(BaseModel):
    full_name: str
    branch_id: int

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    id: int
    branch: BranchResponse 

    class Config:
        from_attributes = True
