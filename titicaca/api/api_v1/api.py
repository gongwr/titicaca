# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from fastapi import APIRouter

from titicaca.api.api_v1.endpoints import user


api_router = APIRouter()
api_router.include_router(user.router, prefix="/user", tags=["users"])
