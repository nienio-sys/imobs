import asyncio
import httpx
from typing import List
from urllib.parse import quote, unquote
from app.config import SCRAPERAPI_KEY
from app.models import ImovelFiltros, ImovelResult

SCRAPER_URL = "http://api.scraperapi.com"


# --- 1. BUSCA VIA VIVAREAL / ZAP (COM HEADERS CORRETOS) ---
async def buscar_api_vivareal(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    
    # Endpoint oficial da Glue API
    api_url = "https://glue-api.vivareal.com.br/v2/listings"
    
    # Monta a query string de localização
    location_id = "BR>Santa Catarina>NULL>Balneario Camboriu"
    if filtros.bairro:
        b = filtros.bairro.lower().strip()
        if "centro" in b:
            location_id = "BR>Santa Catarina>NULL>Balneario Camboriu>Bairros>Centro"
        elif "barra sul" in b:
            location_id = "BR>Santa Catarina>NULL>Balneario Camboriu>Bairros>Barra Sul"
        elif "pioneiros" in b:
            location_id = "BR>Santa Catarina>NULL>Balneario Camboriu>Bairros>Pioneiros"

    params_str = (
        f"addressLocationId={quote(location_id)}"
        f"&business=SALE"
        f"&unitTypes=APARTMENT"
        f"&size=10"
        f"&from=0"
    )

    if filtros.preco_max:
        params_str += f"&priceUpperLimit={int(filtros.preco_max)}"
    if filtros.suites_min:
        params_str += f"&suites={filtros.suites_min}"

    target_url = f"{api_url}?{params_str}"

    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': target_url,
        'keep_headers': 'true'
    }

    # O VivaReal EXIGE esses headers para responder 200 OK
    headers = {
        'x-domain': 'www.vivareal.com.br',
        'accept': 'application/json, text/plain, */*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = await client.get(SCRAPER_URL, params=payload, headers=headers, timeout=25.0)
        
        if response.status_code == 200:
            data = response.json()
            # A API retorna no nó 'search' ou na raiz
            results = data.get("search", {}).get("result", {}).get("listings", []) or data.get("listings", [])
            
            for item in results[:5]:
                listing = item.get("listing", item)
                titulo = listing.get("title") or "Apartamento à venda em Balneário Camboriú"
                
                # Preços
                pricing_infos = listing.get("pricingInfos", [])
                preco = 0.0
                if pricing_infos and isinstance(pricing_infos, list):
                    preco = float(pricing_infos[0].get("price", 0) or 0)

                # Link
                link_path = listing.get("link", {}).get("href", "")
                link = f"https://www.vivareal.com.br{link_path}" if link_path else "https://www.vivareal.com.br"

                # Suítes e vagas
                suites_list = listing.get("suites", [0])
                num_suites = suites_list[0] if isinstance(suites_list, list) and suites_list else (filtros.suites_min or 0)
                
                vagas_list = listing.get("parkingSpaces", [0])
                num_vagas = vagas_list[0] if isinstance(vagas_list, list) and vagas_list else (filtros.vagas_min or 0)

                imoveis.append(ImovelResult(
                    titulo=f"{titulo} (VivaReal)",
                    bairro=filtros.bairro or "Balneário Camboriú",
                    preco=preco,
                    suites=num_suites,
                    vagas=num_vagas,
                    link=link
                ))
        else:
            print(f"VivaReal API retornou Status {response.status_code}")
    except Exception as e:
        print(f"Erro na requisição VivaReal: {e}")

    return imoveis


# --- 2. BUSCA VIA ENGINE DE PESQUISA (FALLBACK COM IMÓVEIS REAIS) ---
async def buscar_via_pesquisa_google(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    
    # Monta a query exata no Google para achar anúncios reais de imóveis em BC
    query_parts = ["apartamento a venda Balneario Camboriu"]
    if filtros.bairro:
        query_parts.append(filtros.bairro)
    if filtros.suites_min:
        query_parts.append(f"{filtros.suites_min} suites")
    
    query = " ".join(query_parts) + " site:zapimoveis.com.br OR site:chavesnamao.com.br"
    
    # Usa a API do DuckDuckGo HTML simples via ScraperAPI
    search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    
    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': search_url
    }

    try:
        from bs4 import BeautifulSoup
        res = await client.get(SCRAPER_URL, params=payload, timeout=20.0)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            results = soup.select('.result')
            
            for r in results[:3]:
                title_elem = r.select_one('.result__title a')
                snippet_elem = r.select_one('.result__snippet')
                
                if title_elem:
                    titulo = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    
                    # Decodifica o link do DuckDuckGo
                    if "uddg=" in href:
                        raw_link = href.split("uddg=")[-1].split("&")[0]
                        link = unquote(raw_link)
                    else:
                        link = href

                    imoveis.append(ImovelResult(
                        titulo=titulo,
                        bairro=filtros.bairro or "Balneário Camboriú",
                        preco=filtros.preco_max or 0.0,
                        suites=filtros.suites_min or 0,
                        vagas=filtros.vagas_min or 0,
                        link=link
                    ))
    except Exception as e:
        print(f"Erro na busca Google/DDG: {e}")

    return imoveis


# --- EXECUTOR PRINCIPAL ---
async def buscar_imoveis(filtros: ImovelFiltros) -> List[ImovelResult]:
    async with httpx.AsyncClient() as client:
        resultados = await asyncio.gather(
            buscar_api_vivareal(client, filtros),
            buscar_via_pesquisa_google(client, filtros)
        )

    todos_imoveis = [imovel for sublista in resultados for imovel in sublista]
    return todos_imoveis
