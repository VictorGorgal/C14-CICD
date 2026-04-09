from prisma import Prisma
from prisma.errors import PrismaError
from fastapi import HTTPException, status
from features.tasks.schema import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_task(self, user_id: int, data: TaskCreate):
        try:
            task = await self.db.task.create(
                data={
                    "title": data.title,
                    "description": data.description,
                    "priority": data.priority.value,
                    "dueDate": data.due_date,
                    "userId": user_id,
                }
            )
            return task
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create task: {str(e)}",
            )

    async def get_pending_tasks(self, user_id: int):
        try:
            tasks = await self.db.task.find_many(
                where={"userId": user_id, "completed": False},
                order={"createdAt": "desc"},
            )
            return tasks
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch pending tasks: {str(e)}",
            )

    async def get_completed_tasks(self, user_id: int):
        try:
            tasks = await self.db.task.find_many(
                where={"userId": user_id, "completed": True},
                order={"updatedAt": "desc"},
            )
            return tasks
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch completed tasks: {str(e)}",
            )

    async def update_task(self, task_id: int, user_id: int, data: TaskUpdate):
        await self._get_task_or_404(task_id, user_id)

        update_data = data.model_dump(exclude_none=True)

        # Rename due_date to dueDate for Prisma
        if "due_date" in update_data:
            update_data["dueDate"] = update_data.pop("due_date")

        if "priority" in update_data:
            update_data["priority"] = update_data["priority"].value

        try:
            task = await self.db.task.update(
                where={"id": task_id},
                data=update_data,
            )
            return task
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update task: {str(e)}",
            )

    async def complete_task(self, task_id: int, user_id: int):
        await self._get_task_or_404(task_id, user_id)

        try:
            task = await self.db.task.update(
                where={"id": task_id},
                data={"completed": True},
            )
            return task
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to complete task: {str(e)}",
            )

    async def delete_task(self, task_id: int, user_id: int):
        await self._get_task_or_404(task_id, user_id)

        try:
            await self.db.task.delete(where={"id": task_id})
        except PrismaError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete task: {str(e)}",
            )

    async def _get_task_or_404(self, task_id: int, user_id: int):
        task = await self.db.task.find_first(
            where={"id": task_id, "userId": user_id}
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return task
