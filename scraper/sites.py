"""Scrapers por portal de vagas."""

import re
import time
from datetime import datetime
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from scraper.filtros import extrair_termos_tecnicos
from scraper.vaga_utils import enriquecer_vaga

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

SITES_DISPONIVEIS = (
    "LinkedIn",
    "Vagas.com.br",
    "Catho",
    "Indeed",
    "Glassdoor",
    "GeekHunter",
    "Revelo",
    "Coodesh",
    "Trampos.co",
    "Jerimum Jobs",
    "Remotar",
    "Upwork",
    "Toptal",
)

SITES_PLAYWRIGHT = {"Catho", "Indeed", "Revelo", "Coodesh", "Upwork"}


def _limpar_texto(texto):
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto).strip()


def _variantes_busca(termo):
    """Gera termos alternativos para ampliar busca nos portais."""
    variantes = [termo.strip()]
    tecnicos = extrair_termos_tecnicos(termo)
    for t in tecnicos:
        if t not in {v.lower() for v in variantes}:
            variantes.append(t)
    if "remoto" in termo.lower() and termo not in variantes:
        base = " ".join(tecnicos) if tecnicos else termo
        combo = f"{base} remoto".strip()
        if combo not in variantes:
            variantes.append(combo)
    return variantes


def _slug(termo):
    texto = re.sub(r"[^\w\s#+.]", "", termo.lower())
    return re.sub(r"\s+", "-", texto.strip())


def _criar_vaga(titulo, empresa, link, termo, fonte, localizacao="", descricao="", data_publicacao=None,
                cidade="", estado="", pais="", tipo_vaga=""):
    titulo = _limpar_texto(titulo)
    link = _limpar_texto(link)
    if not titulo or not link:
        return None
    vaga = {
        "titulo": titulo,
        "cargo": titulo,
        "empresa": _limpar_texto(empresa) or "Não informada",
        "localizacao": _limpar_texto(localizacao),
        "link": link,
        "descricao": _limpar_texto(descricao),
        "data_publicacao": data_publicacao,
        "palavra_chave": termo,
        "fonte": fonte,
        "cidade": _limpar_texto(cidade),
        "estado": _limpar_texto(estado),
        "pais": _limpar_texto(pais),
        "tipo_vaga": _limpar_texto(tipo_vaga),
    }
    return enriquecer_vaga(vaga, termo)


def _get(url, params=None, timeout=20):
    resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp


def _dias_desde(inicio_iso):
    if not inicio_iso:
        return None
    try:
        inicio = datetime.strptime(inicio_iso[:10], "%Y-%m-%d").date()
        return (datetime.now().date() - inicio).days
    except ValueError:
        return None


