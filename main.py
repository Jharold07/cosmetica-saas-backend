from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.stores import router as stores_router
from app.routers.users import router as users_router
from app.routers.products import router as products_router
from app.routers.inventory import router as inventory_router
from app.routers.sales import router as sales_router
from app.routers.tenants import router as tenants_router

app = FastAPI(title="Cosmetica SaaS API")

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(stores_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(sales_router)
app.include_router(tenants_router)

@app.get("/")
def root():
    return {"status": "API running"}