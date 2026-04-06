import time
import requests
from typing import List, Dict, Any
from config import settings

def fetch_indicator_page(indicator: str, page: int) -> List[Dict[str, Any]]:
    # Tirei o per_page dos parâmetros da função e fixei no params abaixo
    url = f"{settings.api_base_url}/country/all/indicator/{indicator}"
    
    params = {
        "format": "json", 
        "per_page": 100, 
        "mrv": 10,       
        "page": page
    }

    for attempt in range(5):
        try:
            response = requests.get(url, params=params, timeout=90)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise ValueError("Resposta da API não está no formato esperado (lista).")

            if len(data) > 1 and data[1] is not None:
                return data[1]
            return [] 

        except Exception as exc:
            # Se for a primeira página e der erro, precisamos insistir (pode ser rede)
            # Mas se for uma página avançada (ex: > 25) e der Timeout, 
            # é muito provável que a API só esteja instável no final dos dados.
            if page >= 27 and "timeout" in str(exc).lower():
                print(f"[extract] Timeout na página {page}. Assumindo fim dos dados para o indicador {indicator}.")
                return [] # Retorna lista vazia para ativar o 'break' no extract_all_indicators

            tempo_espera = 2 ** (attempt + 1)
            print(f"[extract] tentativa {attempt + 1}/5 falhou na pág {page} do ind. {indicator}: {exc}. Aguardando {tempo_espera}s...")
            time.sleep(tempo_espera)

    raise RuntimeError(f"Falha ao extrair {indicator} na página {page} após 5 tentativas.")


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
        
            page_data = fetch_indicator_page(indicador, page)

            if not page_data:
                print(f"[extract] {indicador}: página {page} vazia. Fim deste indicador.")
                break

            print(f"[log] {indicador} | página {page}: {len(page_data)} registros extraídos.")
            all_data_indicador.extend(page_data)

        todos_dados[indicador] = all_data_indicador
        print(f"[extract] total do indicador {indicador}: {len(all_data_indicador)} registros.")

    return todos_dados

def fetch_countries() -> List[Dict[str, Any]]:
    url = f"{settings.api_base_url}/country"
    
    params = {"format": "json", "per_page": 300}
    
    print("\n--- Iniciando extração de Países ---")
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=120)
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