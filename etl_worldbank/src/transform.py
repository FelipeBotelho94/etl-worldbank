from typing import List, Dict, Any, Optional
from datetime import datetime

def safe_str(value: Any) -> Optional[str]:
    """T2: Aplicar strip(), substituir vazias por None."""
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None

def safe_float(value: Any) -> Optional[float]:
    """T3: Converter para float com tratamento seguro."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def safe_int(value: Any) -> Optional[int]:
    """T3: Converter para int com tratamento seguro (Para o ano)."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# TRANSFORMAÇÃO DE PAÍSES (Dimensão)

def transform_country_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Transforma um único registro de país."""
    region_dict = record.get("region", {})
    region_name = safe_str(region_dict.get("value")) if isinstance(region_dict, dict) else None
    
    income_dict = record.get("incomeLevel", {})
    income_group = safe_str(income_dict.get("value")) if isinstance(income_dict, dict) else None

    return {
        "iso2_code": safe_str(record.get("iso2Code")),
        "iso3_code": safe_str(record.get("id")),
        "name": safe_str(record.get("name")),
        "region": region_name.title() if region_name else None, # T2: title-case
        "income_group": income_group,
        "capital": safe_str(record.get("capitalCity")),
        "longitude": safe_float(record.get("longitude")),
        "latitude": safe_float(record.get("latitude")),
    }

def transform_all_countries(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed = []
    skipped = 0

    for record in raw_data:
        item = transform_country_record(record)
        iso2 = item.get("iso2_code")
        regiao = item.get("region")
        renda = item.get("income_group")

        # REGRA 1: Filtro de Entidade (Excluir Agregados)
        
        # Filtro brando exclui apenas "Aggregates" e não classificados.
        # Mantém continentes abertos para não perder países de referência da query (US e NG).
        if not iso2 or regiao == "Aggregates":
            skipped += 1
            continue

        # REGRA 2: Filtro de Renda (LIC, MIC, HIC)

        # O Banco Mundial usa os termos: 'Low income', 'Lower middle income', 'Upper middle income', 'High income'
        # Se for 'Not classified' ou vier vazio, joga fora.
        if not renda or renda == "Not classified":
            skipped += 1
            continue

        transformed.append(item)

    print(f"\n[transform] Países válidos transformados: {len(transformed)}")
    print(f"[transform] Países/Agregados descartados: {skipped}")
    return transformed

# TRANSFORMAÇÃO DE FATOS (Série Histórica)

def transform_fact_record(record: Dict[str, Any], indicator_code: str) -> Dict[str, Any]:
    """Transforma um único registro de indicador/fato."""
    country_info = record.get("country", {})
    
    return {
        "iso2_code": safe_str(country_info.get("id")),
        "indicator_code": indicator_code,
        "year": safe_int(record.get("date")),
        "value": safe_float(record.get("value")) # O professor disse que pode ser nulo!
    }

# Adicione 'valid_iso2_codes' aqui nos parênteses:
def transform_all_facts(raw_indicators_dict: Dict[str, List[Dict[str, Any]]], valid_iso2_codes: set) -> List[Dict[str, Any]]:
    transformed = {} 
    skipped = 0
    duplicatas = 0
    ano_atual = datetime.now().year

    for indicador_code, lista_registros in raw_indicators_dict.items():
        for record in lista_registros:
            item = transform_fact_record(record, indicador_code)
            iso2 = item["iso2_code"]
            ano = item["year"]
            
            # Se o código não for de um país aprovado, joga fora
            if not iso2 or iso2 not in valid_iso2_codes:
                skipped += 1
                continue
                
            # Filtro temporal (2010 até hoje)
            if ano is None or not (2010 <= ano <= ano_atual):
                skipped += 1
                continue
                
            # Deduplicação
            chave_composta = (iso2, indicador_code, ano)
            if chave_composta in transformed:
                duplicatas += 1
            transformed[chave_composta] = item

    print(f"\n[transform] Fatos válidos transformados: {len(transformed)}")
    print(f"[transform] Fatos descartados (fora do escopo ou agregados): {skipped}")
    return list(transformed.values())


# ==========================================
# 4. TABELA DE INDICADORES (A Dimensão Fixa)
# ==========================================

def get_indicators_table() -> List[Dict[str, str]]:
    """Gera a lista fixa para a tabela de dimensão de indicadores."""
    return [
        {"indicator_code": "NY.GDP.PCAP.KD", "indicator_name": "PIB per capita", "unit": "USD"},
        {"indicator_code": "SP.POP.TOTL", "indicator_name": "População total", "unit": "Pessoas"},
        {"indicator_code": "SH.XPD.CHEX.GD.ZS", "indicator_name": "Gasto em saúde", "unit": "% PIB"},
        {"indicator_code": "SE.XPD.TOTL.GD.ZS", "indicator_name": "Gasto em educação", "unit": "% PIB"},
        {"indicator_code": "EG.ELC.ACCS.ZS", "indicator_name": "Acesso à eletricidade", "unit": "%"},
    ]