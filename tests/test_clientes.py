import os
import tempfile
from contextlib import contextmanager

from fastapi.testclient import TestClient


@contextmanager
def temp_db_env():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    abs_path = os.path.abspath(path)
    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:////{abs_path}"
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def make_client():
    # Import tardio para pegar DATABASE_URL já setado
    from app.main import app  # type: ignore

    return TestClient(app)


def test_crud_clientes():
    with temp_db_env():
        with make_client() as client:
            # Lista inicial vazia
            resp = client.get("/clientes")
            assert resp.status_code == 200
            assert resp.json() == []

            # Cria cliente
            novo = {"nome": "Ana", "email": "ana@example.com"}
            resp = client.post("/clientes", json=novo)
            assert resp.status_code == 201
            created = resp.json()
            assert created["id"] > 0

            cid = created["id"]

            # Obtém por id
            resp = client.get(f"/clientes/{cid}")
            assert resp.status_code == 200
            assert resp.json()["email"] == "ana@example.com"

            # Atualiza
            resp = client.put(f"/clientes/{cid}", json={"nome": "Ana Souza"})
            assert resp.status_code == 200
            assert resp.json()["nome"] == "Ana Souza"

            # Lista contendo 1
            resp = client.get("/clientes")
            assert resp.status_code == 200
            assert len(resp.json()) == 1

            # Remove
            resp = client.delete(f"/clientes/{cid}")
            assert resp.status_code == 204

            # 404 após remoção
            resp = client.get(f"/clientes/{cid}")
            assert resp.status_code == 404
