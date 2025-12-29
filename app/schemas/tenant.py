from pydantic import BaseModel

class TenantCreate(BaseModel):
    name: str

class TenantResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
