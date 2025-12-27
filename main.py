from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.stores import router as stores_router
from app.routers.users import router as users_router

app = FastAPI(title="Cosmetica SaaS API")

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(stores_router)
app.include_router(users_router)

@app.get("/")
def root():
    return {"status": "API running"}