"""
    Main file for been called from uvicorn
"""
# pylint: disable=E0401


from fastapi import FastAPI
from mangum import Mangum
from app.api.api_v1.api import router as api_router

app = FastAPI()
app.include_router(api_router, prefix="/api/v1")
handler = Mangum(app)
