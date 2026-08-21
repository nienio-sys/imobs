import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List
from app.config import SCRAPERAPI_KEY
from app.models import ImovelFiltros, ImovelResult

# Base da URL da ScraperAPI
SCRAPER_URL = "http://api.scraperapi.com"

# --- Raspador Site 1 (Ex: Portal Local A) ---
async def raspar_site_1(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    # Altere para a URL real do Site 1 com os parâmetros de filtro
    url_alvo = f"https://www.exemplo-imobiliaria-bc-1.com.br/imoveis?bairro={filtros.bairro or ''}&preco_max={filtros.preco_max or ''}"
    
    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': url_alvo,
        'render': 'true'  # Ative se o site usar JavaScript/React
    }
    
    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=30.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Lógica de extração do HTML do Site 1
            # Exemplo de extração mockada até mapear o HTML real:
            imoveis.append(ImovelResult(
                titulo="Apê Vista Mar - Fonte: Site 1",
                bairro=filtros.bairro or "Barra Sul",
                preco=filtros.preco_max or 3500000.0,
                suites=filtros.suites_min or 3,
                vagas=filtros.vagas_min or 2,
                link="https://www.exemplo-imobiliaria-bc-1.com.br/imovel-1"
            ))
    except Exception as e:
        print(f"Erro ao raspar Site 1: {e}")
        
    return imoveis

# --- Raspador Site 2 (Ex: Portal Local B) ---
async def raspar_site_2(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    url_alvo = "https://www.exemplo-imobiliaria-bc-2.com.br/busca"
    payload = {'api_key': SCRAPERAPI_KEY, 'url': url_alvo}
    
    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=30.0)
        if response.status_code == 200:
            # Lógica de extração do HTML do Site 2
            imoveis.append(ImovelResult(
                titulo="Cobertura Quadra do Mar - Fonte: Site 2",
                bairro=filtros.bairro or "Centro",
                preco=filtros.preco_max or 5000000.0,
                suites=filtros.suites_min or 4,
                vagas=filtros.vagas_min or 3,
                link="https://www.exemplo-imobiliaria-bc-2.com.br/imovel-2"
            ))
    except Exception as e:
        print(f"Erro ao raspar Site 2: {e}")
        
    return imoveis

# --- Raspador Site 3 (Ex: Portal Local C) ---
async def raspar_site_3(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    url_alvo = "https://www.exemplo-imobiliaria-bc-3.com.br/venda"
    payload = {'api_key': SCRAPERAPI_KEY, 'url': url_alvo}
    
    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=30.0)
        if response.status_code == 200:
            # Lógica de extração do HTML do Site 3
            imoveis.append(ImovelResult(
                titulo="Apartamento Frentemar - Fonte: Site 3",
                bairro=filtros.bairro or "Pioneiros",
                preco=filtros.preco_max or 4200000.0,
                suites=filtros.suites_min or 3,
                vagas=filtros.vagas_min or 2,
                link="https://www.exemplo-imobiliaria-bc-3.com.br/imovel-3"
            ))
    except Exception as e:
        print(f"Erro ao raspar Site 3: {e}")
        
    return imoveis

# --- Função Principal que executa as 3 raspagens simultaneamente ---
async def buscar_imoveis(filtros: ImovelFiltros) -> List[ImovelResult]:
    async with httpx.AsyncClient() as client:
        # Dispara os 3 scrapers ao mesmo tempo
        resultados = await asyncio.gather(
            raspar_site_1(client, filtros),
            raspar_site_2(client, filtros),
            raspar_site_3(client, filtros)
        )
    
    # Junta as 3 listas de resultados em uma só
    todos_imoveis = [imovel for sublista in resultados for imovel in sublista]
    return todos_imoveis
