from fastapi import FastAPI
from app.api.main import api_router
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title= settings.PROJECT_NAME, description= settings.PROJECT_DESCRIPTION, version= settings.PROJECT_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)

@app.get("/", tags=["root"])
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}