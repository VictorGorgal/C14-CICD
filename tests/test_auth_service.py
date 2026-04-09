import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from features.auth.service import AuthService


# ── Helpers ────────────────────────────────────────────────────────────────

def make_user(id=1, username="alice", password="secret"):
    user = MagicMock()
    user.id = id
    user.username = username
    user.password = password
    return user


def make_service():
    db = MagicMock()
    db.user = MagicMock()
    db.user.find_unique = AsyncMock()
    db.user.create = AsyncMock()

    jwt = MagicMock()
    jwt.create_token = MagicMock(return_value={"access_token": "tok123", "token_type": "bearer"})

    return AuthService(db=db, jwtHandler=jwt), db, jwt


# ── Register – fluxo normal (happy path) ───────────────────────────────────

@pytest.mark.asyncio
async def test_register_new_user_returns_token():
    """Registrar um usuário novo deve retornar um token JWT."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = None
    db.user.create.return_value = make_user()

    result = await service.register("alice", "secret")

    assert result == {"access_token": "tok123", "token_type": "bearer"}


@pytest.mark.asyncio
async def test_register_calls_find_unique_with_username():
    """Deve verificar unicidade do username antes de criar."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = None
    db.user.create.return_value = make_user()

    await service.register("alice", "secret")

    db.user.find_unique.assert_called_once_with(where={"username": "alice"})


@pytest.mark.asyncio
async def test_register_creates_user_with_correct_data():
    """Deve criar o usuário com username e password fornecidos."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = None
    db.user.create.return_value = make_user()

    await service.register("alice", "secret")

    db.user.create.assert_called_once_with(data={"username": "alice", "password": "secret"})


@pytest.mark.asyncio
async def test_register_calls_jwt_with_user_id():
    """Deve gerar o token usando o id do usuário criado."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = None
    db.user.create.return_value = make_user(id=42)

    await service.register("alice", "secret")

    jwt.create_token.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_register_different_users_get_tokens():
    """Usuários distintos devem conseguir se registrar independentemente."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = None
    db.user.create.return_value = make_user(id=99, username="bob")
    jwt.create_token.return_value = {"access_token": "tok_bob", "token_type": "bearer"}

    result = await service.register("bob", "pass123")

    assert result["access_token"] == "tok_bob"


# ── Login – fluxo normal (happy path) ──────────────────────────────────────

@pytest.mark.asyncio
async def test_login_valid_credentials_returns_token():
    """Login com credenciais corretas deve retornar token."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user(password="secret")

    result = await service.login("alice", "secret")

    assert result == {"access_token": "tok123", "token_type": "bearer"}


@pytest.mark.asyncio
async def test_login_calls_find_unique_with_username():
    """Deve buscar o usuário pelo username informado."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user(password="secret")

    await service.login("alice", "secret")

    db.user.find_unique.assert_called_once_with(where={"username": "alice"})


@pytest.mark.asyncio
async def test_login_calls_jwt_create_token():
    """Deve gerar token com o id do usuário encontrado."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user(id=7, password="secret")

    await service.login("alice", "secret")

    jwt.create_token.assert_called_once_with(7)


@pytest.mark.asyncio
async def test_login_returns_jwt_payload():
    """O retorno deve ser exatamente o que o JWTHandler retornar."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user(password="secret")
    jwt.create_token.return_value = {"access_token": "xyz", "token_type": "bearer"}

    result = await service.login("alice", "secret")

    assert result["access_token"] == "xyz"


@pytest.mark.asyncio
async def test_login_does_not_create_new_user():
    """Login não deve criar nenhum usuário no banco."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user(password="secret")

    await service.login("alice", "secret")

    db.user.create.assert_not_called()


# ── Register – fluxo de extensão (edge cases) ──────────────────────────────

@pytest.mark.asyncio
async def test_register_duplicate_username_raises():
    """Registrar username já existente deve lançar ValueError."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user()

    with pytest.raises(ValueError, match="Username already registered"):
        await service.register("alice", "outrasenha")


@pytest.mark.asyncio
async def test_register_duplicate_does_not_create_user():
    """Em caso de duplicata, create não deve ser chamado."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user()

    with pytest.raises(ValueError):
        await service.register("alice", "outrasenha")

    db.user.create.assert_not_called()


@pytest.mark.asyncio
async def test_register_duplicate_does_not_generate_token():
    """Em caso de duplicata, jwt.create_token não deve ser chamado."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user()

    with pytest.raises(ValueError):
        await service.register("alice", "outrasenha")

    jwt.create_token.assert_not_called()


# ── Login – fluxo de extensão (edge cases) ─────────────────────────────────

@pytest.mark.asyncio
async def test_login_user_not_found_raises():
    """Login com username inexistente deve lançar ValueError."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = None

    with pytest.raises(ValueError, match="Invalid credentials"):
        await service.login("ghost", "secret")


@pytest.mark.asyncio
async def test_login_wrong_password_raises():
    """Login com senha errada deve lançar ValueError."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user(password="correct")

    with pytest.raises(ValueError, match="Invalid credentials"):
        await service.login("alice", "wrong")


@pytest.mark.asyncio
async def test_login_user_not_found_does_not_generate_token():
    """Usuário inexistente não deve gerar token."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = None

    with pytest.raises(ValueError):
        await service.login("ghost", "secret")

    jwt.create_token.assert_not_called()


@pytest.mark.asyncio
async def test_login_wrong_password_does_not_generate_token():
    """Senha errada não deve gerar token."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user(password="correct")

    with pytest.raises(ValueError):
        await service.login("alice", "wrong")

    jwt.create_token.assert_not_called()


@pytest.mark.asyncio
async def test_login_empty_username_raises():
    """Login com username vazio (não encontrado) deve lançar ValueError."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = None

    with pytest.raises(ValueError, match="Invalid credentials"):
        await service.login("", "secret")


@pytest.mark.asyncio
async def test_login_empty_password_raises():
    """Login com senha vazia diferente da cadastrada deve lançar ValueError."""
    service, db, jwt = make_service()
    db.user.find_unique.return_value = make_user(password="secret")

    with pytest.raises(ValueError, match="Invalid credentials"):
        await service.login("alice", "")
