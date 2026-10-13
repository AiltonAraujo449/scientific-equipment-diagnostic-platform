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

## Fluxo integrado de diagnóstico

O SEDP conecta a análise de eventos de equipamentos à geração de relatórios técnicos e à persistência do histórico de diagnósticos.

O fluxo de processamento é:

1. **Ingestão:** recebe eventos do equipamento, incluindo timestamps, subsistemas, componentes, códigos de evento e valores medidos.
2. **Diagnóstico:** aplica regras e analisa sequências temporais para identificar possíveis falhas.
3. **Geração do relatório:** consolida o resultado, a prioridade, a confiança, as evidências e as ações recomendadas.
4. **Persistência:** armazena o relatório no PostgreSQL quando a persistência está habilitada.
5. **Consulta do histórico:** permite recuperar relatórios por identificador e consultar registros com filtros e paginação.

A sequência de falha de refrigeração em `examples/cooling-fault-sequence.json` demonstra como eventos relacionados à bomba, à redução do fluxo de líquido refrigerante e ao aumento da temperatura podem ser correlacionados para produzir um diagnóstico explicável.

A integração é validada por testes automatizados da API e do repositório, incluindo persistência, recuperação, filtragem e paginação dos relatórios.

## Exemplo de diagnóstico

O arquivo `examples/cooling-fault-sequence.json` contém uma sequência de eventos de refrigeração utilizada para testar a identificação de degradação do sistema.

A sequência demonstra como eventos relacionados ao funcionamento da bomba, à redução do fluxo de líquido refrigerante e ao aumento da temperatura podem contribuir para um diagnóstico.

## Estado do projeto

O SEDP possui uma suíte automatizada de testes unitários, funcionais e de integração.

**Última validação:** 49 testes aprovados com os testes de integração habilitados e o PostgreSQL real acessível.

A validação contempla:

- Regras de diagnóstico e análise de sequências temporais de falhas.
- Geração e serialização de relatórios técnicos.
- Endpoints da API e tratamento de erros.
- Persistência e recuperação de relatórios no PostgreSQL.
- Consulta do histórico com filtros e paginação.
- Verificação de prontidão do serviço.

A execução padrão, sem habilitar os testes de integração com banco de dados, apresentou 39 testes aprovados e 10 ignorados. Com `SEDP_RUN_DB_TESTS=1`, os 49 testes foram aprovados.

A suíte apresentou um aviso de depreciação relacionado à integração entre Starlette e HTTPX, que permanece como pendência técnica para avaliação.

Próximos objetivos: aprimorar a observabilidade, ampliar a cobertura de cenários de falha e avaliar estratégias de manutenção preditiva.

## Segurança

- Não armazene credenciais no código-fonte.
- Mantenha `.env` fora do controle de versão.
- A configuração local do Docker publica a porta do banco somente em `127.0.0.1`.
- Antes de disponibilizar a API em rede, implemente os controles de autenticação, autorização e configuração necessários ao ambiente de destino.
