"""Utilitários para enriquecer vagas: score, localização, tipo e dias publicados."""

import re
from datetime import datetime

from scraper.filtros import (
    _extrair_obrigatorios,
    _normalizar,
    _termo_tecnico_no_texto,
    parse_data,
)

TIPOS_VAGA = ("Presencial", "Remota", "Híbrida", "Não informado")

UF_PARA_ESTADO = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}

PALAVRAS_REMOTA = (
    "remoto", "remote", "home office", "homeoffice", "trabalho remoto",
    "100% remoto", "fully remote", "anywhere", "work from home", "wfh",
)
PALAVRAS_HIBRIDA = (
    "hibrido", "híbrido", "hybrid", "semi-presencial", "semipresencial",
    "híbrido flexível", "hibrido flexivel",
)
PALAVRAS_PRESENCIAL = (
    "presencial", "on-site", "onsite", "no escritorio", "no escritório",
    "in office", "in-office",
)

PAISES = {
    "brasil": "Brasil", "brazil": "Brasil",
    "portugal": "Portugal", "argentina": "Argentina",
    "estados unidos": "Estados Unidos", "usa": "Estados Unidos",
    "united states": "Estados Unidos", "eua": "Estados Unidos",
    "espanha": "Espanha", "spain": "Espanha",
    "mexico": "México", "méxico": "México",
    "colombia": "Colômbia", "colômbia": "Colômbia",
    "chile": "Chile", "uruguai": "Uruguai", "paraguai": "Paraguai",
}


def calcular_dias_postado(data_publicacao):
    """Retorna quantos dias se passaram desde a publicação."""
    data = parse_data(data_publicacao)
    if data is None:
        return None
    return (datetime.now().date() - data).days


def formatar_dias_postado(dias):
    """Texto amigável para exibição dos dias desde a publicação."""
    if dias is None:
        return "—"
    if dias == 0:
        return "Hoje"
    if dias == 1:
        return "1 dia"
    return f"{dias} dias"


def detectar_tipo_vaga(titulo="", descricao="", localizacao="", fonte=""):
    """Detecta Presencial, Remota ou Híbrida a partir do conteúdo da vaga."""
    texto = _normalizar(f"{titulo} {descricao} {localizacao}")
    fonte_norm = _normalizar(fonte or "")

    if any(p in texto for p in PALAVRAS_REMOTA):
        if any(p in texto for p in PALAVRAS_HIBRIDA):
            return "Híbrida"
        if any(p in texto for p in PALAVRAS_PRESENCIAL):
            return "Híbrida"
        return "Remota"

    if any(p in texto for p in PALAVRAS_HIBRIDA):
        return "Híbrida"

    if any(p in texto for p in PALAVRAS_PRESENCIAL):
        return "Presencial"

    loc_norm = _normalizar(localizacao or "")
    if loc_norm in ("remoto", "remote", "home office", "homeoffice"):
        return "Remota"

    if fonte_norm in ("remotar", "upwork", "toptal", "revelo"):
        return "Remota"

    return "Não informado"


def parse_localizacao(localizacao="", fonte=""):
    """Extrai cidade, estado e país de uma string de localização."""
    cidade = estado = pais = ""

    if not localizacao or not str(localizacao).strip():
        if _normalizar(fonte) in ("remotar", "upwork", "toptal", "revelo"):
            pais = "Brasil"
        return cidade, estado, pais

    texto = _limpar_localizacao(localizacao)
    texto_norm = _normalizar(texto)

    if texto_norm in ("remoto", "remote", "home office", "homeoffice", "anywhere"):
        return "", "", "Brasil"

    for chave, nome in PAISES.items():
        if re.search(rf"\b{re.escape(chave)}\b", texto_norm):
            pais = nome
            break

    partes = re.split(r"[,;\-|/]+", texto)
    partes = [p.strip() for p in partes if p.strip()]

    if len(partes) >= 2:
        uf_segunda = _extrair_uf(partes[1])
        if uf_segunda and len(partes[1].strip()) <= 3:
            cidade = partes[0]
            estado = _nome_estado_por_uf(uf_segunda)
        else:
            for parte in reversed(partes):
                uf = _extrair_uf(parte)
                if uf:
                    estado = _nome_estado_por_uf(uf)
                    break
            if partes and not cidade:
                primeira = partes[0]
                if not _extrair_uf(primeira) and _normalizar(primeira) not in PAISES:
                    cidade = primeira
    elif len(partes) == 1:
        uf = _extrair_uf(partes[0])
        if uf:
            estado = _nome_estado_por_uf(uf)
        elif _normalizar(partes[0]) not in PAISES:
            cidade = partes[0]

    if not pais:
        pais = "Brasil" if estado or cidade else ""

    return cidade, estado, pais


