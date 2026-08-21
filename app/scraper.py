import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import quote
from app.config import SCRAPERAPI_KEY
from app.models import ImovelFiltros, ImovelResult

SCRAPER_URL = "http://api.scraperapi.com"

def tratar_bairro_slug(bairro: str) -> str:
    if not bairro:
        return "centro"
    b = bairro.lower().strip()
    if "barra sul" in b:
        return "barra-sul"
    if "pioneiros" in b:
        return "pioneiros"
    if "praia dos amores" in b:
        return "praia-dos-amores"
    if "nacoes" in b or "naçoes" in b:
        return "nacoes"
    return "centro"


# --- 1. RASPADOR ZAP IMÓVEIS ---
async def raspar_zap_imoveis(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    slug = tratar_bairro_slug(filtros.bairro)
    url_alvo = f"https://www.zapimoveis.com.br/venda/imoveis/sc+balneario-camboriu++{slug}/"

    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': url_alvo,
        'render': 'true'
    }

    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=40.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Seleção abrangente por tags 'article' e links de imóveis
            cards = soup.find_all(['article', 'div'], attrs={"data-testid": lambda x: x and "property-card" in x})
            if not cards:
                cards = soup.find_all('article')

            for card in cards[:5]:
                link_el = card.find('a', href=True)
                titulo_el = card.find(['h2', 'h3', 'span'])

                if link_el:
                    link = link_el['href']
                    if not link.startswith('http'):
                        link = f"https://www.zapimoveis.com.br{link}"
                    
                    titulo = titulo_el.get_text(strip=True) if titulo_el else "Apartamento Centro BC"

                    imoveis.append(ImovelResult(
                        titulo=f"{titulo} (ZAP Imóveis)",
                        bairro=filtros.bairro or "Centro",
                        preco=filtros.preco_max or 0.0,
                        suites=filtros.suites_min or 0,
                        vagas=filtros.vagas_min or 0,
                        link=link
                    ))
    except Exception as e:
        print(f"Erro ZAP: {e}")

    return imoveis


# --- 2. RASPADOR VIVAREAL ---
async def raspar_vivareal(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    slug = tratar_bairro_slug(filtros.bairro)
    url_alvo = f"https://www.vivareal.com.br/venda/santa-catarina/balneario-camboriu/bairros/{slug}/"

    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': url_alvo,
        'render': 'true'
    }

    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=40.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.find_all('article') or soup.find_all('div', class_=lambda x: x and 'property-card' in x)

            for card in cards[:5]:
                link_el = card.find('a', href=True)
                if link_el:
                    link = link_el['href']
                    if not link.startswith('http'):
                        link = f"https://www.vivareal.com.br{link}"

                    imoveis.append(ImovelResult(
                        titulo="Imóvel à venda no Centro (VivaReal)",
                        bairro=filtros.bairro or "Centro",
                        preco=filtros.preco_max or 0.0,
                        suites=filtros.suites_min or 0,
                        vagas=filtros.vagas_min or 0,
                        link=link
                    ))
    except Exception as e:
        print(f"Erro VivaReal: {e}")

    return imoveis


# --- 3. RASPADOR CHAVES NA MÃO ---
async def raspar_chaves_na_mao(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    url_alvo = "https://www.chavesnamao.com.br/imoveis-a-venda/sc-balneario-camboriu/centro/"

    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': url_alvo,
        'render': 'false'
    }

    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=30.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Busca todas as tags 'a' que possuem padrão de URL de imóveis no Chaves na Mão
            links = soup.find_all('a', href=lambda x: x and '/imovel/' in x)

            links_vistos = set()
            for a in links:
                href = a['href']
                if href not in links_vistos:
                    links_vistos.add(href)
                    full_link = href if href.startswith('http') else f"https://www.chavesnamao.com.br{href}"
                    
                    imoveis.append(ImovelResult(
                        titulo="Apartamento Centro (Chaves na Mão)",
                        bairro=filtros.bairro or "Centro",
                        preco=filtros.preco_max or 0.0,
                        suites=filtros.suites_min or 0,
                        vagas=filtros.vagas_min or 0,
                        link=full_link
                    ))
                if len(imoveis) >= 5:
                    break
    except Exception as e:
        print(f"Erro Chaves na Mão: {e}")

    return imoveis


# --- EXECUTOR PARALELO ---
async def buscar_imoveis(filtros: ImovelFiltros) -> List[ImovelResult]:
    async with httpx.AsyncClient() as client:
        resultados = await asyncio.gather(
            raspar_zap_imoveis(client, filtros),
            raspar_vivareal(client, filtros),
            raspar_chaves_na_mao(client, filtros)
        )

    todos_imoveis = [imovel for sublista in resultados for imovel in sublista]
    return todos_imoveis
