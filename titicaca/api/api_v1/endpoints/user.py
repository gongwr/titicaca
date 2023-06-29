# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from fastapi import APIRouter, HTTPException, Query
from typing import Any, Optional

router = APIRouter()

@router.get("/{user_id}", status_code=200, response_model=Any)
async def hello():
    return {"message": "Hello User"}

@router.get("")
async def all():
    return {"message": "Hello All Users"}