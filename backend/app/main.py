from fastapi import FastAPI
from app.core.database import Base, engine
from app.routers import auth as auth_router
from app.routers import hospital as hospital_router
from app.routers import appointment as appointment_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MHRS Backend API",
    version="1.0.0",
    description="Python 3.12 ve FastAPI ile geliştirilmiş altyapı"
)

app.include_router(auth_router.router)
app.include_router(hospital_router.router)
app.include_router(appointment_router.router)

@app.get("/")
def read_root():
    return {"message": "MHRS Backend sistemine hoş geldiniz! 🚀", "status": "active"}
