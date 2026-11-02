from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Ecommerce AI Service",
    description="This is AI service for data processing",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "message": "Ecommerce AI Service is running smoothly.",
    }