# SellFlow

Sistema de gestao de vendas e estoque para farmacias. O projeto possui uma API
FastAPI, persistencia com SQLAlchemy, migrations com Alembic, SQL Server para
o ambiente integrado e um modo local com SQLite para a aplicacao desktop.

## Visao geral

O fluxo principal da aplicacao e:

1. O usuario chama a API ou utiliza a interface desktop.
2. A camada de entrada valida os dados com schemas Pydantic.
3. Uma sessao SQLAlchemy e aberta para consultar ou alterar o banco.
4. As regras de negocio validam categorias, produtos, usuarios, lotes,
	 validade e saldo de estoque.
5. A operacao e confirmada com `commit()` ou desfeita com `rollback()` quando
	 ocorre um erro de integridade.
6. A resposta e devolvida em JSON pela API ou refletida na tela desktop.

Componentes do repositorio:

| Caminho | Responsabilidade |
| --- | --- |
| `app/main.py` | Cria a aplicacao FastAPI e registra as rotas. |
| `app/api/` | Endpoints de saude, catalogo e operacao. |
| `app/models/` | Modelos SQLAlchemy que representam as tabelas. |
| `app/schemas/` | Validacao e formato das entradas e respostas da API. |
| `app/database/` | Engine, sessoes, Base declarativa e dependencias. |
| `app/messaging/` | Conexao com RabbitMQ. |
| `database/migrations/` | Configuracao e historico de migrations Alembic. |
| `desktop_sellflow.py` | Interface desktop local com PySide6. |
| `run_sellflow.py` | Inicializador da API local e abertura do navegador. |
| `worker/` | Reservado para consumidores de mensagens; atualmente vazio. |

## Requisitos

- Python 3.10 ou superior.
- Docker Desktop, caso sejam usados SQL Server e RabbitMQ em containers.
- O ODBC Driver 18 for SQL Server para o modo integrado.
- Dependencias listadas em `requirements.txt`.

Instalacao no Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Infraestrutura com Docker

Suba os servicos:

```powershell
docker compose up -d
```

O `docker-compose.yml` inicia:

- **SQL Server** em `localhost:1433`, com volume persistente
	`sqlserver_data`.
- **RabbitMQ** em `localhost:5672`, com volume persistente
	`rabbitmq_data`.
- **RabbitMQ Management** em `http://localhost:15672`.

O SQL Server do compose usa o usuario `sa` e a senha definida no proprio
arquivo. Em um ambiente real, essa senha deve ser substituida por segredo de
ambiente e nao deve ser versionada.

Para parar os containers sem remover os dados:

```powershell
docker compose stop
```

Para remover containers e volumes, apagando os dados locais:

```powershell
docker compose down -v
```

## Configuracao do banco

As configuracoes sao lidas do arquivo `.env` por `pydantic-settings`. O projeto
aceita estas variaveis:

```dotenv
DATABASE_SERVER=localhost
DATABASE_PORT=1433
DATABASE_NAME=sellflow
DATABASE_USER=sa
DATABASE_PASSWORD=SuaSenha
STANDALONE_MODE=false
STANDALONE_DATA_DIR=./data
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
```

### Modo integrado: SQL Server

Com `STANDALONE_MODE=false`, o engine usa SQLAlchemy com o driver
`mssql+pyodbc` e o ODBC Driver 18. O banco precisa existir antes da aplicacao
ser iniciada. A estrutura deve ser criada pelas migrations:

```powershell
alembic upgrade head
```

O arquivo `alembic.ini` aponta para `database/migrations`. A URL generica no
INI nao e usada diretamente: `database/migrations/env.py` monta a conexao a
partir das variaveis `DATABASE_*`.

### Modo local: SQLite

Com `STANDALONE_MODE=true`, o projeto cria um arquivo SQLite em
`STANDALONE_DATA_DIR\sellflow.db`. Se o diretorio nao for informado, usa
`data\sellflow.db` no diretorio atual.

Nesse modo, a API chama `Base.metadata.create_all()` na inicializacao e o
desktop tambem cria as tabelas ao abrir. Portanto, o modo local nao aplica o
historico do Alembic; ele cria a estrutura diretamente a partir dos modelos
SQLAlchemy.

