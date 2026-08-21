import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import quote
from app.config import SCRAPERAPI_KEY
from app.models import ImovelFiltros, ImovelResult

SCRAPER_URL = "http://api.scraperapi.com"

# --- Mapeamento simples de Bairros para URL do ZAP/VivaReal ---
def tratar_bairro_slug(bairro: str) -> str:
    if not bairro:
        return ""
    b = bairro.lower().strip()
    if "barra sul" in b:
        return "barra-sul"
    if "centro" in b:
        return "centro"
    if "pioneiros" in b:
        return "pioneiros"
    if "praia dos amores" in b:
        return "praia-dos-amores"
    if "naçoes" in b or "nacoes" in b:
        return "nacoes"
    return quote(b.replace(" ", "-"))


# --- 1. RASPADOR ZAP IMÓVEIS ---
async def raspar_zap_imoveis(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    slug_bairro = tratar_bairro_slug(filtros.bairro)
    
    # URL base do ZAP
    if slug_bairro:
        url_alvo = f"https://www.zapimoveis.com.br/venda/imoveis/sc+balneario-camboriu++{slug_bairro}/"
    else:
        url_alvo = "https://www.zapimoveis.com.br/venda/imoveis/sc+balneario-camboriu/"

    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': url_alvo,
        'render': 'true'  # Necessário para ZAP Imóveis (React/Next.js)
    }

    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=35.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Cartões de imóvel do ZAP
            cards = soup.select('.card-container') or soup.select('[data-type="property"]')
            
            for card in cards[:5]:  # Pega os 5 primeiros
                titulo_el = card.select_one('.card__title') or card.select_one('[data-testid="property-card-title"]')
                preco_el = card.select_one('.simple-card__price') or card.select_one('[data-testid="property-card-price"]')
                link_el = card.select_one('a')

                if titulo_el and link_el:
                    link = link_el.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.zapimoveis.com.br{link}"

                    imoveis.append(ImovelResult(
                        titulo=titulo_el.get_text(strip=True) + " (ZAP Imóveis)",
                        bairro=filtros.bairro or "Balneário Camboriú",
                        preco=filtros.preco_max or 0.0,
                        suites=filtros.suites_min or 0,
                        vagas=filtros.vagas_min or 0,
                        link=link
                    ))
    except Exception as e:
        print(f"Erro no ZAP Imóveis: {e}")

    return imoveis


# --- 2. RASPADOR VIVAREAL ---
async def raspar_vivareal(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    slug_bairro = tratar_bairro_slug(filtros.bairro)

    if slug_bairro:
        url_alvo = f"https://www.vivareal.com.br/venda/santa-catarina/balneario-camboriu/bairros/{slug_bairro}/"
    else:
        url_alvo = "https://www.vivareal.com.br/venda/santa-catarina/balneario-camboriu/"

    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': url_alvo,
        'render': 'true'
    }

    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=35.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.select('.property-card__container')

            for card in cards[:5]:
                titulo_el = card.select_one('.property-card__title')
                link_el = card.select_one('a.property-card__content-link')

                if titulo_el and link_el:
                    link = link_el.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.vivareal.com.br{link}"

                    imoveis.append(ImovelResult(
                        titulo=titulo_el.get_text(strip=True) + " (VivaReal)",
                        bairro=filtros.bairro or "Balneário Camboriú",
                        preco=filtros.preco_max or 0.0,
                        suites=filtros.suites_min or 0,
                        vagas=filtros.vagas_min or 0,
                        link=link
                    ))
    except Exception as e:
        print(f"Erro no VivaReal: {e}")

    return imoveis


# --- 3. RASPADOR CHAVES NA MÃO ---
async def raspar_chaves_na_mao(client: httpx.AsyncClient, filtros: ImovelFiltros) -> List[ImovelResult]:
    imoveis = []
    
    # URL de busca do Chaves na Mão
    url_alvo = "https://www.chavesnamao.com.br/imoveis-a-venda/sc-balneario-camboriu/"

    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': url_alvo,
        'render': 'false'  # Pode ser false para economizar créditos e ser mais rápido
    }

    try:
        response = await client.get(SCRAPER_URL, params=payload, timeout=35.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.select('div[data-template="card-imovel"]') or soup.select('article')

            for card in cards[:5]:
                titulo_el = card.select_one('h2') or card.select_one('h3')
                link_el = card.select_one('a')

                if titulo_el and link_el:
                    link = link_el.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.chavesnamao.com.br{link}"

                    imoveis.append(ImovelResult(
                        titulo=titulo_el.get_text(strip=True) + " (Chaves na Mão)",
                        bairro=filtros.bairro or "Balneário Camboriú",
                        preco=filtros.preco_max or 0.0,
                        suites=filtros.suites_min or 0,
                        vagas=filtros.vagas_min or 0,
                        link=link
                    ))
    except Exception as e:
        print(f"Erro no Chaves na Mão: {e}")

    return imoveis


# --- EXECUTOR PARALELO ---
async def buscar_imoveis(filtros: ImovelFiltros) -> List[ImovelResult]:
    async with httpx.AsyncClient() as client:
        # Roda os 3 scrapers em paralelo usando asyncio.gather
        resultados = await asyncio.gather(
            raspar_zap_imoveis(client, filtros),
            raspar_vivareal(client, filtros),
            raspar_chaves_na_mao(client, filtros)
        )

    # Junta os resultados dos 3 portais em uma lista única
    todos_imoveis = [imovel for sublista in resultados for imovel in sublista]
    return todos_imoveis