# --- LinkedIn ---
def buscar_linkedin(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    vistos = set()
    dias = _dias_desde(data_inicio)
    f_tpr = None
    if dias is not None:
        if dias <= 1:
            f_tpr = "r86400"
        elif dias <= 7:
            f_tpr = "r604800"
        elif dias <= 30:
            f_tpr = "r2592000"

    for busca in _variantes_busca(termo):
        for pagina in range(max_paginas):
            params = {
                "keywords": busca,
                "location": "Brasil",
                "geoId": "106057199",
                "start": pagina * 25,
            }
            if f_tpr:
                params["f_TPR"] = f_tpr
            try:
                resp = _get("https://www.linkedin.com/jobs/search/", params=params)
            except requests.RequestException:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.base-card")
            if not cards:
                break

            for card in cards:
                link_el = card.select_one("a.base-card__full-link")
                titulo_el = card.select_one("h3, .base-search-card__title")
                empresa_el = card.select_one("h4, .base-search-card__subtitle")
                local_el = card.select_one(".job-search-card__location")
                snippet_el = card.select_one(
                    ".base-search-card__snippet, .job-search-card__snippet, .base-card__snippet"
                )
                if not link_el or not titulo_el:
                    continue
                link = link_el["href"].split("?")[0]
                if link in vistos:
                    continue
                vistos.add(link)
                vaga = _criar_vaga(
                    titulo=titulo_el.get_text(),
                    empresa=empresa_el.get_text() if empresa_el else "",
                    link=link,
                    termo=termo,
                    fonte="LinkedIn",
                    localizacao=local_el.get_text() if local_el else "",
                    descricao=snippet_el.get_text() if snippet_el else "",
                )
                if vaga:
                    vagas.append(vaga)
            time.sleep(1)
    return vagas


# --- Vagas.com.br ---
def buscar_vagas_com_br(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    vistos = set()
    for busca in _variantes_busca(termo):
        slug = _slug(busca)
        for pagina in range(1, max_paginas + 1):
            url = f"https://www.vagas.com.br/vagas-de-{quote_plus(slug)}?pagina={pagina}"
            try:
                resp = _get(url)
            except requests.RequestException:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("li.vaga")
            if not cards:
                break

            for card in cards:
                titulo_el = card.select_one("h2.cargo a, a.vaga-title, h3 a")
                empresa_el = card.select_one("span.emprVaga, .company, .empresa")
                local_el = card.select_one("span.localvaga, .localidade")
                desc_el = card.select_one("p.descricao, .description")
                if not titulo_el:
                    continue
                link = titulo_el.get("href", "")
                if link and not link.startswith("http"):
                    link = urljoin("https://www.vagas.com.br", link)
                if link in vistos:
                    continue
                vistos.add(link)
                vaga = _criar_vaga(
                    titulo=titulo_el.get_text(),
                    empresa=empresa_el.get_text() if empresa_el else "",
                    link=link,
                    termo=termo,
                    fonte="Vagas.com.br",
                    localizacao=local_el.get_text() if local_el else "",
                    descricao=desc_el.get_text() if desc_el else "",
                )
                if vaga:
                    vagas.append(vaga)
            time.sleep(1)
    return vagas


# --- Glassdoor ---
def buscar_glassdoor(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    for pagina in range(1, max_paginas + 1):
        params = {"sc.keyword": termo, "p": pagina}
        try:
            resp = _get("https://www.glassdoor.com.br/Vaga/jobs.htm", params=params)
        except requests.RequestException:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.jobCard")
        if not cards:
            break

        for card in cards:
            titulo_el = card.select_one("a[data-test='job-title'], .JobCard_jobTitle__GLyJ1")
            empresa_el = card.select_one(".EmployerProfile_compactEmployerName__9MGcV")
            local_el = card.select_one("[data-test='emp-location'], .JobCard_location__Ds1fM")
            desc_el = card.select_one("[data-test='descSnippet'], .JobCard_jobDescriptionSnippet__l1tnl")
            if not titulo_el:
                continue
            link = titulo_el.get("href", "")
            if link and not link.startswith("http"):
                link = urljoin("https://www.glassdoor.com.br", link)
            vaga = _criar_vaga(
                titulo=titulo_el.get_text(),
                empresa=empresa_el.get_text() if empresa_el else "",
                link=link,
                termo=termo,
                fonte="Glassdoor",
                localizacao=local_el.get_text() if local_el else "",
                descricao=desc_el.get_text() if desc_el else "",
            )
            if vaga:
                vagas.append(vaga)
        time.sleep(1)
    return vagas


# --- GeekHunter ---
def buscar_geekhunter(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    vistos = set()
    for busca in _variantes_busca(termo):
        for pagina in range(1, max_paginas + 1):
            params = {"q": busca, "page": pagina}
            try:
                resp = _get("https://www.geekhunter.com.br/pt/vagas", params=params)
            except requests.RequestException:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select('a[href*="/jobs/"]')
            if not links:
                break

            for link_el in links:
                link = link_el["href"]
                if not link.startswith("http"):
                    link = urljoin("https://www.geekhunter.com.br", link)
                if link in vistos:
                    continue
                vistos.add(link)
                titulo = _limpar_texto(link_el.get_text())
                titulo = re.split(r"Publicada", titulo, maxsplit=1)[0].strip()
                if not titulo:
                    slug = link.rstrip("/").split("/")[-1]
                    titulo = slug.replace("-", " ").title()
                partes = link.split("/")
                empresa = partes[4].replace("-", " ").title() if len(partes) > 4 else "Não informada"
                vaga = _criar_vaga(
                    titulo=titulo,
                    empresa=empresa,
                    link=link,
                    termo=termo,
                    fonte="GeekHunter",
                )
                if vaga:
                    vagas.append(vaga)
            time.sleep(1)
    return vagas


# --- Trampos.co ---
def buscar_trampos(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    vistos = set()
    limite_paginas = max(max_paginas * 4, 6)

    for pagina in range(1, limite_paginas + 1):
        try:
            resp = _get("https://trampos.co/api/oportunidades", params={"page": pagina})
        except requests.RequestException:
            break

        dados = resp.json()
        if not isinstance(dados, list) or not dados:
            break

        for item in dados:
            opp = item.get("opportunity", item)
            titulo = opp.get("name", "")
            descricao = opp.get("description", "") or ""
            if isinstance(descricao, str) and descricao.startswith("<"):
                descricao = BeautifulSoup(descricao, "html.parser").get_text()
            link = opp.get("permalink", "")
            if not titulo or not link or link in vistos:
                continue
            vistos.add(link)
            vaga = _criar_vaga(
                titulo=titulo,
                empresa=opp.get("company_name", ""),
                link=link,
                termo=termo,
                fonte="Trampos.co",
                descricao=descricao,
                data_publicacao=opp.get("published_at"),
            )
            if vaga:
                vagas.append(vaga)

        time.sleep(0.5)
    return vagas


# --- Jerimum Jobs ---
def buscar_jerimum(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    base = "https://jerimumjobs.imd.ufrn.br"
    try:
        resp = _get(f"{base}/jerimumjobs/oportunidade/listar")
    except requests.RequestException:
        return vagas

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.select("a[href*='/jerimumjobs/oportunidade/']"):
        href = a.get("href", "")
        if href.endswith("listar"):
            continue
        titulo_el = a.find("h6") or a
        titulo = titulo_el.get_text(separator=" ").strip()
        if not titulo or titulo.lower() in {"vagas", "visualizar vaga"}:
            continue
        link = urljoin(base, href)
        local = ""
        texto = a.get_text(separator="\n")
        if "Remoto" in texto:
            local = "Remoto"
        vaga = _criar_vaga(
            titulo=titulo.split("\n")[0],
            empresa="",
            link=link,
            termo=termo,
            fonte="Jerimum Jobs",
            localizacao=local,
        )
        if vaga:
            vagas.append(vaga)
    return vagas


# --- Remotar (API) ---
def buscar_remotar(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    vistos = set()
    for busca in _variantes_busca(termo):
        for pagina in range(1, max_paginas + 1):
            params = {"search": busca, "page": pagina, "per_page": 30}
            try:
                resp = _get("https://api.remotar.com.br/jobs", params=params)
            except requests.RequestException:
                break

            dados = resp.json().get("data", [])
            if not dados:
                break

            for job in dados:
                link = job.get("externalLink") or f"https://remotar.com.br/job/{job.get('id', '')}"
                if link in vistos:
                    continue
                vistos.add(link)
                desc = BeautifulSoup(job.get("description") or "", "html.parser").get_text()
                titulo = job.get("title", "")
                vaga = _criar_vaga(
                    titulo=titulo,
                    empresa=(job.get("company") or {}).get("name", job.get("companyDisplayName", "")),
                    link=link,
                    termo=termo,
                    fonte="Remotar",
                    localizacao=job.get("city") or ("Remoto" if job.get("type") == "remote" else ""),
                    descricao=desc[:500],
                    data_publicacao=job.get("createdAt"),
                )
                if vaga:
                    vagas.append(vaga)
            time.sleep(0.5)
    return vagas


# --- Toptal ---
def buscar_toptal(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    try:
        resp = _get("https://www.toptal.com/careers")
    except requests.RequestException:
        return vagas

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.select("a[href*='/careers/']"):
        href = a.get("href", "")
        if href in ("/careers", "/careers/"):
            continue
        titulo = _limpar_texto(a.get_text())
        if not titulo or len(titulo) < 5:
            continue
        link = urljoin("https://www.toptal.com", href)
        vaga = _criar_vaga(
            titulo=titulo.replace("Apply", "").strip(),
            empresa="Toptal",
            link=link,
            termo=termo,
            fonte="Toptal",
        )
        if vaga:
            vagas.append(vaga)
    return vagas


# --- Playwright: Indeed ---
def buscar_indeed(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    vagas = []
    if page is None:
        return _buscar_indeed_requests(termo, max_paginas, data_inicio)

    fromage = _dias_desde(data_inicio) or 30
    fromage = min(max(fromage, 1), 30)

    for pagina in range(max_paginas):
        start = pagina * 10
        url = f"https://br.indeed.com/jobs?q={quote_plus(termo)}&start={start}&fromage={fromage}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)
            cards = page.query_selector_all("div.job_seen_beacon, div[data-jk], .tapItem")
            if not cards:
                break
            for card in cards:
                titulo_el = card.query_selector("h2 a span, h2.jobTitle span, a.jcs-JobTitle")
                empresa_el = card.query_selector(".companyName, [data-testid='company-name']")
                local_el = card.query_selector(".companyLocation, [data-testid='text-location']")
                link_el = card.query_selector("h2 a, a.jcs-JobTitle")
                if not titulo_el or not link_el:
                    continue
                href = link_el.get_attribute("href") or ""
                link = urljoin("https://br.indeed.com", href.split("?")[0])
                vaga = _criar_vaga(
                    titulo=titulo_el.inner_text(),
                    empresa=empresa_el.inner_text() if empresa_el else "",
                    link=link,
                    termo=termo,
                    fonte="Indeed",
                    localizacao=local_el.inner_text() if local_el else "",
                )
                if vaga:
                    vagas.append(vaga)
        except Exception:
            break
        time.sleep(1)
    return vagas if vagas else _buscar_indeed_requests(termo, max_paginas, data_inicio)


def _buscar_indeed_requests(termo, max_paginas, data_inicio):
    vagas = []
    fromage = _dias_desde(data_inicio) or 30
    fromage = min(max(fromage, 1), 30)
    for pagina in range(max_paginas):
        start = pagina * 10
        url = f"https://br.indeed.com/jobs?q={quote_plus(termo)}&start={start}&fromage={fromage}"
        try:
            resp = _get(url)
        except requests.RequestException:
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.job_seen_beacon, div[data-jk]")
        for card in cards:
            titulo_el = card.select_one("h2.jobTitle span, h2 a, a.jcs-JobTitle span")
            empresa_el = card.select_one(".companyName, [data-testid='company-name']")
            local_el = card.select_one(".companyLocation")
            link_el = card.select_one("h2 a, a.jcs-JobTitle")
            if not titulo_el or not link_el:
                continue
            link = urljoin("https://br.indeed.com", link_el.get("href", "").split("?")[0])
            vaga = _criar_vaga(
                titulo=titulo_el.get_text(),
                empresa=empresa_el.get_text() if empresa_el else "",
                link=link,
                termo=termo,
                fonte="Indeed",
                localizacao=local_el.get_text() if local_el else "",
            )
            if vaga:
                vagas.append(vaga)
        time.sleep(1)
    return vagas


# --- Playwright: Catho ---
def buscar_catho(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    if page is None:
        return []
    vagas = []
    slug = _slug(termo)
    urls = [
        f"https://www.catho.com.br/vagas/palavra-chave/{slug}/",
        f"https://www.catho.com.br/vagas/{slug}/",
    ]
    for url in urls:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)
            cards = page.query_selector_all(
                "a[href*='/vagas/'], article, div[data-testid*='job'], .sc-"
            )
            for card in cards[:40]:
                link_el = card if card.evaluate("el => el.tagName === 'A'") else card.query_selector("a")
                if not link_el:
                    continue
                href = link_el.get_attribute("href") or ""
                if not href or "palavra-chave" in href or href.endswith("/vagas/"):
                    continue
                titulo = _limpar_texto(link_el.inner_text())
                if len(titulo) < 4:
                    continue
                link = urljoin("https://www.catho.com.br", href)
                vaga = _criar_vaga(
                    titulo=titulo,
                    empresa="",
                    link=link,
                    termo=termo,
                    fonte="Catho",
                )
                if vaga:
                    vagas.append(vaga)
            if vagas:
                break
        except Exception:
            continue
    return vagas


# --- Playwright: Coodesh ---
def buscar_coodesh(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    if page is None:
        return []
    vagas = []
    try:
        page.goto(
            f"https://coodesh.com/jobs?search={quote_plus(termo)}",
            wait_until="networkidle",
            timeout=60000,
        )
        links = page.query_selector_all("a[href*='/jobs/']")
        vistos = set()
        for link_el in links:
            href = link_el.get_attribute("href") or ""
            if not href or href in vistos:
                continue
            vistos.add(href)
            titulo = _limpar_texto(link_el.inner_text())
            if len(titulo) < 4:
                continue
            link = urljoin("https://coodesh.com", href)
            vaga = _criar_vaga(
                titulo=titulo,
                empresa="",
                link=link,
                termo=termo,
                fonte="Coodesh",
            )
            if vaga:
                vagas.append(vaga)
    except Exception:
        pass
    return vagas


# --- Playwright: Revelo ---
def buscar_revelo(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    if page is None:
        return []
    vagas = []
    urls = [
        f"https://jobs.revelo.com.br/?search={quote_plus(termo)}",
        "https://app.careers.revelo.com/",
    ]
    for url in urls:
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(2)
            links = page.query_selector_all("a[href*='job'], a[href*='career'], a[href*='vaga']")
            for link_el in links:
                href = link_el.get_attribute("href") or ""
                titulo = _limpar_texto(link_el.inner_text())
                if len(titulo) < 5 or not href:
                    continue
                link = urljoin(url, href)
                vaga = _criar_vaga(
                    titulo=titulo,
                    empresa="Revelo",
                    link=link,
                    termo=termo,
                    fonte="Revelo",
                )
                if vaga:
                    vagas.append(vaga)
            if vagas:
                break
        except Exception:
            continue
    return vagas


# --- Playwright: Upwork ---
def buscar_upwork(termo, max_paginas=2, page=None, data_inicio=None, data_fim=None):
    if page is None:
        return []
    vagas = []
    try:
        page.goto(
            f"https://www.upwork.com/nx/search/jobs/?q={quote_plus(termo)}",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        time.sleep(3)
        cards = page.query_selector_all("article, [data-test='job-tile'], .job-tile")
        for card in cards:
            titulo_el = card.query_selector("h2, h3, a[href*='/jobs/']")
            link_el = card.query_selector("a[href*='/jobs/']")
            if not titulo_el:
                continue
            titulo = _limpar_texto(titulo_el.inner_text())
            link = ""
            if link_el:
                href = link_el.get_attribute("href") or ""
                link = urljoin("https://www.upwork.com", href)
            vaga = _criar_vaga(
                titulo=titulo,
                empresa="Upwork",
                link=link or f"https://www.upwork.com/nx/search/jobs/?q={quote_plus(termo)}",
                termo=termo,
                fonte="Upwork",
            )
            if vaga:
                vagas.append(vaga)
    except Exception:
        pass
    return vagas


SCRAPERS = {
    "LinkedIn": buscar_linkedin,
    "Vagas.com.br": buscar_vagas_com_br,
    "Catho": buscar_catho,
    "Indeed": buscar_indeed,
    "Glassdoor": buscar_glassdoor,
    "GeekHunter": buscar_geekhunter,
    "Revelo": buscar_revelo,
    "Coodesh": buscar_coodesh,
    "Trampos.co": buscar_trampos,
    "Jerimum Jobs": buscar_jerimum,
    "Remotar": buscar_remotar,
    "Upwork": buscar_upwork,
    "Toptal": buscar_toptal,
}


def _configurar_playwright():
    """Aponta o Playwright para o Chromium empacotado, quando existir."""
    import os

    try:
        from runtime_paths import get_playwright_browsers_path
    except ImportError:
        return

    browsers_path = get_playwright_browsers_path()
    if browsers_path:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)


def buscar_em_todos_sites(termo, max_paginas=2, data_inicio=None, data_fim=None):
    vagas = []
    avisos = []
    kwargs = {"data_inicio": data_inicio, "data_fim": data_fim}

    for nome, func in SCRAPERS.items():
        if nome in SITES_PLAYWRIGHT:
            continue
        try:
            vagas.extend(func(termo, max_paginas, **kwargs))
        except Exception:
            continue

    _configurar_playwright()
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for nome in SITES_PLAYWRIGHT:
                func = SCRAPERS.get(nome)
                if func:
                    try:
                        vagas.extend(func(termo, max_paginas, page=page, **kwargs))
                    except Exception:
                        continue
            browser.close()
    except ImportError:
        avisos.append(
            "Playwright não instalado. Sites com JavaScript foram ignorados: "
            + ", ".join(sorted(SITES_PLAYWRIGHT))
        )
    except Exception as exc:
        avisos.append(
            "Navegador Chromium indisponível para sites com JavaScript ("
            + ", ".join(sorted(SITES_PLAYWRIGHT))
            + f"). Detalhe: {exc}"
        )

    return vagas, avisos
