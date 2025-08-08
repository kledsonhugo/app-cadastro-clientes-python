# API Cadastro de Clientes

Uma API REST simples em Python utilizando FastAPI com CRUD de clientes persistido em SQLite via SQLModel.

## Endpoints

- `GET /clientes`: lista todos os clientes
- `GET /clientes/{id}`: obtém um cliente por id
- `POST /clientes`: cria um cliente
- `PUT /clientes/{id}`: atualiza um cliente
- `DELETE /clientes/{id}`: remove um cliente

## Requisitos

- Python 3.11+ (recomendado 3.12)

## Configuração

Variáveis de ambiente suportadas (opcionais):

- `DATABASE_URL`: URL do banco (default `sqlite:///./clientes.db`)
- `ECHO_SQL`: `true` para logar SQL (default `false`)

Crie um arquivo `.env` na raiz para configurar, por exemplo:

```
DATABASE_URL=sqlite:///./clientes.db
ECHO_SQL=false
```

## Como rodar localmente

1. Crie e ative um ambiente virtual (use `--copies` para evitar problemas de symlink). Se falhar, use uma das alternativas abaixo.

```bash
python3 -m venv --copies .venv
source .venv/bin/activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Rode a API em modo de desenvolvimento (recomendado usar o módulo do Python):

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Acesse a documentação interativa em:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Testes

Execute os testes automatizados seguindo estes passos:

```bash
python -m pytest -q
```

Observação (pytest não encontrado): se aparecer `command not found: pytest`, verifique se o venv está ativo e rode via módulo (`python -m pytest -q`). Se necessário, reinstale as dependências com `pip install -r requirements.txt`.

### Testes cobertos

Os testes exercitam todos os endpoints com cenários de sucesso e falha:

- GET /clientes
	- Lista inicial vazia em um banco novo.
	- Lista com 1 após criação.
- GET /clientes/{id}
	- Retorna o cliente existente (200).
	- Retorna 404 para id inexistente.
- POST /clientes
	- Cria cliente com sucesso (201).
	- Validação 422 para email inválido.
	- 409 conflito quando email já está cadastrado.
- PUT /clientes/{id}
	- Atualiza campos (200) com dados parciais.
	- 404 para id inexistente.
	- 409 conflito ao tentar usar email já existente.
- DELETE /clientes/{id}
	- Remove cliente (204).
	- 404 ao tentar remover novamente ou id inexistente.

Notas de execução dos testes:
- Cada teste usa um banco SQLite temporário (arquivo em diretório temporário) configurado via variável de ambiente `DATABASE_URL`, garantindo isolamento e não interferência em dados reais.
- A aplicação inicializa o engine no ciclo de vida (`lifespan`), com descarte no shutdown, evitando travas de arquivo.
- O pytest está configurado no `pyproject.toml` para suprimir warnings de terceiros irrelevantes e incluir a raiz no `PYTHONPATH`.



## CI

Um workflow GitHub Actions (`.github/workflows/ci.yml`) executa lint, format-check e testes a cada push/PR.
