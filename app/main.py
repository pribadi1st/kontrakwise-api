from fastapi import FastAPI
from app.api.main import api_router
from app.core.config import settings

app = FastAPI(title= settings.PROJECT_NAME, description= settings.PROJECT_DESCRIPTION, version= settings.PROJECT_VERSION)

app.include_router(api_router)

@app.get("/", tags=["root"])
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}