## Como o SQL funciona

O SQLAlchemy e a camada que traduz objetos Python e consultas para SQL. Cada
requisicao que usa banco recebe uma sessao por meio de `get_session()`:

1. `SessionLocal()` abre uma sessao ligada ao engine.
2. O endpoint consulta ou adiciona objetos SQLAlchemy.
3. `session.commit()` grava a transacao.
4. Em caso de erro tratado, `session.rollback()` desfaz a transacao.
5. O bloco `finally` fecha a sessao.

As tabelas principais sao:

- `categorias`: categorias dos produtos.
- `produtos`: cadastro, precos, dados farmaceuticos e status ativo.
- `usuarios`: usuarios, perfis e senha armazenada como hash.
- `clientes`: dados do cliente.
- `lotes`: estoque separado por produto, lote, validade e localizacao.
- `movimentacoes_estoque`: historico de entradas e saidas.
- `compras` e `compra_itens`: entradas de mercadoria.
- `orcamentos` e `orcamento_itens`: propostas comerciais.
- `vendas` e `venda_itens`: vendas finalizadas.

As chaves estrangeiras preservam as relacoes, por exemplo, um produto aponta
para uma categoria e um lote aponta para um produto. Valores monetarios usam
`Numeric`, evitando calculos financeiros com `float`.

### Migrations

As migrations sao a forma recomendada de atualizar o SQL Server compartilhado.
A cadeia atual e:

1. `37740bdad66a_cria_tabela_de_categorias.py`: cria `categorias`.
2. `49794418a1d1_cria_tabela_de_produtos.py`: cria `produtos` e sua relacao
	 com `categorias`.
3. `8a1c2d3e4f5a_cria_operacao_sellflow.py`: cria usuarios, clientes, lotes,
	 estoque, compras, orcamentos e vendas.

Uma nova alteracao de estrutura deve gerar uma nova migration e ser enviada ao
Git junto com o codigo que depende dela:

```powershell
alembic revision --autogenerate -m "descreve a alteracao"
alembic upgrade head
```

Antes de aceitar uma migration gerada automaticamente, revise o arquivo para
confirmar chaves, indices, nulabilidade e operacoes de `downgrade`.

## Regras de negocio por etapa

### Catalogo

- Categorias podem ser criadas e listadas.
- O nome da categoria e unico.
- Um produto precisa apontar para uma categoria existente.
- O codigo de barras, quando informado, e unico.
- Produto nao e apagado fisicamente: o endpoint de exclusao marca `ativo` como
	`false`.
- A listagem de produtos aceita o filtro `ativos=true` ou `ativos=false`.

### Usuarios e clientes

- Perfis aceitos: `administrador`, `gerente` e `operador`.
- E-mails sao normalizados para minusculas e nao podem se repetir.
- A senha nunca e salva em texto puro; `hash_password()` gera o hash.
- CPF/CNPJ, quando informado, e unico.

### Estoque e lotes

- Um lote precisa de um produto existente.
- A validade nao pode estar no passado ao cadastrar o lote.
- O cadastro inicial cria uma movimentacao de estoque do tipo `entrada`.
- Compras aumentam a quantidade do lote e registram outra entrada.
- O estoque e controlado por lote, e nao apenas por produto.

### Venda

Ao finalizar uma venda, a API:

1. Confirma que o usuario existe e esta ativo.
2. Confirma o cliente, quando informado.
3. Confirma que cada produto esta ativo.
4. Busca lotes com saldo positivo e validade vigente.
5. Ordena os lotes pela validade mais proxima, usando primeiro o lote que
	 vence antes.
6. Diminui o saldo dos lotes ate atender a quantidade solicitada.
7. Cria os itens da venda e movimentacoes do tipo `saida`.
8. Calcula o total com o preco de venda do produto e confirma a transacao.

Se o saldo valido for insuficiente, a venda e rejeitada e o banco nao deve ser
confirmado.

## API

Inicie a API com:

```powershell
uvicorn app.main:app --reload
```

Documentacao interativa:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Rotas principais:

