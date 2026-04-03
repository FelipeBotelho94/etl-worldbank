from extract import fetch_countries, extract_all_indicators
from transform import transform_all_countries, transform_all_facts, get_indicators_table
from load import load_all_data

def run_etl() -> None:
    print("[main] Iniciando pipeline ETL do Banco Mundial...")
    
    # ==========================================
    # 1. EXTRAÇÃO (E)
    # ==========================================
    print("\n--- ETAPA 1: EXTRAÇÃO ---")
    raw_countries = fetch_countries()
    raw_indicators = extract_all_indicators()
    
    # ==========================================
    # 2. TRANSFORMAÇÃO (T)
    # ==========================================
    print("\n--- ETAPA 2: TRANSFORMAÇÃO ---")
    transformed_countries = transform_all_countries(raw_countries)
    transformed_facts = transform_all_facts(raw_indicators)
    transformed_indicators = get_indicators_table() # Puxa a lista fixa de 5 indicadores
    
    # ==========================================
    # 3. CARGA (L)
    # ==========================================
    print("\n--- ETAPA 3: CARGA ---")
    # Enviamos as 3 listas limpas para o orquestrador do banco de dados
    load_all_data(
        countries_data=transformed_countries,
        indicators_data=transformed_indicators,
        facts_data=transformed_facts
    )
    
    print("\n[main] Pipeline finalizado com sucesso. Dados prontos para o Painel de Indicadores!")

if __name__ == "__main__":
    run_etl()