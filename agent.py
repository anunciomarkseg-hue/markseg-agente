"""
Cérebro do agente — converte descrição em linguagem natural
nos dados estruturados que cada template precisa.
"""

import json, os
import anthropic

CLIENT = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

SCHEMAS = {
    "relatorio_performance": """
Extraia do texto do usuário um JSON com esta estrutura exata:
{
  "cliente": str,
  "periodo": str,
  "agencia": "MarkSeg Tráfego · Rafael",
  "responsavel": "Rafael",
  "frase_resumo": str,       // frase curta resumindo resultado
  "frase_destaque": str,     // frase de destaque em laranja (ex: "CPL R$ 3,39 · escalar agora")
  "info_capa": str,          // subtítulo da capa
  "meta_total": float,       // investimento total Meta
  "meta_leads": int,
  "meta_cpl": float,
  "meta_campanhas": [
    {"etapa": "TOPO|MEIO|FUNDO", "nome": str, "verba": float,
     "resultado": str, "cpr": float, "impressoes": int}
  ],
  "criativos": [
    {"nome": str, "status": "Ativo|Inativo", "gasto": float,
     "leads": int, "cpl": float, "hook": str, "avaliacao": str, "destaque": bool}
  ],
  "conjuntos": [
    {"nome": str, "status": "Ativo|Inativo", "orcamento": float,
     "gasto": float, "leads": int, "cpl": float, "alcance": int}
  ],
  "google_gasto": float,
  "google_cliques": int,
  "google_impressoes": int,
  "google_ctr": str,
  "google_conv": int,
  "google_cpl": float,
  "insights_criativos": [str],
  "insights_google": [str],
  "sugestoes_conteudo": [str],
  "estrategia_seguidores": [
    {"iniciativa": str, "acao": str, "prioridade": str}
  ],
  "proximos_passos": [
    {"acao": str, "responsavel": str, "prazo": str, "impacto": str}
  ]
}
""",

    "relatorio_social": """
Extraia um JSON:
{
  "cliente": str, "periodo": str, "agencia": "MarkSeg Tráfego · Rafael",
  "frase_resumo": str, "frase_destaque": str, "info_capa": str,
  "seguidores_atual": int, "seguidores_novos": int,
  "alcance_total": int, "impressoes_total": int,
  "engajamento_medio": str, "saves_total": int,
  "posts": [
    {"data": str, "formato": "Reels|Carrossel|Estático|Story",
     "titulo": str, "alcance": int, "curtidas": int,
     "saves": int, "engajamento": str, "destaque": bool}
  ],
  "reels": [
    {"titulo": str, "reproducoes": int, "alcance": int,
     "engajamento": str, "destaque": bool}
  ],
  "insights_semana": [str],
  "recomendacoes": [str],
  "pauta_proxima": [
    {"dia": str, "formato": str, "tema": str, "objetivo": str}
  ]
}
""",

    "plano_de_midia": """
Extraia um JSON:
{
  "cliente": str, "periodo": str, "agencia": "MarkSeg Tráfego · Rafael",
  "investimento": float, "leads_estimados": str,
  "cpl_estimado_min": float, "cpl_estimado_max": float,
  "frase_resumo": str, "frase_destaque": str, "info_capa": str,
  "canais": [
    {"etapa": "Google|Meta|Reserva", "canal": str, "funcao": str,
     "verba": float, "percentual": float}
  ],
  "produtos": [
    {"nome": str, "tipo": str, "prioridade": str, "descricao": str}
  ],
  "cronograma": [
    {"semana": str, "itens": [str]}
  ],
  "infraestrutura": [str],
  "precisa_cliente": [str],
  "palavras_chave": [str]
}
""",

    "apresentacao_resultado": """
Extraia um JSON:
{
  "cliente": str, "periodo": str, "agencia": "MarkSeg Tráfego · Rafael",
  "investimento_total": float, "leads_total": int,
  "cpl_medio": float, "taxa_qualificacao": str,
  "roas": str, "cac": float,
  "frase_resumo": str, "frase_destaque": str, "info_capa": str,
  "metas": [
    {"metrica": str, "meta": str, "realizado": str,
     "status": "OK|ALERTA|CRITICO"}
  ],
  "canais": [
    {"canal": str, "gasto": float, "leads": int,
     "cpl": float, "taxa_qual": str, "avaliacao": str}
  ],
  "evolucao": [
    {"semana": str, "leads": int, "gasto": float, "cpl": float}
  ],
  "aprendizados": [str],
  "plano_proximo_mes": [
    {"acao": str, "canal": str, "impacto_esperado": str}
  ]
}
""",

    "proposta_comercial": """
Extraia um JSON:
{
  "cliente": str, "periodo": str, "agencia": "MarkSeg Tráfego · Rafael",
  "responsavel": "Rafael", "data_proposta": str, "validade": "30 dias",
  "verba_midia": float, "honorarios": float, "total_mensal": float,
  "frase_resumo": str, "frase_destaque": str, "info_capa": str,
  "diagnostico": [str],
  "servicos": [
    {"nome": str, "descricao": str, "investimento": float, "recorrente": bool}
  ],
  "resultados_esperados": [
    {"metrica": str, "valor": str, "prazo": str}
  ],
  "diferenciais": [str],
  "proximos_passos": [
    {"passo": str, "prazo": str}
  ]
}
""",
}

SYSTEM = """Você é o assistente da MarkSeg Agência de Tráfego.
Sua tarefa é extrair informações do texto do usuário e retornar APENAS um JSON válido,
sem explicações, sem markdown, sem bloco de código — apenas o JSON puro.
Se uma informação não for mencionada, use valores padrão razoáveis (0 para números,
listas vazias para arrays, strings vazias para texto).
Sempre gere frases de resumo executivo impactantes baseadas nos dados fornecidos.
Sempre gere insights e recomendações relevantes quando não fornecidos explicitamente."""


def extrair_dados(tipo: str, descricao: str) -> dict:
    schema = SCHEMAS.get(tipo, "")
    prompt = f"""O usuário quer gerar um documento do tipo: {tipo.replace('_', ' ').upper()}

SCHEMA esperado:
{schema}

DESCRIÇÃO DO USUÁRIO:
{descricao}

Retorne APENAS o JSON preenchido com as informações acima."""

    msg = CLIENT.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text.strip()
    # limpa caso venha com bloco de código
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
