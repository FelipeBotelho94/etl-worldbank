# 🌍 ETL Pipeline — World Bank Indicators

Pipeline ETL completo que extrai indicadores socioeconômicos da API pública do Banco Mundial, transforma e carrega em um banco PostgreSQL estruturado — pronto para análises comparativas entre países da América Latina, Europa e Ásia.

---

## 📋 Visão Geral

| Item | Detalhe |
|---|---|
| Fonte | World Bank Data API v2 (api.worldbank.org) |
| Destino | PostgreSQL (3 tabelas relacionais) |
| Orquestração | Python modular (extract → transform → load) |
| Ambiente | Docker + Docker Compose |
| Indicadores | PIB per capita, População, Saúde, Educação, Eletricidade |

**Problema resolvido:** automatizar a coleta e estruturação de dados de desenvolvimento econômico de mais de 200 países, com pipeline idempotente e reexecutável sem duplicação.

---

## 🗄️ Modelo de Dados

```
┌─────────────────────────┐       ┌──────────────────────────┐
│        countries        │       │        indicators        │
├─────────────────────────┤       ├──────────────────────────┤
│ iso2_code  CHAR(2) PK   │       │ indicator_code  VARCHAR PK│
│ iso3_code  CHAR(3)      │       │ indicator_name  TEXT      │
│ name       VARCHAR      │       │ unit            VARCHAR   │
│ region     VARCHAR      │       └────────────┬─────────────┘
│ income_group VARCHAR    │                    │
│ capital    VARCHAR      │       ┌────────────▼─────────────┐
│ longitude  NUMERIC      │       │         wdi_facts        │
│ latitude   NUMERIC      │       ├──────────────────────────┤
│ loaded_at  TIMESTAMP    │       │ iso2_code  CHAR(2)  FK   │
└──────────┬──────────────┘       │ indicator_code      FK   │
           │                      │ year       SMALLINT      │
           └──────────────────────│ value      NUMERIC       │
                                  │ loaded_at  TIMESTAMP     │
                                  │ PK (iso2, indicator,year)│
                                  └──────────────────────────┘
```

**Abordagem ORM:** foi utilizado `DeclarativeBase` do SQLAlchemy, que oferece mapeamento explícito entre classes Python e tabelas, facilitando o upsert tipado e a manutenção do código.

---

## ⚙️ Indicadores Extraídos

| Código WDI | Indicador | Unidade |
|---|---|---|
| NY.GDP.PCAP.KD | PIB per capita (USD constante 2015) | USD |
| SP.POP.TOTL | População total | Pessoas |
| SH.XPD.CHEX.GD.ZS | Gasto em saúde (% do PIB) | % PIB |
| SE.XPD.TOTL.GD.ZS | Gasto em educação (% do PIB) | % PIB |
| EG.ELC.ACCS.ZS | Acesso à eletricidade (% da população) | % |

---

## 🔄 Regras de Transformação

| Regra | Descrição |
|---|---|
| **T1 — Filtro de entidade** | Remove agregados regionais — mantém apenas países com ISO2 de exatamente 2 caracteres |
| **T2 — Limpeza de strings** | Aplica `strip()` em campos de texto, substitui strings vazias por `None`, padroniza regiões em title-case |
| **T3 — Conversão de tipos** | Converte `year` para `int` e `value` para `float` com `try/except`, retornando `None` em falha |
| **T4 — Filtro temporal** | Mantém apenas registros com `year` entre 2010 e o ano corrente |
| **T5 — Deduplicação** | Remove duplicatas por `(iso2, indicator_code, year)` mantendo o registro mais recente, com log da quantidade removida |

---

## 🚀 Como Executar

### Pré-requisitos
- Docker 24+
- Docker Compose

### 1. Clone o repositório
```bash
git clone https://github.com/FelipeBotelho94/etl-worldbank
cd etl-worldbank
```

### 2. Configure as variáveis de ambiente
```bash
cp .env.example .env
# edite o .env com suas credenciais do banco
```

### 3. Suba o ambiente
```bash
docker-compose up --build
```

O pipeline executa automaticamente ao subir. O PostgreSQL é inicializado com o DDL em `db/init.sql` antes da execução do ETL.

---

## ✅ Consultas de Validação

### Volume de países carregados
```sql
SELECT COUNT(*) FROM countries;
-- Resultado: 214 países
```

### Distribuição por grupo de renda
```sql
SELECT income_group, COUNT(*)
FROM countries
GROUP BY income_group
ORDER BY 2 DESC;
```

### Volume e nulos por indicador
```sql
SELECT indicator_code, COUNT(*) as obs,
       SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) as nulls
FROM wdi_facts
GROUP BY indicator_code;
```

### PIB per capita — países de referência
```sql
SELECT c.name, f.year, f.value
FROM wdi_facts f
JOIN countries c ON c.iso2_code = f.iso2_code
WHERE f.indicator_code = 'NY.GDP.PCAP.KD'
  AND c.iso2_code IN ('BR','US','CN','DE','NG')
ORDER BY c.name, f.year;
```

### Idempotência
```sql
-- Execute o pipeline duas vezes e compare:
SELECT COUNT(*) FROM wdi_facts;
-- O resultado deve ser idêntico nas duas execuções
```

---

## 📁 Estrutura do Projeto

```
etl_worldbank/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
├── db/
│   └── init.sql          # DDL das 3 tabelas
└── src/
    ├── __init__.py
    ├── config.py          # Parâmetros e variáveis de ambiente
    ├── extract.py         # Chamadas à API com paginação e retry
    ├── transform.py       # Regras T1–T5
    ├── load.py            # Upsert nas 3 tabelas via SQLAlchemy
    └── main.py            # Orquestração do pipeline
```

---

## 🔧 Decisões Técnicas

- **SQLAlchemy ORM** foi escolhido sobre psycopg2 direto pela tipagem explícita, facilidade de upsert com `on_conflict_do_update` e rollback automático via `session.begin()`
- **Retry com backoff** implementado na extração para lidar com instabilidades da API do Banco Mundial
- **Inserção em lote** via `bulk_insert_mappings()` para performance — evita loop de inserts individuais
- **Ordem de carga** respeitada: `countries` → `indicators` → `wdi_facts` para garantir integridade referencial das FKs
- **Valores nulos** tratados explicitamente na transformação — o pipeline nunca aborta por `value: null` na API

---

## 👨‍💻 Autor

**Felipe Botelho** — [LinkedIn](https://www.linkedin.com/in/felipe-botelho-451418180/) · [GitHub](https://github.com/FelipeBotelho94)

Estudante de Sistemas de Informação — ESPM
