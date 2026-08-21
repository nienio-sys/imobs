from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import GROQ_API_KEY
from app.models import ImovelFiltros

# Instancia o modelo configurado no Groq
llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    groq_api_key=GROQ_API_KEY,
    temperature=0
)

# Parser para converter a saída do modelo direto na classe Pydantic
parser = JsonOutputParser(pydantic_object=ImovelFiltros)

system_prompt = """
Você é um corretor e especialista em imóveis em Balneário Camboriú (SC).
Sua tarefa é analisar o pedido do cliente e extrair os filtros de busca.

Locais comuns em BC:
- Barra Sul, Centro, Nações, Pioneiros, Ariribá, Praia dos Amores, Quadra do Mar, Av. Atlântica, Av. Brasil.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{consulta}")
]).partial(format_instructions=parser.get_format_instructions())

# Cadeia de processamento: Prompt -> Modelo -> Parser JSON
chain = prompt | llm | parser

def extrair_filtros(consulta: str) -> ImovelFiltros:
    dados_dict = chain.invoke({"consulta": consulta})
    return ImovelFiltros(**dados_dict)
