import os
import tempfile
from contextlib import contextmanager

from fastapi.testclient import TestClient


@contextmanager
def temp_db_env():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    # Garantir URL absoluta com 4 barras (sqlite:////abs)
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
    from app.main import app  # type: ignore

    return TestClient(app)


def test_get_lista_vazia_e_criacao():
    with temp_db_env():
        with make_client() as client:
            r = client.get("/clientes")
            assert r.status_code == 200
            assert r.json() == []

            r = client.post("/clientes", json={"nome": "Ana", "email": "ana@example.com"})
            assert r.status_code == 201
            cid = r.json()["id"]

            r = client.get(f"/clientes/{cid}")
            assert r.status_code == 200
            assert r.json()["email"] == "ana@example.com"


def test_post_email_invalido_retorna_422():
    with temp_db_env():
        with make_client() as client:
            r = client.post("/clientes", json={"nome": "Ana", "email": "invalido"})
            assert r.status_code == 422


def test_post_email_duplicado_retorna_409():
    with temp_db_env():
        with make_client() as client:
            client.post("/clientes", json={"nome": "Ana", "email": "a@a.com"})
            r = client.post("/clientes", json={"nome": "Bia", "email": "a@a.com"})
            assert r.status_code == 409


def test_get_nao_encontrado_404():
    with temp_db_env():
        with make_client() as client:
            r = client.get("/clientes/9999")
            assert r.status_code == 404


def test_put_atualiza_e_409_se_duplicado():
    with temp_db_env():
        with make_client() as client:
            c1 = client.post("/clientes", json={"nome": "Ana", "email": "ana@ex.com"}).json()
            _ = client.post("/clientes", json={"nome": "Bia", "email": "bia@ex.com"}).json()

            r = client.put(f"/clientes/{c1['id']}", json={"nome": "Ana Souza"})
            assert r.status_code == 200
            assert r.json()["nome"] == "Ana Souza"

            # Tentar atualizar c1 com email de c2 -> 409
            r = client.put(f"/clientes/{c1['id']}", json={"email": "bia@ex.com"})
            assert r.status_code == 409


def test_put_404_para_id_inexistente():
    with temp_db_env():
        with make_client() as client:
            r = client.put("/clientes/9999", json={"nome": "X"})
            assert r.status_code == 404


def test_delete_remove_e_404_se_nao_existe():
    with temp_db_env():
        with make_client() as client:
            created = client.post("/clientes", json={"nome": "Ana", "email": "ana@ex.com"}).json()
            cid = created["id"]
            r = client.delete(f"/clientes/{cid}")
            assert r.status_code == 204

            r = client.delete(f"/clientes/{cid}")
            assert r.status_code == 404
