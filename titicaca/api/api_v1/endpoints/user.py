from fastapi import APIRouter, HTTPException, Query
from typing import Any, Optional

router = APIRouter()

@router.get("/hello")
async def hello():
    return {"message": "Hello User"}
