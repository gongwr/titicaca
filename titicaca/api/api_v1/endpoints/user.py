# Copyright (c) 2023 WenRui Gong
# All rights reserved.


import http.client

from fastapi import APIRouter

router = APIRouter()


def _list_users():
    return [
        {"username": "Foo"},
        {"username": "Bar"},
        {"username": "Baz"},
    ]


def _get_user(user_id: int):
    return {"username": "Foo"}


@router.get("/{user_id}")
async def get_user(user_id: int):
    return _get_user(user_id)


@router.head("/{user_id}")
async def list_user(user_id: int):
    return _get_user(user_id)


@router.get("")
async def get_users():
    return _list_users()


@router.head("")
async def list_users():
    return _list_users()


@router.post("")
async def create_user():
    return http.client.CREATED


@router.patch("/{user_id}")
async def update_user(user_id: int):
    return _get_user(user_id)


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    return http.client.NO_CONTENT
