from typing import List, Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, func, SmallInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from config import settings

# ==========================================
# 1. CONFIGURAÇÃO DO BANCO (Engine e ORM)
# ==========================================

# Monta a URL de conexão do PostgreSQL
# Montei a string de conexão dinamicamente via f-string em vez de colocar a URL inteira no .env.
# Justificativa: O docker-compose já exige as variáveis atômicas (USER, PASSWORD, DB_NAME) 
# separadas para conseguir inicializar o contêiner do PostgreSQL. 
# Reutilizando essas mesmas variáveis aqui através do config.settings, nós:
# 1. Cumprimos a regra de ZERO hardcode de credenciais no script.
# 2. Aplicamos o princípio DRY (Don't Repeat Yourself), evitando ter que atualizar senhas 
#    em dois lugares diferentes do .env em caso de manutenção.
DATABASE_URL = f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

# Cria o "motor" do banco de dados
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ==========================================
# 2. DEFINIÇÃO DOS MODELOS (As 3 Tabelas)
# ==========================================

class Country(Base):
    __tablename__ = 'countries'
    iso2_code = Column(String(2), primary_key=True)
    iso3_code = Column(String(3))
    name = Column(String(100), nullable=False)
    region = Column(String(80))
    income_group = Column(String(60))
    capital = Column(String(80))
    longitude = Column(Float)
    latitude = Column(Float)
    loaded_at = Column(DateTime, server_default=func.now())

class Indicator(Base):
    __tablename__ = 'indicators'
    indicator_code = Column(String(40), primary_key=True)
    indicator_name = Column(String, nullable=False)
    unit = Column(String(30))

class WdiFact(Base):
    __tablename__ = 'wdi_facts'
    iso2_code = Column(String(2), primary_key=True)
    indicator_code = Column(String(40), primary_key=True)
    year = Column(SmallInteger, primary_key=True)
    value = Column(Float, nullable=True)
    loaded_at = Column(DateTime, server_default=func.now())

# ==========================================
# 3. FUNÇÕES DE CARGA (Com Upsert)
# ==========================================

def load_countries(session, data: List[Dict[str, Any]]):
    """Faz o upsert em lote da tabela countries."""
    if not data:
        return
        
    stmt = pg_insert(Country).values(data)
    # Se der conflito na chave primária (iso2_code), ele atualiza os outros campos
    stmt = stmt.on_conflict_do_update(
        index_elements=['iso2_code'],
        set_={
            "iso3_code": stmt.excluded.iso3_code,
            "name": stmt.excluded.name,
            "region": stmt.excluded.region,
            "income_group": stmt.excluded.income_group,
            "capital": stmt.excluded.capital,
            "longitude": stmt.excluded.longitude,
            "latitude": stmt.excluded.latitude,
            "loaded_at": func.now()
        }
    )
    session.execute(stmt)
    print(f"[load] Tabela 'countries' carregada/atualizada com {len(data)} registros.")

def load_indicators(session, data: List[Dict[str, Any]]):
    """Faz o upsert em lote da tabela indicators."""
    if not data:
        return
        
    stmt = pg_insert(Indicator).values(data)
    stmt = stmt.on_conflict_do_update(
        index_elements=['indicator_code'],
        set_={
            "indicator_name": stmt.excluded.indicator_name,
            "unit": stmt.excluded.unit
        }
    )
    session.execute(stmt)
    print(f"[load] Tabela 'indicators' carregada/atualizada com {len(data)} registros.")

def load_facts(session, data: List[Dict[str, Any]]):
    """Faz o upsert em lote da tabela wdi_facts."""
    if not data:
        return
        
    # O professor proibiu iterar em loop! Mandamos a lista toda de uma vez:
    stmt = pg_insert(WdiFact).values(data)
    
    # Idempotência: Chave primária composta (país, indicador, ano)
    stmt = stmt.on_conflict_do_update(
        index_elements=["iso2_code", "indicator_code", "year"],
        set_={
            "value": stmt.excluded.value, 
            "loaded_at": func.now()
        }
    )
    session.execute(stmt)
    print(f"[load] Tabela 'wdi_facts' carregada/atualizada com {len(data)} registros.")

# ==========================================
# 4. O MAESTRO DA CARGA (Gerencia as transações)
# ==========================================

def load_all_data(countries_data: List[Dict], indicators_data: List[Dict], facts_data: List[Dict]):
    """
    Executa a carga na ordem correta, garantindo o Rollback em caso de erro.
    """
    # A regra do professor: encapsular em with session.begin()
    with SessionLocal() as session:
        with session.begin():
            try:
                print("\n--- Iniciando Carga no Banco de Dados ---")
                
                # Regra atendida: Carga das Dimensões DEVE ocorrer antes dos Fatos (FK)
                load_countries(session, countries_data)
                load_indicators(session, indicators_data)
                
                # Por último, carrega os Fatos
                load_facts(session, facts_data)
                
                print("[load] Carga finalizada com sucesso! Fazendo commit...")
                
            except Exception as e:
                print(f"[load] ERRO CRÍTICO na carga! Fazendo ROLLBACK automático. Detalhes: {e}")
                session.rollback() # Desfaz qualquer alteração parcial
                raise e