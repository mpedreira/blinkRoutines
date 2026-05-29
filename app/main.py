"""
    Main file for been called from uvicorn
"""
# pylint: disable=E0401


from fastapi import FastAPI
from mangum import Mangum
from app.api.api_v1.api import router as api_router
from app.api.api_v2.api import router as api_v2_router

app = FastAPI()
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")
handler = Mangum(app)
