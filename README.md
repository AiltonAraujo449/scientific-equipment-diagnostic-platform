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
- Verificação de disponibilidade e prontidão da API.
- Métricas operacionais no formato Prometheus.
- Logs estruturados em JSON com identificadores de correlação.

## Tecnologias

- Python
- FastAPI
- PostgreSQL
- Psycopg
- Docker Compose
- Pytest
- Prometheus Client
- Prometheus Server
- Grafana

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
4. Configure `SEDP_GRAFANA_ADMIN_PASSWORD` no arquivo `.env`,
   utilizando uma senha forte para o administrador do Grafana.

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

Endpoints disponíveis:

- `GET /health` — verifica se a API está respondendo.
- `GET /ready` — verifica a prontidão do serviço e a conexão com PostgreSQL, quando habilitado.
- `POST /diagnostics` — processa eventos e gera um relatório diagnóstico.
- `GET /diagnostics/history` — consulta relatórios com filtros e paginação.
- `GET /diagnostics/history/{report_id}` — recupera um relatório pelo identificador.
- `GET /metrics/` — expõe métricas operacionais no formato Prometheus.
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


## Observabilidade

O SEDP possui instrumentação de observabilidade integrada à API FastAPI.

A implementação utiliza a biblioteca `prometheus-client` para expor métricas operacionais e o módulo `logging` do Python para produzir logs estruturados em JSON.

### Métricas Prometheus

As métricas estão disponíveis em:

`GET http://127.0.0.1:8000/metrics/`

Métricas implementadas:

| Métrica | Descrição |
|---|---|
| `sedp_diagnostics_total` | Quantidade de diagnósticos concluídos, com rótulos de resultado e severidade. |
| `sedp_diagnostic_duration_seconds` | Distribuição do tempo de processamento dos diagnósticos. |
| `sedp_events_ingested_total` | Quantidade de eventos processados com sucesso. |
| `sedp_api_request_duration_seconds` | Distribuição da latência das requisições HTTP. |

Os contadores de diagnósticos e eventos são atualizados após o processamento bem-sucedido e, quando habilitada, a persistência do relatório.

O histograma de duração registra o tempo de execução do endpoint de diagnóstico, incluindo tentativas que terminam em erro.

### Logs estruturados

O SEDP utiliza logs JSON com informações como:

- Timestamp em UTC.
- Nível do log.
- Nome do logger.
- Identificador de correlação (`request_id`).
- Mensagem da operação.

A API aceita o cabeçalho `X-Request-ID` para correlação de requisições. Quando ele não é informado, a aplicação gera um identificador.

### Consultar as métricas

Com a API em execução, utilize o PowerShell:

```powershell
$response = Invoke-WebRequest `
    -Uri "http://127.0.0.1:8000/metrics/" `
    -UseBasicParsing

$response.StatusCode
```

Para consultar as métricas específicas do SEDP:

```powershell
$response.Content -split "`n" |
    Where-Object {
        $_ -match '^sedp_'
    }
```

### Estado da integração

### Infraestrutura de monitoramento

O SEDP utiliza Prometheus e Grafana para coletar, armazenar e visualizar métricas operacionais da API.

A infraestrutura é gerenciada pelo Docker Compose e inclui:

- **PostgreSQL:** persistência do histórico de diagnósticos.
- **Prometheus:** coleta periódica das métricas da API.
- **Grafana:** visualização dos indicadores e dashboards de monitoramento.

#### Iniciar os serviços

Com o Docker Desktop em execução e as variáveis `SEDP_DB_PASSWORD` e `SEDP_GRAFANA_ADMIN_PASSWORD` configuradas no arquivo `.env`, execute:

```powershell
docker compose config --quiet
docker compose up -d
docker compose ps
```

A API FastAPI é executada separadamente no ambiente Python do Windows:

```powershell
python -m uvicorn sedp.api:app --reload
```

O Prometheus utiliza `host.docker.internal:8000` para acessar a API executada no host Windows. Se necessário, ajuste a configuração de rede do servidor de desenvolvimento para permitir a comunicação com o contêiner, mantendo as restrições de firewall apropriadas.

#### Endereços locais

| Serviço | Endereço |
|---|---|
| FastAPI | `http://127.0.0.1:8000/docs` |
| Métricas da API | `http://127.0.0.1:8000/metrics/` |
| Prometheus | `http://127.0.0.1:9090` |
| Grafana | `http://127.0.0.1:3000` |

