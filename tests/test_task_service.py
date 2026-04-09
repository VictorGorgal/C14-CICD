import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from prisma.errors import PrismaError
from features.tasks.service import TaskService


# ── Helpers ────────────────────────────────────────────────────────────────

def make_db():
    db = MagicMock()
    db.task = MagicMock()
    db.task.create = AsyncMock()
    db.task.find_many = AsyncMock()
    db.task.find_first = AsyncMock()
    db.task.update = AsyncMock()
    db.task.delete = AsyncMock()
    return db


def make_task(id=1, title="Buy milk", completed=False, user_id=10):
    task = MagicMock()
    task.id = id
    task.title = title
    task.completed = completed
    task.userId = user_id
    return task


def make_task_create(title="Buy milk", description="2% fat", priority=None, due_date=None):
    data = MagicMock()
    data.title = title
    data.description = description
    data.priority = MagicMock()
    data.priority.value = priority or "MEDIUM"
    data.due_date = due_date
    return data


def make_task_update(**kwargs):
    data = MagicMock()
    dump = {}
    if "title" in kwargs:
        dump["title"] = kwargs["title"]
    if "priority" in kwargs:
        p = MagicMock()
        p.value = kwargs["priority"]
        dump["priority"] = p
    if "due_date" in kwargs:
        dump["due_date"] = kwargs["due_date"]
    data.model_dump = MagicMock(return_value=dump)
    return data


# ── create_task – fluxo normal ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task_returns_task():
    """Criar tarefa válida deve retornar o objeto criado."""
    db = make_db()
    db.task.create.return_value = make_task()
    service = TaskService(db=db)

    result = await service.create_task(10, make_task_create())

    assert result.title == "Buy milk"


@pytest.mark.asyncio
async def test_create_task_calls_db_with_correct_data():
    """Deve chamar db.task.create com userId e campos corretos."""
    db = make_db()
    db.task.create.return_value = make_task()
    service = TaskService(db=db)
    data = make_task_create(title="Read book", description="Chapter 1", priority="HIGH")

    await service.create_task(10, data)

    call_data = db.task.create.call_args[1]["data"]
    assert call_data["userId"] == 10
    assert call_data["title"] == "Read book"
    assert call_data["priority"] == "HIGH"


@pytest.mark.asyncio
async def test_create_task_with_due_date():
    """Deve incluir dueDate quando fornecido."""
    from datetime import datetime
    db = make_db()
    db.task.create.return_value = make_task()
    service = TaskService(db=db)
    due = datetime(2025, 12, 31)
    data = make_task_create(due_date=due)

    await service.create_task(10, data)

    call_data = db.task.create.call_args[1]["data"]
    assert call_data["dueDate"] == due


# ── get_pending_tasks – fluxo normal ──────────────────────────────────────

@pytest.mark.asyncio
async def test_get_pending_tasks_returns_list():
    """Deve retornar lista de tarefas pendentes."""
    db = make_db()
    db.task.find_many.return_value = [make_task(completed=False), make_task(id=2, completed=False)]
    service = TaskService(db=db)

    result = await service.get_pending_tasks(10)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_pending_tasks_filters_by_user_and_completed():
    """Deve filtrar por userId e completed=False."""
    db = make_db()
    db.task.find_many.return_value = []
    service = TaskService(db=db)

    await service.get_pending_tasks(10)

    call_where = db.task.find_many.call_args[1]["where"]
    assert call_where["userId"] == 10
    assert call_where["completed"] is False


@pytest.mark.asyncio
async def test_get_pending_tasks_empty_returns_empty_list():
    """Deve retornar lista vazia se não houver tarefas pendentes."""
    db = make_db()
    db.task.find_many.return_value = []
    service = TaskService(db=db)

    result = await service.get_pending_tasks(10)

    assert result == []


# ── get_completed_tasks – fluxo normal ────────────────────────────────────

@pytest.mark.asyncio
async def test_get_completed_tasks_returns_list():
    """Deve retornar lista de tarefas concluídas."""
    db = make_db()
    db.task.find_many.return_value = [make_task(completed=True)]
    service = TaskService(db=db)

    result = await service.get_completed_tasks(10)

    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_completed_tasks_filters_correctly():
    """Deve filtrar por userId e completed=True."""
    db = make_db()
    db.task.find_many.return_value = []
    service = TaskService(db=db)

    await service.get_completed_tasks(10)

    call_where = db.task.find_many.call_args[1]["where"]
    assert call_where["completed"] is True
    assert call_where["userId"] == 10


# ── complete_task – fluxo normal ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_complete_task_sets_completed_true():
    """Deve atualizar completed=True na tarefa."""
    db = make_db()
    db.task.find_first.return_value = make_task()
    db.task.update.return_value = make_task(completed=True)
    service = TaskService(db=db)

    result = await service.complete_task(1, 10)

    db.task.update.assert_called_once_with(
        where={"id": 1},
        data={"completed": True},
    )


