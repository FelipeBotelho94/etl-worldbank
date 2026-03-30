import time
import requests
from typing import List, Dict, Any
from config import settings

# --- 1. O FETCH DO PROFESSOR (Adaptado para Indicadores) ---
def fetch_indicator_page(indicator: str, page: int) -> List[Dict[str, Any]]:
    # Tirei o per_page dos parâmetros da função e fixei no params abaixo
    url = f"{settings.api_base_url}/country/all/indicator/{indicator}"
    
    # Colocamos os valores exigidos pelo professor direto aqui!
    params = {
        "format": "json", 
        "per_page": 100, # Exigência do professor para indicadores
        "mrv": 10,       # Últimos 10 anos
        "page": page
    }

    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise ValueError("Resposta da API não está no formato esperado (lista).")

            if len(data) > 1 and data[1] is not None:
                return data[1]
            return [] 

        except Exception as exc:
            tempo_espera = 2 ** (attempt + 1)
            print(f"[extract] tentativa {attempt + 1}/3 falhou na pág {page} do ind. {indicator}: {exc}. Aguardando {tempo_espera}s...")
            time.sleep(tempo_espera)

    raise RuntimeError(f"Falha ao extrair {indicator} na página {page} após 3 tentativas.")


# --- 2. O EXTRACT ALL DO PROFESSOR (O Maestro) ---
def extract_all_indicators() -> Dict[str, List[Dict[str, Any]]]:
    todos_dados = {}
    
    # Já que não está no config.py, definimos a lista obrigatória direto aqui
    indicadores_obrigatorios = [
        "NY.GDP.PCAP.KD", 
        "SP.POP.TOTL", 
        "SH.XPD.CHEX.GD.ZS",
        "SE.XPD.TOTL.GD.ZS", 
        "EG.ELC.ACCS.ZS"
    ]

    for indicador in indicadores_obrigatorios:
        all_data_indicador = []
        print(f"\n--- Iniciando extração do indicador: {indicador} ---")
        
        for page in range(1, 1000): 
            # Tiramos o settings.indicators_per_page daqui
            page_data = fetch_indicator_page(indicador, page)

            if not page_data:
                print(f"[extract] {indicador}: página {page} vazia. Fim deste indicador.")
                break

            print(f"[log] {indicador} | página {page}: {len(page_data)} registros extraídos.")
            all_data_indicador.extend(page_data)

        todos_dados[indicador] = all_data_indicador
        print(f"[extract] total do indicador {indicador}: {len(all_data_indicador)} registros.")

    return todos_dados


# --- 3. EXTRAÇÃO DE PAÍSES (Uma única chamada) ---
def fetch_countries() -> List[Dict[str, Any]]:
    url = f"{settings.api_base_url}/country"
    
    # Colocamos o 300 direto aqui, sem chamar o settings!
    params = {"format": "json", "per_page": 300}
    
    print("\n--- Iniciando extração de Países ---")
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if len(data) > 1 and data[1] is not None:
                print(f"[log] Países extraídos com sucesso: {len(data[1])} registros.")
                return data[1]
            return []
            
        except Exception as exc:
            tempo_espera = 2 ** (attempt + 1)
            print(f"[extract] falha ao buscar países: {exc}. Aguardando {tempo_espera}s...")
            time.sleep(tempo_espera)
            
    raise RuntimeError("Falha ao extrair países após 3 tentativas.")

# --- ÁREA DE EXECUÇÃO (O gatilho do script) ---
if __name__ == "__main__":
    print("Iniciando o processo de Extração (Extract)...")
    
    # 1. Manda executar a extração de países e salva na variável
    paises_extraidos = fetch_countries()
    
    # 2. Manda executar a extração de todos os 5 indicadores e salva na variável
    indicadores_extraidos = extract_all_indicators()
    
    # 3. Mostra um resumo final para provar que deu tudo certo!
    print("\n=== RESUMO FINAL DA EXTRAÇÃO ===")
    print(f"Total de Países/Agregados extraídos: {len(paises_extraidos)}")
    
    if indicadores_extraidos:
        for indicador, dados in indicadores_extraidos.items():
            print(f"Indicador {indicador}: {len(dados)} registros em memória.")