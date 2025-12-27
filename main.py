from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router

app = FastAPI(title="Cosmetica SaaS API")

app.include_router(auth_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {"status": "API running"}