@pytest.mark.asyncio
async def test_complete_task_returns_updated_task():
    """Deve retornar a tarefa atualizada."""
    db = make_db()
    db.task.find_first.return_value = make_task()
    updated = make_task(completed=True)
    db.task.update.return_value = updated
    service = TaskService(db=db)

    result = await service.complete_task(1, 10)

    assert result.completed is True


# ── delete_task – fluxo normal ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_task_calls_db_delete():
    """Deve chamar db.task.delete com o id correto."""
    db = make_db()
    db.task.find_first.return_value = make_task()
    db.task.delete.return_value = None
    service = TaskService(db=db)

    await service.delete_task(1, 10)

    db.task.delete.assert_called_once_with(where={"id": 1})


# ── update_task – fluxo normal ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_task_returns_updated():
    """Deve retornar a tarefa atualizada após update."""
    db = make_db()
    db.task.find_first.return_value = make_task()
    updated = make_task(title="Updated title")
    db.task.update.return_value = updated
    service = TaskService(db=db)
    data = make_task_update(title="Updated title")

    result = await service.update_task(1, 10, data)

    assert result.title == "Updated title"


@pytest.mark.asyncio
async def test_update_task_renames_due_date_to_dueDate():
    """Deve renomear due_date para dueDate antes de enviar ao Prisma."""
    from datetime import datetime
    db = make_db()
    db.task.find_first.return_value = make_task()
    db.task.update.return_value = make_task()
    service = TaskService(db=db)
    data = make_task_update(due_date=datetime(2025, 6, 1))

    await service.update_task(1, 10, data)

    call_data = db.task.update.call_args[1]["data"]
    assert "dueDate" in call_data
    assert "due_date" not in call_data


# ── Fluxo de extensão (edge cases / erros) ────────────────────────────────

@pytest.mark.asyncio
async def test_create_task_prisma_error_raises_http_500():
    """PrismaError no create deve lançar HTTPException 500."""
    db = make_db()
    db.task.create.side_effect = PrismaError("db error")
    service = TaskService(db=db)

    with pytest.raises(HTTPException) as exc:
        await service.create_task(10, make_task_create())

    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_get_pending_tasks_prisma_error_raises_http_500():
    """PrismaError no find_many de pendentes deve lançar HTTPException 500."""
    db = make_db()
    db.task.find_many.side_effect = PrismaError("db error")
    service = TaskService(db=db)

    with pytest.raises(HTTPException) as exc:
        await service.get_pending_tasks(10)

    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_get_completed_tasks_prisma_error_raises_http_500():
    """PrismaError no find_many de concluídas deve lançar HTTPException 500."""
    db = make_db()
    db.task.find_many.side_effect = PrismaError("db error")
    service = TaskService(db=db)

    with pytest.raises(HTTPException) as exc:
        await service.get_completed_tasks(10)

    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_complete_task_not_found_raises_http_404():
    """complete_task com tarefa inexistente deve lançar HTTPException 404."""
    db = make_db()
    db.task.find_first.return_value = None
    service = TaskService(db=db)

    with pytest.raises(HTTPException) as exc:
        await service.complete_task(999, 10)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_not_found_raises_http_404():
    """delete_task com tarefa inexistente deve lançar HTTPException 404."""
    db = make_db()
    db.task.find_first.return_value = None
    service = TaskService(db=db)

    with pytest.raises(HTTPException) as exc:
        await service.delete_task(999, 10)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_task_not_found_raises_http_404():
    """update_task com tarefa inexistente deve lançar HTTPException 404."""
    db = make_db()
    db.task.find_first.return_value = None
    service = TaskService(db=db)
    data = make_task_update(title="x")

    with pytest.raises(HTTPException) as exc:
        await service.update_task(999, 10, data)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_complete_task_wrong_user_raises_http_404():
    """complete_task com userId errado deve lançar 404 (tarefa não encontrada)."""
    db = make_db()
    db.task.find_first.return_value = None  # find_first retorna None p/ user errado
    service = TaskService(db=db)

    with pytest.raises(HTTPException) as exc:
        await service.complete_task(1, 999)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_complete_task_prisma_error_raises_http_500():
    """PrismaError no update de complete deve lançar HTTPException 500."""
    db = make_db()
    db.task.find_first.return_value = make_task()
    db.task.update.side_effect = PrismaError("db error")
    service = TaskService(db=db)

    with pytest.raises(HTTPException) as exc:
        await service.complete_task(1, 10)

    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_delete_task_prisma_error_raises_http_500():
    """PrismaError no delete deve lançar HTTPException 500."""
    db = make_db()
    db.task.find_first.return_value = make_task()
    db.task.delete.side_effect = PrismaError("db error")
    service = TaskService(db=db)

    with pytest.raises(HTTPException) as exc:
        await service.delete_task(1, 10)

    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_update_task_prisma_error_raises_http_500():
    """PrismaError no update deve lançar HTTPException 500."""
    db = make_db()
    db.task.find_first.return_value = make_task()
    db.task.update.side_effect = PrismaError("db error")
    service = TaskService(db=db)
    data = make_task_update(title="fail")

    with pytest.raises(HTTPException) as exc:
        await service.update_task(1, 10, data)

    assert exc.value.status_code == 500