O Grafana utiliza o usuário administrador configurado no Docker Compose e a senha definida em `SEDP_GRAFANA_ADMIN_PASSWORD`.

#### Dashboard SEDP

O dashboard **SEDP - Scientific Equipment Monitoring** é carregado automaticamente pelo provisionamento do Grafana.

Ele apresenta quatro indicadores:

| Painel | Descrição |
|---|---|
| SEDP API Availability | Disponibilidade da API para coleta pelo Prometheus. |
| Equipment Events Ingested | Quantidade de eventos processados. |
| Diagnostics by Status | Quantidade de diagnósticos agrupados por resultado. |
| Diagnostic Processing Time | Tempo médio de processamento dos diagnósticos contabilizados pela instância. |

Os valores dos contadores Prometheus podem reiniciar quando o processo da API é reiniciado. Eles não representam necessariamente o total histórico armazenado no PostgreSQL.

#### Arquivos de configuração

```text
monitoring/
├── prometheus/
│   └── prometheus.yml
└── grafana/
    ├── dashboards/
    │   └── sedp-monitoring.json
    └── provisioning/
        ├── dashboards/
        │   └── dashboards.yml
        └── datasources/
            └── prometheus.yml
```

O provisionamento automático permite carregar a fonte de dados Prometheus e o dashboard a partir dos arquivos versionados no repositório, sem necessidade de configuração manual em uma nova instalação.

#### Validar a coleta

No Prometheus ou no Grafana Explore, execute:

```promql
up{job="sedp-api"}
```

O valor `1` indica que o Prometheus está conseguindo coletar as métricas da API.

Para consultar diagnósticos agrupados por resultado:

```promql
sum by (outcome) (sedp_diagnostics_total{job="sedp-api"})
```

Para calcular o tempo médio de processamento:

```promql
sedp_diagnostic_duration_seconds_sum{job="sedp-api"}
/
sedp_diagnostic_duration_seconds_count{job="sedp-api"}
```

A infraestrutura foi validada com os quatro painéis funcionando no Grafana.

## Exemplo de diagnóstico

O arquivo `examples/cooling-fault-sequence.json` contém uma sequência de eventos de refrigeração utilizada para testar a identificação de degradação do sistema.

A sequência demonstra como eventos relacionados ao funcionamento da bomba, à redução do fluxo de líquido refrigerante e ao aumento da temperatura podem contribuir para um diagnóstico.


## Estado do projeto

O SEDP possui uma suíte automatizada de testes unitários, funcionais e de integração, incluindo testes de observabilidade.

**Última validação: 51 testes aprovados com PostgreSQL real e integração habilitada.**

A validação contempla:

- Regras de diagnóstico e análise de sequências temporais.
- Priorização de falhas e geração de evidências.
- Geração e serialização de relatórios técnicos.
- Endpoints da API e tratamento de erros.
- Persistência e recuperação de relatórios no PostgreSQL.
- Consulta do histórico com filtros e paginação.
- Verificação de prontidão do serviço.
- Atualização dos contadores Prometheus.
- Exposição das métricas pelo endpoint `/metrics/`.

Resultados da última execução:

| Execução | Resultado |
|---|---|
| Testes específicos de observabilidade | 2 aprovados |
| Suíte padrão | 41 aprovados, 10 ignorados |
| Suíte com PostgreSQL habilitado | 51 aprovados |

A suíte apresentou um aviso de depreciação relacionado à integração entre Starlette e HTTPX, sem falhas nos testes. A atualização dessa dependência permanece como pendência técnica.

### Próximos objetivos

1. Implementar alertas operacionais no Grafana para indisponibilidade da API e aumento de falhas.
2. Ampliar os dashboards com gráficos históricos, taxas de falhas e percentis de latência.
3. Ampliar a cobertura de cenários de falha de equipamentos científicos.
4. Evoluir a análise histórica para identificar tendências e padrões de falha.
5. Avaliar estratégias de manutenção preditiva.

## Segurança

- Não armazene credenciais no código-fonte.
- Mantenha `.env` fora do controle de versão.
- A configuração local do Docker publica a porta do banco somente em `127.0.0.1`.
- Antes de disponibilizar a API em rede, implemente os controles de autenticação, autorização e configuração necessários ao ambiente de destino.
