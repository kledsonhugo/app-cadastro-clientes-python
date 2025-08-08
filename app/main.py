import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlmodel import create_engine, Field, SQLModel, Session, select


load_dotenv()


def _get_env_db_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./clientes.db")


def _get_env_echo() -> bool:
    return os.getenv("ECHO_SQL", "false").lower() == "true"


# Engine global, inicializado no lifespan
engine = None  # type: ignore


class ClienteBase(SQLModel):
    nome: str
    email: EmailStr


class Cliente(ClienteBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # Garante unicidade do email no banco
    email: EmailStr = Field(index=True, sa_column_kwargs={"unique": True})


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(SQLModel):
    nome: str | None = None
    email: EmailStr | None = None


def get_session():
    if engine is None:
        # Fallback para execuções fora do ciclo de vida (ex.: import direto)
        tmp_engine = create_engine(
            _get_env_db_url(),
            echo=_get_env_echo(),
            connect_args=(
                {"check_same_thread": False} if _get_env_db_url().startswith("sqlite") else {}
            ),
        )
        SQLModel.metadata.create_all(tmp_engine)
        with Session(tmp_engine) as session:
            yield session
        tmp_engine.dispose()
        return
    with Session(engine) as session:  # type: ignore[arg-type]
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    db_url = _get_env_db_url()
    echo = _get_env_echo()
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, echo=echo, connect_args=connect_args)
    init_db()
    try:
        yield
    finally:
        if engine is not None:
            engine.dispose()
            engine = None


app = FastAPI(title="API Cadastro de Clientes", version="0.2.0", lifespan=lifespan)


@app.get("/clientes", response_model=list[Cliente], summary="Lista todos os clientes")
def listar_clientes(session: Session = Depends(get_session)) -> list[Cliente]:
    return session.exec(select(Cliente)).all()


@app.get("/clientes/{cliente_id}", response_model=Cliente, summary="Obtém um cliente")
def obter_cliente(cliente_id: int, session: Session = Depends(get_session)) -> Cliente:
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return cliente


@app.post(
    "/clientes",
    response_model=Cliente,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um cliente",
)
def criar_cliente(payload: ClienteCreate, session: Session = Depends(get_session)) -> Cliente:
    cliente = Cliente.model_validate(payload)
    session.add(cliente)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")
    session.refresh(cliente)
    return cliente


@app.put("/clientes/{cliente_id}", response_model=Cliente, summary="Atualiza um cliente")
def atualizar_cliente(
    cliente_id: int, payload: ClienteUpdate, session: Session = Depends(get_session)
) -> Cliente:
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(cliente, k, v)
    session.add(cliente)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")
    session.refresh(cliente)
    return cliente


@app.delete(
    "/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove um cliente"
)
def remover_cliente(cliente_id: int, session: Session = Depends(get_session)) -> None:
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    session.delete(cliente)
    session.commit()
    return None
