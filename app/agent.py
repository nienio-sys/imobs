from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.config import GROQ_API_KEY
from app.models import ImovelFiltros

# Modelo utilizado no projeto anterior via Groq
llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    groq_api_key=GROQ_API_KEY,
    temperature=0
)

system_prompt = """
Você é um corretor e especialista em imóveis em Balneário Camboriú (SC).
Sua tarefa é analisar o pedido do cliente e extrair os filtros de busca no formato JSON estruturado.

Locais comuns em BC:
- Barra Sul, Centro, Nações, Pioneiros, Ariribá, Praia dos Amores, Quadra do Mar, Av. Atlântica, Av. Brasil.

Responda APENAS com o JSON contendo:
- bairro: string ou null
- preco_max: float ou null
- suites_min: int ou null
- vagas_min: int ou null
- caracteristicas_extras: lista de strings (ex: ["frente mar", "churrasqueira"])
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{consulta}")
])

chain = prompt | llm.with_structured_output(ImovelFiltros)

def extrair_filtros(consulta: str) -> ImovelFiltros:
    return chain.invoke({"consulta": consulta})
