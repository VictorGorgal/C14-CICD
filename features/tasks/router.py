from fastapi import APIRouter, Depends
from typing import List
from features.tasks.schema import TaskCreate, TaskUpdate, TaskResponse
from features.tasks.service import TaskService
from features.core.database import db
from features.auth.utils import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_task_service() -> TaskService:
    return TaskService(db)


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    current_user=Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    return await service.create_task(user_id=current_user, data=data)


@router.get("/pending", response_model=List[TaskResponse])
async def get_pending_tasks(
    current_user=Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    return await service.get_pending_tasks(user_id=current_user)


@router.get("/completed", response_model=List[TaskResponse])
async def get_completed_tasks(
    current_user=Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    return await service.get_completed_tasks(user_id=current_user)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user=Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    return await service.update_task(task_id=task_id, user_id=current_user, data=data)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    current_user=Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    return await service.complete_task(task_id=task_id, user_id=current_user)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    current_user=Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    await service.delete_task(task_id=task_id, user_id=current_user)