| Metodo | Rota | Funcao |
| --- | --- | --- |
| `GET` | `/health` | Verifica API, banco e RabbitMQ. |
| `POST/GET` | `/categorias` | Cria e lista categorias. |
| `GET` | `/categorias/{id}` | Consulta uma categoria. |
| `POST/GET` | `/produtos` | Cria e lista produtos. |
| `GET` | `/produtos/{id}` | Consulta um produto. |
| `PUT` | `/produtos/{id}` | Atualiza um produto. |
| `DELETE` | `/produtos/{id}` | Desativa um produto. |
| `POST/GET` | `/usuarios` | Cria e lista usuarios. |
| `POST/GET` | `/clientes` | Cria e lista clientes. |
| `POST/GET` | `/lotes` | Cadastra e lista lotes. |
| `POST` | `/compras` | Registra entrada de compra. |
| `POST/GET` | `/orcamentos` | Cria e lista orcamentos. |
| `POST/GET` | `/vendas` | Finaliza e lista vendas. |
| `GET` | `/relatorios/resumo` | Retorna indicadores de vendas e estoque. |

## RabbitMQ e mensageria

RabbitMQ e o broker de mensagens do projeto. O container expoe a porta AMQP
`5672` para aplicacoes e a porta `15672` para o painel de gerenciamento.

Atualmente, a implementacao esta na etapa de infraestrutura/conectividade:

- `app/messaging/rabbitmq.py` cria uma conexao `pika.BlockingConnection` com
	`RABBITMQ_HOST` e `RABBITMQ_PORT`.
- `GET /health` abre uma conexao, confirma que o broker responde e fecha a
	conexao imediatamente.
- Nao ha exchange, fila, routing key, produtor ou consumidor implementado.
- O diretorio `worker/` esta reservado, mas ainda nao possui um worker.
- As operacoes de venda, compra e estoque sao sincronas: elas gravam
	diretamente no banco durante a requisicao HTTP.

Isso significa que, no estado atual, RabbitMQ nao processa vendas em segundo
plano e nao participa da confirmacao das transacoes. Para implementar a
mensageria sera necessario definir contratos de evento, por exemplo
`venda.finalizada` e `estoque.movimentado`, criar exchanges e filas, publicar
as mensagens apos a transacao do banco e criar consumidores idempotentes no
worker. O consumidor tambem precisara confirmar (`ack`) apenas depois de
processar a mensagem e tratar mensagens rejeitadas ou reenfileiradas.

## Aplicacao desktop

Para executar a interface local:

```powershell
python desktop_sellflow.py
```

O desktop usa SQLite, executa localmente na maquina e oferece telas de
dashboard, produtos, clientes, lotes, vendas e usuarios. Ele acessa os mesmos
modelos SQLAlchemy, mas nao usa a API HTTP nem RabbitMQ.

Tambem existe um inicializador que sobe a API em modo local e abre o Swagger:

```powershell
python run_sellflow.py
```

Os dados locais ficam em `%LOCALAPPDATA%\SellFlow\sellflow.db`.

## Health check

`GET /health` retorna o estado da API e tenta executar `SELECT 1` no banco. Em
seguida, testa uma conexao AMQP com RabbitMQ. Um exemplo de resposta e:

```json
{
	"status": "ok",
	"service": "sellflow-api",
	"database": "connected",
	"rabbitmq": "connected"
}
```

O campo `status` representa a disponibilidade da API; os campos `database` e
`rabbitmq` mostram individualmente a conectividade dos servicos.

## Build do instalador

O projeto possui `SellFlow.spec`, `installer.iss` e scripts PowerShell para a
geracao do executavel e do instalador Windows. O fluxo geral e:

```powershell
./build_installer.ps1
```

Consulte `COMO GERAR O INSTALADOR.txt` para os detalhes especificos do
ambiente de build.

## Boas praticas de versionamento

Devem ser versionados:

- codigo da aplicacao;
- `requirements.txt`;
- `alembic.ini`;
- `database/migrations/`;
- arquivos de configuracao e scripts necessarios ao build.

Nao devem ser versionados:

- `.env` com senhas;
- banco SQLite local;
- dados dos volumes Docker;
- ambientes virtuais e arquivos gerados de build.

Ao alterar tabelas, envie a migration junto com o codigo. Sem a migration, um
ambiente novo nao conseguira reproduzir a mesma estrutura de banco.