def calcular_score(termo, vaga):
    """
    Score de relevância 0–100.
    Título pesa mais que descrição; todos os termos técnicos devem ser considerados.
    """
    termos = _extrair_obrigatorios(termo)
    titulo = _normalizar(vaga.get("cargo") or vaga.get("titulo") or "")
    descricao = _normalizar(vaga.get("descricao") or "")

    if not termos:
        texto = f"{titulo} {descricao}"
        termo_norm = _normalizar(termo)
        if len(termo_norm) >= 3 and termo_norm in texto:
            return 80 if termo_norm in titulo else 50
        return 30

    max_pontos = len(termos) * 3
    pontos = 0
    for t in termos:
        if _termo_tecnico_no_texto(t, titulo):
            pontos += 3
        elif _termo_tecnico_no_texto(t, descricao):
            pontos += 1

    if max_pontos == 0:
        return 50
    return min(100, round((pontos / max_pontos) * 100))


def enriquecer_vaga(vaga, termo=None):
    """Preenche cargo, score, localização estruturada, tipo e dias publicados."""
    if not vaga:
        return vaga

    titulo = vaga.get("titulo") or vaga.get("cargo") or ""
    vaga["titulo"] = titulo
    vaga["cargo"] = titulo

    localizacao = vaga.get("localizacao") or ""
    fonte = vaga.get("fonte") or ""
    descricao = vaga.get("descricao") or ""

    cidade, estado, pais = parse_localizacao(localizacao, fonte)
    vaga["cidade"] = cidade
    vaga["estado"] = estado
    vaga["pais"] = pais

    vaga["tipo_vaga"] = detectar_tipo_vaga(titulo, descricao, localizacao, fonte)

    dias = calcular_dias_postado(vaga.get("data_publicacao"))
    vaga["dias_postado"] = dias

    if termo:
        vaga["score"] = calcular_score(termo, vaga)
    elif vaga.get("palavra_chave"):
        vaga["score"] = calcular_score(vaga["palavra_chave"], vaga)
    else:
        vaga["score"] = vaga.get("score") or 0

    return vaga


def _limpar_localizacao(texto):
    return re.sub(r"\s+", " ", str(texto)).strip()


def _extrair_uf(parte):
    parte = parte.strip()
    match = re.search(r"^([A-Z]{2})$", parte)
    if match and match.group(1) in UF_PARA_ESTADO:
        return match.group(1)
    match = re.search(r"\b([A-Z]{2})\b", parte)
    if match and match.group(1) in UF_PARA_ESTADO:
        return match.group(1)
    return None


def _nome_estado_por_uf(uf):
    return UF_PARA_ESTADO.get(uf, uf)


def formatar_localizacao(vaga):
    """Exibe Cidade, Estado — País de forma compacta."""
    cidade = vaga.get("cidade") or ""
    estado = vaga.get("estado") or ""
    pais = vaga.get("pais") or ""
    loc = vaga.get("localizacao") or ""

    if cidade and estado:
        local = f"{cidade}, {estado}"
    elif cidade:
        local = cidade
    elif estado:
        local = estado
    elif loc:
        local = loc
    else:
        local = "—"

    if pais and pais not in local:
        return f"{local} — {pais}"
    return local


def cor_score(score):
    """Retorna cor do badge de score."""
    if score is None:
        return "#94a3b8", "#f1f5f9"
    if score >= 80:
        return "#166534", "#dcfce7"
    if score >= 50:
        return "#92400e", "#fef3c7"
    return "#991b1b", "#fee2e2"


def cor_tipo_vaga(tipo):
    """Retorna cor do badge de tipo de vaga."""
    cores = {
        "Remota": ("#065f46", "#d1fae5"),
        "Híbrida": ("#5b21b6", "#ede9fe"),
        "Presencial": ("#1e40af", "#dbeafe"),
        "Não informado": ("#475569", "#f1f5f9"),
    }
    return cores.get(tipo, cores["Não informado"])
