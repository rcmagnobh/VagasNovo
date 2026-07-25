"""Robô de captura de vagas via web scraping."""

from datetime import datetime

import pandas as pd

from database import db
from scraper.filtros import filtrar_vagas
from scraper.sites import SCRAPERS, SITES_DISPONIVEIS, buscar_em_todos_sites
from scraper.vaga_utils import enriquecer_vaga


def _deduplicar_dataframe(vagas):
    if not vagas:
        return []
    df = pd.DataFrame(vagas)
    df = df.drop_duplicates(subset=["link"], keep="first")
    df["titulo"] = df["titulo"].astype(str).str.strip()
    if "cargo" not in df.columns:
        df["cargo"] = df["titulo"]
    df["cargo"] = df["cargo"].astype(str).str.strip()
    df["empresa"] = df["empresa"].astype(str).str.strip()
    return df.to_dict("records")


def _mesclar_vagas_unicas(destino, novas):
    """Mescla vagas por link sem duplicar entre termos de busca."""
    for vaga in novas:
        link = vaga.get("link")
        if not link:
            continue
        if link not in destino:
            destino[link] = vaga
        elif not destino[link].get("palavra_chave"):
            destino[link]["palavra_chave"] = vaga.get("palavra_chave")


def executar_busca(termos=None, max_paginas=2, sites=None, data_inicio=None, data_fim=None):
    """Executa busca para todos os termos ativos e persiste no banco."""
    db.init_db()
    hora_inicio = datetime.now()

    if data_inicio is None and data_fim is None:
        data_inicio, data_fim = db.get_intervalo_busca()

    if termos is None:
        termos = [p["termo"] for p in db.listar_palavras_chave(apenas_ativas=True)]

    if not termos:
        hora_fim = datetime.now()
        db.registrar_historico_busca("", 0, 0, "Nenhuma palavra-chave ativa configurada.")
        return {
            "total_encontradas": 0,
            "total_unicas": 0,
            "total_novas": 0,
            "total_ja_existentes": 0,
            "total_filtradas": 0,
            "total_brutas": 0,
            "total_cadastro": db.contar_vagas(),
            "termos": [],
            "sites": list(SITES_DISPONIVEIS),
            "vagas": [],
            "hora_inicio": hora_inicio,
            "hora_fim": hora_fim,
            "duracao_segundos": (hora_fim - hora_inicio).total_seconds(),
            "avisos": [],
        }

    resultado_geral = {
        "total_encontradas": 0,
        "total_unicas": 0,
        "total_novas": 0,
        "total_ja_existentes": 0,
        "total_filtradas": 0,
        "total_brutas": 0,
        "total_cadastro": 0,
        "termos": [],
        "sites": list(SITES_DISPONIVEIS),
        "vagas": [],
        "hora_inicio": hora_inicio,
        "hora_fim": None,
        "duracao_segundos": 0,
        "avisos": [],
    }
    vagas_unicas = {}
    avisos_gerais = []

    for termo in termos:
        if sites:
            vagas = []
            for site in sites:
                scraper = SCRAPERS.get(site)
                if scraper:
                    try:
                        vagas.extend(scraper(termo, max_paginas, data_inicio=data_inicio, data_fim=data_fim))
                    except Exception:
                        continue
        else:
            vagas, avisos = buscar_em_todos_sites(termo, max_paginas, data_inicio, data_fim)
            avisos_gerais.extend(avisos)

        brutas = len(vagas)
        vagas = filtrar_vagas(vagas, termo, data_inicio, data_fim)
        vagas = [enriquecer_vaga(v, termo) for v in vagas]
        vagas = _deduplicar_dataframe(vagas)
        filtradas = brutas - len(vagas)

        novas = 0
        ja_existentes = 0
        for vaga in vagas:
            if db.inserir_vaga(vaga):
                novas += 1
            else:
                ja_existentes += 1

        encontradas = len(vagas)
        resultado_geral["total_encontradas"] += encontradas
        resultado_geral["total_brutas"] += brutas
        resultado_geral["total_novas"] += novas
        resultado_geral["total_ja_existentes"] += ja_existentes
        resultado_geral["total_filtradas"] += filtradas
        resultado_geral["termos"].append({
            "termo": termo,
            "encontradas": encontradas,
            "novas": novas,
            "ja_existentes": ja_existentes,
            "descartadas": filtradas,
            "brutas": brutas,
        })
        _mesclar_vagas_unicas(vagas_unicas, vagas)

        intervalo = ""
        if data_inicio or data_fim:
            intervalo = f" | Período: {data_inicio or '...'} a {data_fim or '...'}"

        db.registrar_historico_busca(
            termo,
            encontradas,
            novas,
            f"Busca em {len(SITES_DISPONIVEIS)} sites: {brutas} brutas, "
            f"{encontradas} relevantes, {filtradas} descartadas, "
            f"{novas} novas, {ja_existentes} já no cadastro{intervalo}.",
        )

    resultado_geral["vagas"] = list(vagas_unicas.values())
    resultado_geral["total_unicas"] = len(vagas_unicas)
    resultado_geral["total_cadastro"] = db.contar_vagas()
    resultado_geral["avisos"] = list(dict.fromkeys(avisos_gerais))

    hora_fim = datetime.now()
    resultado_geral["hora_fim"] = hora_fim
    resultado_geral["duracao_segundos"] = (hora_fim - hora_inicio).total_seconds()
    return resultado_geral


if __name__ == "__main__":
    resultado = executar_busca()
    print(f"Busca finalizada: {resultado}")
