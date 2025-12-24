from fastapi import FastAPI
from app.core.database import test_connection

app = FastAPI(title="Cosmetica SaaS API")

@app.get("/")
def root():
    return {"status": "API running"}

#probar conexion a la base de datos
@app.get("/health/db")
def health_db():
    value = test_connection()
    return {"db": "ok", "select_1": value}