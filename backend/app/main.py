from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from app.core.database import Base, engine
from app.routers import auth as auth_router
from app.routers import hospital as hospital_router
from app.routers import appointment as appointment_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MHRS Backend API",
    version="1.0.0",
    docs_url=None
)

app.include_router(auth_router.router)
app.include_router(hospital_router.router)
app.include_router(appointment_router.router)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Dokümantasyon",
        swagger_custom_parameters={
            "customCss": ".swagger-ui .info a { display: none !important; }"
        }
    )

@app.get("/")
def read_root():
    return {"message": "MHRS Backend sistemine hoş geldiniz! ", "status": "active"}
