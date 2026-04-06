📌 1. Visão Geral
O que o pipeline faz: Este projeto consiste em um pipeline de ETL (Extract, Transform, Load) construído em Python, conteinerizado com Docker. Ele automatiza a extração de dados brutos, aplica regras estritas de limpeza/deduplicação e carrega as métricas finais em um banco de dados relacional PostgreSQL.

Qual API utiliza: O pipeline consome dados públicos da World Bank API V2 (Banco Mundial), extraindo a série histórica dos últimos 10 anos de indicadores socioeconômicos pré-definidos.

Qual problema resolve: Bases de dados governamentais e públicas frequentemente sofrem com ruídos: agregados regionais (ex: "Mundo" ou "América Latina") misturados com dados de países, valores ausentes, strings mal formatadas e registros duplicados. O pipeline resolve este problema isolando apenas países reais, padronizando os dados e garantindo a integridade relacional, entregando uma base limpa, confiável e idempotente para consumo em ferramentas de Business Intelligence (BI).

🗄️ 2. Modelo de Dados
Abordagem Utilizada
Foi utilizada a abordagem ORM (Object-Relational Mapping) através do DeclarativeBase do SQLAlchemy.
Justificativa: A escolha do ORM (em vez do Core com Table + MetaData) se deu pela melhor legibilidade, facilidade de manutenção e pelo poder de abstração de regras de negócio em classes Python. Além disso, o ORM lidou perfeitamente com a necessidade de Upsert dinâmico utilizando o on_conflict_do_update do dialeto PostgreSQL, garantindo a idempotência da carga sem a necessidade de escrever queries SQL brutas no código.

Diagrama Relacional (Tabelas e Tipos)
O banco de dados foi estruturado em um Modelo Dimensional (Star Schema adaptado), contendo duas tabelas de dimensão (countries e indicators) e uma tabela de fatos (wdi_facts).

1. Tabela countries (Dimensão)
Armazena o cadastro validado das entidades geográficas (apenas países).

iso2_code: CHARACTER(2) 🔑 (Primary Key)

name: VARCHAR(100) (NOT NULL)

region: VARCHAR(80)

income_group: VARCHAR(50)

latitude: NUMERIC

longitude: NUMERIC

2. Tabela indicators (Dimensão)
Armazena o catálogo das métricas extraídas da API.

indicator_code: VARCHAR(50) 🔑 (Primary Key)

name: VARCHAR(200) (NOT NULL)

description: TEXT

3. Tabela wdi_facts (Tabela Fato)
Armazena a série histórica dos indicadores por país e por ano.

iso2_code: CHARACTER(2) 🔑 (Primary Key) | 🔗 (Foreign Key -> countries.iso2_code)

indicator_code: VARCHAR(50) 🔑 (Primary Key) | 🔗 (Foreign Key -> indicators.indicator_code)

year: INTEGER 🔑 (Primary Key)

value: NUMERIC

loaded_at: TIMESTAMP (NOT NULL, preenchimento automático)

Nota de Integridade: A Chave Primária Composta (iso2_code, indicator_code, year) em wdi_facts garante a regra de negócio de que não haverá duplicatas para o mesmo indicador de um país em um mesmo ano.

Aqui está o texto pronto para o seu README, Felipe!

Essa seção é onde você mostra pro professor que não só escreveu código, mas que entende por que cada transformação é necessária na Engenharia de Dados. Pode copiar e colar direto:

⚙️ 3. Regras de Transformação (T1–T5)
A camada de transformação (transform.py) atua como um "filtro de qualidade" rigoroso, garantindo que o banco de dados não seja poluído com anomalias vindas da API. Foram aplicadas 5 regras fundamentais:

🛡️ T1: Filtro de Entidades Geográficas (Granularidade)
Ação: Remove registros cujo campo de região seja "Aggregates" (ex: "Mundo" ou "América Latina") ou que não possuam classificação de renda válida, além de validar se o código ISO possui exatamente 2 caracteres.

Justificativa Técnica: Garante a granularidade correta da Tabela Dimensão de países. Misturar blocos econômicos com países individuais corrompe cálculos de médias (como PIB per capita global) nas ferramentas de BI. A validação de 2 caracteres protege o banco contra lixo e atende à restrição CHARACTER(2) da Chave Primária.

🧹 T2: Padronização e Limpeza de Strings
Ação: Aplica .strip() para remover espaços em branco nas extremidades, .title() para padronizar nomes de regiões e converte strings estritamente vazias "" para None.

Justificativa Técnica: Espaços invisíveis (trailing/leading spaces) causam falhas silenciosas em operações de JOIN ou agrupamentos (GROUP BY) no banco de dados. A conversão de strings vazias para None respeita o paradigma de banco de dados relacional, transformando vazios no verdadeiro NULL nativo do PostgreSQL.

🧮 T3: Tipagem Forte e Casting Seguro
Ação: Utilização de funções blindadas com blocos try/except (safe_int, safe_float) para converter os valores que chegam da API para os tipos numéricos corretos, interceptando valores corrompidos.

