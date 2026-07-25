"""Filtros de relevância e intervalo de datas para vagas."""

import re
import unicodedata
from datetime import datetime

# Palavras genéricas que não definem a tecnologia/área buscada
PALAVRAS_GENERICAS = {
    "desenvolvedor", "desenvolvedora", "programador", "programadora",
    "analista", "engenheiro", "engenheira", "estagio", "estagiario",
    "estagiaria", "remoto", "remote", "hibrido", "presencial",
    "pleno", "senior", "junior", "vaga", "vagas", "emprego",
    "trabalho", "home", "office", "profissional", "tecnologia",
    "software", "full", "stack", "frontend", "backend", "dev",
    "de", "da", "do", "para", "com", "em", "e", "a", "o", "na",
    "no", "brasil", "brazil", "area", "busca", "oportunidade",
    "trainee", "assistente", "coordenador", "coordenadora", "gerente",
    "consultor", "consultora", "especialista", "tecnico", "tecnica",
}

# Sinônimos de tecnologias
ALIASES_TECNOLOGIA = {
    "delphi": ("delphi", "object pascal", "objectpascal", "embarcadero", "rad studio", "radstudio"),
    "python": ("python",),
    "java": ("java", "kotlin"),
    "react": ("react", "reactjs", "react.js"),
    "angular": ("angular", "angularjs"),
    "vue": ("vue", "vuejs", "vue.js"),
    "net": (".net", "dotnet", "dot net", "c#", "csharp"),
}

FORMATOS_DATA = (
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
)


def _normalizar(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def _tokenizar(termo):
    """Separa o termo em tokens preservando tecnologias como c#, c++ e .net."""
    termo = termo.strip()
    padrao = r"[a-zA-ZÀ-ÿ#.+]+\+?|\d+"
    return re.findall(padrao, termo)


def _extrair_obrigatorios(termo):
    tokens = _tokenizar(termo)
    obrigatorios = []
    for tok in tokens:
        norm = _normalizar(tok)
        if len(norm) < 2 and norm not in {"c", "r"}:
            continue
        if norm in PALAVRAS_GENERICAS:
            continue
        obrigatorios.append(norm)
    if not obrigatorios:
        obrigatorios = [_normalizar(t) for t in tokens if len(_normalizar(t)) >= 3]
    return obrigatorios


def _texto_titulo_descricao(vaga=None, titulo="", descricao=""):
    """Usa somente título e descrição da vaga — não o corpo inteiro da página."""
    if isinstance(vaga, dict):
        titulo = vaga.get("titulo") or ""
        descricao = vaga.get("descricao") or ""
    return _normalizar(f"{titulo} {descricao}")


def _termo_tecnico_no_texto(termo_tecnico, texto):
    """Verifica se o termo técnico aparece no título ou na descrição da vaga."""
    aliases = ALIASES_TECNOLOGIA.get(termo_tecnico, (termo_tecnico,))
    for alias in aliases:
        norm_alias = _normalizar(alias)
        if not norm_alias:
            continue
        if norm_alias in texto:
            return True
        if norm_alias == "c#" and re.search(r"c\s*#|csharp", texto, re.I):
            return True
        if norm_alias == ".net" and re.search(r"\.net|dotnet|dot\s*net", texto, re.I):
            return True
        if norm_alias in ("c++",) and re.search(r"c\s*\+\s*\+", texto, re.I):
            return True
    return False


def extrair_termos_tecnicos(termo):
    """Retorna tokens técnicos do termo de busca (ex: delphi, python)."""
    return _extrair_obrigatorios(termo)


def vaga_relevante(termo, titulo="", descricao="", vaga=None, **_kwargs):
    """
    Mantém a vaga somente se o termo da inclusão aparecer no TÍTULO ou na DESCRIÇÃO.

    Não considera rodapé, menu, anúncios ou outros textos da página do site.
    """
    texto = _texto_titulo_descricao(vaga=vaga, titulo=titulo, descricao=descricao)
    if not texto.strip():
        return False

    termos_tecnicos = _extrair_obrigatorios(termo)
    if not termos_tecnicos:
        termo_norm = _normalizar(termo)
        return len(termo_norm) >= 3 and termo_norm in texto

    return any(_termo_tecnico_no_texto(t, texto) for t in termos_tecnicos)


def parse_data(valor):
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    texto = str(valor).strip()
    for fmt in FORMATOS_DATA:
        try:
            return datetime.strptime(texto[:len(fmt.replace("%", "0")) if "%H" in fmt else 10], fmt).date()
        except ValueError:
            try:
                return datetime.strptime(texto[:10], fmt).date()
            except ValueError:
                continue
    match = re.search(r"(\d{4}-\d{2}-\d{2})", texto)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def dentro_intervalo(data_valor, data_inicio=None, data_fim=None):
    """Filtra por data de publicação. Sem data na vaga, mantém (não descarta)."""
    if not data_inicio and not data_fim:
        return True

    data = parse_data(data_valor)
    if data is None:
        return True

    inicio = parse_data(data_inicio) if data_inicio else None
    fim = parse_data(data_fim) if data_fim else None

    if inicio and data < inicio:
        return False
    if fim and data > fim:
        return False
    return True


def filtrar_vagas(vagas, termo, data_inicio=None, data_fim=None):
    """Aplica filtro de relevância (título/descrição) e intervalo de datas."""
    resultado = []
    for vaga in vagas:
        if not vaga_relevante(termo, vaga=vaga):
            continue
        if not dentro_intervalo(vaga.get("data_publicacao"), data_inicio, data_fim):
            continue
        resultado.append(vaga)
    return resultado
