from fastapi import FastAPI, HTTPException
from app.models import ChatRequest, ChatResponse
from app.agent import extrair_filtros
from app.scraper import buscar_imoveis

app = FastAPI(title="Agente de Imóveis Balneário Camboriú", version="1.0.0")

@app.get("/")
def health_check():
    return {"status": "ok", "servico": "Agente Imobiliario BC"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. Extrai filtros com a IA
        filtros = extrair_filtros(request.query)
        
        # 2. Executa a busca assíncrona nos 3 sites
        imoveis = await buscar_imoveis(filtros)
        
        # 3. Gera resposta
        resumo_agente = (
            f"Encontrei {len(imoveis)} opção(ões) nos 3 portais consultados "
            f"para a sua busca em Balneário Camboriú."
        )
        
        return ChatResponse(
            filtros_extraidos=filtros,
            imoveis_encontrados=imoveis,
            resposta_agente=resumo_agente
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