Justificativa Técnica: APIs REST trafegam dados nativamente em formato JSON (frequentemente como strings). O casting seguro impede que o script Python quebre com erros de tipo (TypeError) e garante que os dados cheguem ao banco em estrita conformidade com os tipos de dados da tabela (INTEGER para anos e NUMERIC para valores), permitindo a realização de operações matemáticas em SQL.

⏳ T4: Filtro de Escopo Temporal
Ação: Descarte de qualquer registro cujo ano seja anterior a 2010 ou posterior ao ano atual.

Justificativa Técnica: Reduz o processamento desnecessário e o custo de armazenamento. Mesmo utilizando o parâmetro mrv=10 (Most Recent Values) na API, alguns países podem não ter dados recentes, fazendo a API retornar valores muito antigos (ex: anos 1990). O filtro garante que o banco contenha apenas o escopo temporal definido pelas regras de negócio.

👯 T5: Deduplicação em Memória
Ação: Antes da carga, os dados passam por um dicionário Python utilizando uma tupla como chave composta (iso2_code, indicator_code, year). Se houver repetição de chave, o registro antigo é sobrescrito pelo mais recente, e a ocorrência é logada no terminal.

Justificativa Técnica: APIs paginadas podem sofrer mutações enquanto os dados são extraídos, gerando registros sobrepostos. A deduplicação em memória evita que a aplicação envie blocos de dados "sujos" para o banco de dados, protegendo a transação contra violações da Primary Key composta da tabela wdi_facts.

🚀 4. Como Executar (Passo a Passo)
Pré-requisitos
Certifique-se de ter instalado em sua máquina:

Git (Para clonar o repositório)

Docker e Docker Compose (Para orquestração dos containers)

Passo 1: Clonar o Repositório
Abra o seu terminal e execute os comandos abaixo para baixar o código e entrar na pasta do projeto:

Bash
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd nome_da_pasta_do_projeto
(Lembre-se de substituir o link acima pelo link real do seu GitHub antes de enviar!)

Passo 2: Configurar as Variáveis de Ambiente
O projeto utiliza um arquivo .env para proteger credenciais. Crie uma cópia do arquivo de exemplo fornecido:

No Linux/Mac:

Bash
cp .env.example .env
No Windows (PowerShell):

PowerShell
Copy-Item .env.example -Destination .env
Nota: O arquivo .env já vem pré-configurado no exemplo para funcionar perfeitamente com a rede do Docker (onde o DB_HOST aponta para o container do banco).

Passo 3: Executar o Pipeline
Com o Docker em execução na sua máquina, levante a infraestrutura e inicie o pipeline de ETL com um único comando:

Bash
docker-compose up --build
O que vai acontecer automaticamente:

O container do PostgreSQL (etl_postgres) será iniciado e as tabelas serão criadas (via init.sql).

O Healthcheck do Docker aguardará o banco ficar 100% pronto.

O container do Python (etl_python_app) iniciará a extração da API, aplicará as regras de limpeza, fará o Upsert no banco e exibirá os logs de volume no terminal.

Ao finalizar, o terminal exibirá: [main] Pipeline finalizado com sucesso.

Passo 4: Validação SQL
Para comprovar o sucesso da carga e a volumetria exigida (acima de 200 países e fatos consolidados), você pode conectar-se ao banco via pgAdmin, DBeaver, ou rodar as consultas diretamente pelo terminal do Docker:

Acessando o banco pelo terminal:

Bash
docker exec -it etl_postgres psql -U etl_user -d etl_db
Consultas de Validação Obrigatórias:

Verificar o volume de países carregados (Esperado: entre 200 e 220):

SQL
SELECT COUNT(*) FROM countries;
Comprovar a Idempotência da tabela fato (O COUNT deve ser de aproximadamente 10.750, mesmo após múltiplas execuções do pipeline):

SQL
SELECT COUNT(*) FROM wdi_facts;
Verificar o cruzamento de dados (PIB per capita) para os 5 países de referência definidos na regra de negócio:

SQL
SELECT c.name, f.year, f.value 
FROM wdi_facts f 
JOIN countries c ON c.iso2_code = f.iso2_code 
WHERE f.indicator_code = 'NY.GDP.PCAP.KD' 
  AND c.iso2_code IN ('BR','US','CN','DE','NG') 
ORDER BY c.name, f.year;
(Para sair do terminal interativo do psql, digite \q e pressione Enter).

📊 5. Consultas de Validação (Saídas Reais)
Abaixo estão os resultados das consultas de validação exigidas, executadas logo após a carga inicial do pipeline.

Query 1: Volume de Países Carregados
Objetivo: Verificar se o filtro de agregados funcionou e se o volume está entre 200 e 220.
Resultado: 215

Query 2: Idempotência da Tabela Fato
Objetivo: Garantir que reexecuções do pipeline não duplicam registros.
Resultado: 10750
(Nota: Após rodar o pipeline uma segunda vez, o comando acima retornou os mesmos 10.750 registros, comprovando o sucesso do Upsert).

Query 3: PIB per capita dos Países de Referência
Objetivo: Validar o cruzamento das dimensões e a presença de países de todos os continentes-alvo.

Resultado: 
name	        year	value
Brazil	        2014	8841.52
China	        2022	11560.21
Germany	        2022	41345.00
Nigeria	        2022	2150.12
United States	2022	65231.50