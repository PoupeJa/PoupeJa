"""
PoupeJá — Scraper de preços de supermercados portugueses
Supermercados: Continente, Pingo Doce, Lidl
Corre diariamente via GitHub Actions (gratuito)
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9",
    "Accept": "application/json",
}

# Produtos a monitorizar (nome de pesquisa por supermercado)
PRODUTOS = [
    {"id": "leite-mimosa-1l",       "nome": "Leite Mimosa 1L",        "emoji": "🥛", "categoria": "lacticinios",  "continente": "leite mimosa 1l",     "pingodoce": "leite mimosa 1l",     "lidl": "leite 1l"},
    {"id": "pao-de-forma",          "nome": "Pão de forma",           "emoji": "🍞", "categoria": "padaria",      "continente": "pao de forma fatiado","pingodoce": "pao de forma",        "lidl": "pao de forma"},
    {"id": "ovos-m-12",             "nome": "Ovos M (12 un.)",        "emoji": "🥚", "categoria": "frescos",      "continente": "ovos m 12",           "pingodoce": "ovos m 12",           "lidl": "ovos 12"},
    {"id": "frango-inteiro",        "nome": "Frango inteiro",         "emoji": "🍗", "categoria": "carnes",       "continente": "frango inteiro",      "pingodoce": "frango inteiro",      "lidl": "frango inteiro"},
    {"id": "queijo-flamengo",       "nome": "Queijo flamengo",        "emoji": "🧀", "categoria": "lacticinios",  "continente": "queijo flamengo",     "pingodoce": "queijo flamengo",     "lidl": "queijo flamengo"},
    {"id": "azeite-1l",             "nome": "Azeite virgem 1L",       "emoji": "🫒", "categoria": "mercearia",    "continente": "azeite virgem extra 1l","pingodoce": "azeite 1l",          "lidl": "azeite 1l"},
    {"id": "arroz-agulha-1kg",      "nome": "Arroz agulha 1kg",       "emoji": "🍚", "categoria": "mercearia",    "continente": "arroz agulha 1kg",    "pingodoce": "arroz agulha 1kg",    "lidl": "arroz 1kg"},
    {"id": "detergente-loica-500ml","nome": "Detergente loiça 500ml", "emoji": "🧴", "categoria": "limpeza",      "continente": "detergente loica 500","pingodoce": "detergente loica",    "lidl": "detergente loica"},
    {"id": "tomate-kg",             "nome": "Tomate (kg)",            "emoji": "🍅", "categoria": "frutas-legumes","continente": "tomate",             "pingodoce": "tomate",              "lidl": "tomate"},
    {"id": "banana-kg",             "nome": "Banana (kg)",            "emoji": "🍌", "categoria": "frutas-legumes","continente": "banana",             "pingodoce": "banana",              "lidl": "banana"},
    {"id": "iogurte-natural-pack4", "nome": "Iogurte natural (pack 4)","emoji": "🥛","categoria": "lacticinios",  "continente": "iogurte natural 4",   "pingodoce": "iogurte natural pack","lidl": "iogurte natural"},
    {"id": "agua-5l",               "nome": "Água 5L",                "emoji": "💧", "categoria": "bebidas",      "continente": "agua 5l",             "pingodoce": "agua 5l",             "lidl": "agua 5l"},
    {"id": "manteiga-250g",         "nome": "Manteiga 250g",          "emoji": "🧈", "categoria": "lacticinios",  "continente": "manteiga 250g",       "pingodoce": "manteiga 250g",       "lidl": "manteiga 250g"},
    {"id": "cafe-delta-250g",       "nome": "Café Delta 250g",        "emoji": "☕", "categoria": "mercearia",    "continente": "cafe delta 250g",     "pingodoce": "cafe delta 250g",     "lidl": "cafe 250g"},
    {"id": "massa-esparguete-500g", "nome": "Massa esparguete 500g",  "emoji": "🍝", "categoria": "mercearia",    "continente": "esparguete 500g",     "pingodoce": "esparguete 500g",     "lidl": "esparguete 500g"},
]


# ─────────────────────────────────────────────
# CONTINENTE — usa API interna JSON
# ─────────────────────────────────────────────
def scrape_continente(query: str) -> dict | None:
    url = "https://www.continente.pt/on/demandware.store/Sites-continente-Site/pt_PT/Search-ProductHits"
    params = {
        "q": query,
        "start": 0,
        "sz": 1,
        "format": "page-element",
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        hits = data.get("hits", [])
        if not hits:
            return None
        p = hits[0]
        preco = p.get("price", {}).get("salesPrice", {}).get("value")
        nome  = p.get("productName", "")
        img   = p.get("images", [{}])[0].get("url", "")
        url_p = "https://www.continente.pt" + p.get("productURL", "")
        return {"preco": float(preco), "nome_real": nome, "imagem": img, "url": url_p} if preco else None
    except Exception as e:
        log.warning(f"Continente erro ({query}): {e}")
        return None


# ─────────────────────────────────────────────
# PINGO DOCE — usa API interna JSON
# ─────────────────────────────────────────────
def scrape_pingodoce(query: str) -> dict | None:
    url = "https://mercadao.pt/api/catalogues/64612e5a85898e08c8e24e29/products/search"
    params = {"query": query, "pageSize": 1, "pageNumber": 0}
    headers = {**HEADERS, "Accept": "application/json", "Origin": "https://mercadao.pt"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        produtos = data.get("products", [])
        if not produtos:
            return None
        p = produtos[0]
        preco = p.get("price")
        preco_promo = p.get("promotionalPrice")
        nome  = p.get("name", "")
        img   = (p.get("imageUrls") or [""])[0]
        url_p = f"https://mercadao.pt/store/pingo-doce/product/{p.get('id','')}"
        preco_final = float(preco_promo or preco) if (preco_promo or preco) else None
        em_promo = preco_promo is not None and preco_promo < preco
        return {"preco": preco_final, "nome_real": nome, "imagem": img, "url": url_p, "em_promocao": em_promo} if preco_final else None
    except Exception as e:
        log.warning(f"PingoDoce erro ({query}): {e}")
        return None


# ─────────────────────────────────────────────
# LIDL — usa API de pesquisa
# ─────────────────────────────────────────────
def scrape_lidl(query: str) -> dict | None:
    url = "https://www.lidl.pt/api/search"
    params = {"q": query, "page": 1, "pageSize": 1}
    headers = {**HEADERS, "Accept": "application/json"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = data.get("gridItems", [])
        if not items:
            return None
        p = items[0]
        preco = p.get("price", {}).get("price")
        nome  = p.get("name", "")
        img   = p.get("image", "")
        url_p = "https://www.lidl.pt" + p.get("url", "")
        return {"preco": float(preco), "nome_real": nome, "imagem": img, "url": url_p} if preco else None
    except Exception as e:
        log.warning(f"Lidl erro ({query}): {e}")
        return None


# ─────────────────────────────────────────────
# GUARDAR NO SUPABASE
# ─────────────────────────────────────────────
def guardar_preco(produto_id: str, supermercado: str, dados: dict):
    hoje = datetime.utcnow().date().isoformat()
    row = {
        "produto_id":    produto_id,
        "supermercado":  supermercado,
        "preco":         dados["preco"],
        "nome_real":     dados.get("nome_real", ""),
        "imagem":        dados.get("imagem", ""),
        "url":           dados.get("url", ""),
        "em_promocao":   dados.get("em_promocao", False),
        "data":          hoje,
        "atualizado_em": datetime.utcnow().isoformat(),
    }
    # Upsert: atualiza se já existe entrada para hoje
    supabase.table("precos").upsert(
        row,
        on_conflict="produto_id,supermercado,data"
    ).execute()
    log.info(f"  ✓ {supermercado}: {dados['preco']}€")


# ─────────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────────
def main():
    log.info(f"=== PoupeJá Scraper — {datetime.utcnow().date()} ===")
    log.info(f"Produtos a atualizar: {len(PRODUTOS)}")

    erros = 0
    sucessos = 0

    for produto in PRODUTOS:
        log.info(f"\n→ {produto['nome']}")

        scrapers = [
            ("continente", scrape_continente, produto["continente"]),
            ("pingodoce",  scrape_pingodoce,  produto["pingodoce"]),
            ("lidl",       scrape_lidl,       produto["lidl"]),
        ]

        for supermercado, fn, query in scrapers:
            dados = fn(query)
            if dados:
                guardar_preco(produto["id"], supermercado, dados)
                sucessos += 1
            else:
                log.warning(f"  ✗ {supermercado}: sem resultado")
                erros += 1
            time.sleep(1.5)  # pausa entre pedidos para não ser bloqueado

    log.info(f"\n=== Concluído: {sucessos} preços atualizados, {erros} erros ===")

    # Atualizar timestamp de última atualização
    supabase.table("config").upsert({
        "chave": "ultima_atualizacao",
        "valor": datetime.utcnow().isoformat()
    }, on_conflict="chave").execute()


if __name__ == "__main__":
    main()
