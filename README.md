# Scientific Equipment Diagnostic Platform (SEDP)

Plataforma de diagnóstico de equipamentos científicos que analisa eventos, identifica possíveis falhas e gera relatórios técnicos com evidências e ações recomendadas.

O projeto é um portfólio de engenharia de software voltado para diagnóstico assistido, histórico de falhas e futuras capacidades de manutenção preditiva.

## Funcionalidades

- Ingestão e análise de eventos de equipamentos.
- Diagnóstico baseado em regras e sequências temporais.
- Evidências para explicar os diagnósticos.
- API REST com FastAPI.
- Persistência de relatórios em PostgreSQL.
- Consulta do histórico por equipamento e código de falha.
- Testes unitários e de integração.

## Tecnologias

- Python
- FastAPI
- PostgreSQL
- Psycopg
- Docker Compose
- Pytest

## Pré-requisitos

- Python compatível com a versão declarada em `pyproject.toml`.
- Docker Desktop com Docker Compose.
- PowerShell no Windows.

## Configuração

1. Configure a variável `SEDP_DB_PASSWORD` no arquivo `.env`, na raiz do projeto. Utilize uma senha forte e não a compartilhe.
2. Configure também:

   - `SEDP_DB_ENABLED=true`
   - `SEDP_DB_HOST=localhost`
   - `SEDP_DB_PORT=5432`
   - `SEDP_DB_NAME=sedp`
   - `SEDP_DB_USER=sedp_user`

3. Confirme que `.env` permanece ignorado pelo Git.

Não versione o arquivo `.env` nem credenciais reais.

## Instalar dependências

Na raiz do projeto, crie e ative o ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o Python Launcher (`py`) não estiver disponível, utilize `python -m venv .venv`.

Atualize o instalador e instale o projeto com as dependências de desenvolvimento:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Iniciar o PostgreSQL

```powershell
docker compose up -d db
docker compose ps
```

Confirme que o banco está pronto:

```powershell
docker exec sedp-postgres pg_isready -U sedp_user -d sedp
```

## Inicializar o banco

Com o ambiente virtual ativado e as variáveis de ambiente configuradas:

```powershell
python -c "from sedp.repository import initialize_database; initialize_database()"
```

Esse comando cria a tabela de histórico caso ela ainda não exista.

## Executar a API

```powershell
uvicorn sedp.api:app --reload
```

Endpoints úteis:

- `GET /health` — verifica a API.
- `POST /diagnostics` — executa um diagnóstico.
- `GET /diagnostics/history` — consulta o histórico.
- `GET /docs` — documentação interativa da API.

Com a API em execução, acesse `http://127.0.0.1:8000/docs`.

## Executar os testes

Testes comuns:

```powershell
pytest -q
```

Testes de integração com PostgreSQL:

```powershell
$env:SEDP_RUN_DB_TESTS = "1"
try {
    pytest -q
}
finally {
    Remove-Item Env:SEDP_RUN_DB_TESTS -ErrorAction SilentlyContinue
}
```

Os testes de integração exigem um PostgreSQL acessível e as variáveis de ambiente corretas.

## Exemplo de diagnóstico

O arquivo `examples/cooling-fault-sequence.json` contém uma sequência de eventos de refrigeração utilizada para testar a identificação de degradação do sistema.

A sequência demonstra como eventos relacionados ao funcionamento da bomba, à redução do fluxo de líquido refrigerante e ao aumento da temperatura podem contribuir para um diagnóstico.

## Estado do projeto

A integração com PostgreSQL foi validada com **46 testes aprovados**, executados com os testes de integração habilitados e o banco real acessível. A evolução do projeto inclui ampliar a cobertura de falhas, aprimorar a observabilidade e avaliar estratégias de manutenção preditiva.

## Segurança

- Não armazene credenciais no código-fonte.
- Mantenha `.env` fora do controle de versão.
- A configuração local do Docker publica a porta do banco somente em `127.0.0.1`.
- Antes de disponibilizar a API em rede, implemente os controles de autenticação, autorização e configuração necessários ao ambiente de destino.
