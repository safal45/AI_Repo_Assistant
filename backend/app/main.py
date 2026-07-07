from fastapi import FastAPI
from app.config.settings import settings
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes import repository

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(repository.router)

@app.get("/")
def root():

    return {
        "message": f"Welcome to {settings.APP_NAME}"
    }