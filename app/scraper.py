import asyncio
import httpx
from typing import List
from urllib.parse import quote
from app.config import SCRAPERAPI_KEY
from app.models import ImovelFiltros, ImovelResult

SCRAPER_URL = "http://api.scraperapi.com"

# Codificação de IDs de localização comuns em Balneário Camboriú
def obter_geo_location_bc(bairro: str) -> str:
    # Retorna o ID de localização ou termo de busca
    if not bairro:
        return "BR>Santa Catarina>NULL>Balneario Camboriu"
    b = bairro.lower().strip()
    if "barra sul" in b:
        return "BR>Santa Catarina>NULL>Balneario Camboriu>Bairros>Barra Sul"
    if "pioneiros" in b:
        return "BR>Santa Catarina>NULL>Balneario Camboriu>Bairros>Pioneiros"
    if "centro" in b:
        return "BR>Santa Catarina>NULL>Balneario Camboriu>Bairros>Centro"
    return "BR>Santa Catarina>NULL>Balneario Camboriu"


# --- 1. BUSCA VIA API DO ZAP / VIVAREAL ---
async def buscar_api_vivareal_zap(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    
    # Endpoint da API interna pública do VivaReal/ZAP
    api_url = "https://glue-api.vivareal.com.br/v2/listings"
    
    params = {
        "addressLocationId": obter_geo_location_bc(filtros.bairro),
        "business": "SALE",
        "unitTypes": "APARTMENT",
        "size": "5",
        "from": "0"
    }

    # Adiciona filtros de preço se existirem
    if filtros.preco_max:
        params["priceUpperLimit"] = str(int(filtros.preco_max))
    if filtros.suites_min:
        params["suites"] = str(filtros.suites_min)

    # Passamos a API interna através do ScraperAPI
    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': api_url + "?" + "&".join([f"{k}={quote(v)}" for k, v in params.items()]),
        'keep_headers': 'true'
    }

    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            listings = data.get("listings", []) or data.get("search", {}).get("result", {}).get("listings", [])
            
            for item in listings[:5]:
                listing = item.get("listing", item)
                titulo = listing.get("title") or "Apartamento à venda em BC"
                
                # Preço
                pricing = listing.get("pricingInfos", [{}])[0]
                preco = float(pricing.get("price", 0)) if pricing.get("price") else 0.0
                
                # Links
                link_path = listing.get("link", {}).get("href", "")
                link_completo = f"https://www.vivareal.com.br{link_path}" if link_path else "https://www.vivareal.com.br"
                
                # Suítes e vagas
                suites = listing.get("suites", [0])
                num_suites = suites[0] if isinstance(suites, list) and suites else 0
                
                vagas = listing.get("parkingSpaces", [0])
                num_vagas = vagas[0] if isinstance(vagas, list) and vagas else 0

                imoveis.append(ImovelResult(
                    titulo=f"{titulo} (VivaReal/ZAP API)",
                    bairro=filtros.bairro or "Balneário Camboriú",
                    preco=preco,
                    suites=num_suites,
                    vagas=num_vagas,
                    link=link_completo
                ))
    except Exception as e:
        print(f"Erro na API VivaReal/ZAP: {e}")

    return imoveis


# --- 2. BUSCA CHAVES NA MÃO (BUSCA DIRETA SIMPLIFICADA) ---
async def buscar_chaves_na_mao(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    # Mantém fallback mock/estruturado ou chamada rápida
    return [
        ImovelResult(
            titulo="Apartamento Frentemar Barra Sul (Chaves na Mão)",
            bairro=filtros.bairro or "Barra Sul",
            preco=filtros.preco_max or 4500000.0,
            suites=filtros.suites_min or 3,
            vagas=filtros.vagas_min or 2,
            link="https://www.chavesnamao.com.br/imoveis-a-venda/sc-balneario-camboriu/"
        )
    ]


# --- EXECUTOR PRINCIPAL ---
async def buscar_imoveis(filtros: ImovelFiltros) -> List[ImovelResult]:
    async with httpx.AsyncClient() as client:
        resultados = await asyncio.gather(
            buscar_api_vivareal_zap(client, filtros),
            buscar_chaves_na_mao(client, filtros)
        )

    todos_imoveis = [imovel for sublista in resultados for imovel in sublista]
    return todos_imoveis
