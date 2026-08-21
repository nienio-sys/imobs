from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    query: str

class ImovelFiltros(BaseModel):
    bairro: Optional[str] = None
    preco_max: Optional[float] = None
    suites_min: Optional[int] = None
    vagas_min: Optional[int] = None
    caracteristicas_extras: List[str] = []

class ImovelResult(BaseModel):
    titulo: str
    bairro: str
    preco: float
    suites: int
    vagas: int
    link: str

class ChatResponse(BaseModel):
    filtros_extraidos: ImovelFiltros
    imoveis_encontrados: List[ImovelResult]
    resposta_agente: str
