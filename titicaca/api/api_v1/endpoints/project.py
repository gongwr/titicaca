# Copyright (c) 2023 WenRui Gong
# All rights reserved.


import http.client

from fastapi import APIRouter

router = APIRouter()


def _list_projects():
    return [
        {"project_id": 1},
        {"project_id": 2},
        {"project_id": 3},
    ]


def _get_project(project_id: int):
    return {"project_id": project_id}


@router.get("")
async def get_projects():
    """Get list projects.

    GET/HEAD /v1/projects
    """
    return _list_projects()


@router.head("")
async def list_projects():
    """Get list projects.

    GET/HEAD /v1/projects
    """
    return _list_projects()


@router.get("/{project_id}")
async def get_project(project_id: int):
    """Get project by project id.

    GET/HEAD /v1/projects/{project_id}
    """
    return _get_project(project_id)


@router.head("/{project_id}")
async def list_project(project_id: int):
    """Get project by project id.

    HEAD /v1/projects/{project_id}
    """
    return _get_project(project_id)


@router.post("")
async def create_project():
    """Create project.

    POST /v1/projects
    """
    return http.client.CREATED


@router.patch("/{project_id}")
async def update_project(project_id: int):
    """Update project.

    PATCH /v1/projects/{project_id}
    """
    return _get_project(project_id)


@router.delete("/{project_id}")
async def delete_project(project_id: int):
    return http.client.NO_CONTENT
