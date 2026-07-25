"""Dashboard Gestão de Vagas - Painel de controle de vagas."""



import re
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components



from database import db
from scraper.scraper import executar_busca
from scraper.sites import SITES_DISPONIVEIS
from scraper.vaga_utils import (
    TIPOS_VAGA,
    cor_score,
    cor_tipo_vaga,
    enriquecer_vaga,
    formatar_dias_postado,
    formatar_localizacao,
)



st.set_page_config(

    page_title="Gestão de Vagas",

    page_icon="💼",

    layout="wide",

    initial_sidebar_state="collapsed",

)



db.init_db()



STATUS_OPCOES = list(db.STATUS_VALIDOS)

FUNIL_ORDEM = ["Pendente", "Interessado", "Candidatado", "Entrevista", "Proposta", "Rejeitado"]



EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.IGNORECASE)

PHONE_RE = re.compile(

    r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?\d{2}|\d{2})[\s.-]?\d{4,5}[\s.-]?\d{4}"

)



COR_CONTATO = "#fff3cd"

COR_CONTATO_BORDA = "#ffc107"





def _texto_vaga(vaga):

    partes = [

        vaga.get("titulo") or "",

        vaga.get("empresa") or "",

        vaga.get("descricao") or "",

        vaga.get("obs") or "",

    ]

    return " ".join(partes)





def tem_contato(vaga):

    texto = _texto_vaga(vaga)

    return bool(EMAIL_RE.search(texto) or PHONE_RE.search(texto))





def formatar_duracao(segundos):
    if segundos < 60:
        return f"{segundos:.1f} segundos"
    minutos = int(segundos // 60)
    segs = int(segundos % 60)
    if minutos < 60:
        return f"{minutos} min {segs} seg"
    horas = minutos // 60
    mins = minutos % 60
    return f"{horas} h {mins} min"


def renderizar_cronometro_busca(hora_inicio=None, em_andamento=False, hora_fim=None, duracao_segundos=None):
    """Exibe cronômetro da busca. Durante a busca, o tempo corre no navegador em tempo real."""
    if em_andamento and hora_inicio:
        inicio_iso = hora_inicio.strftime("%Y-%m-%dT%H:%M:%S")
        inicio_hora = hora_inicio.strftime("%H:%M:%S")
        components.html(
            f"""
            <div style="font-family: Inter, sans-serif; display: flex; gap: 12px; width: 100%;">
              <div style="flex:1; background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px;">
                <div style="color:#64748b; font-size:0.8rem; font-weight:500;">Hora Inicial</div>
                <div style="color:#1e293b; font-size:1.6rem; font-weight:600;">{inicio_hora}</div>
              </div>
              <div style="flex:1; background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px;">
                <div style="color:#64748b; font-size:0.8rem; font-weight:500;">Hora Final</div>
                <div id="hora-final" style="color:#1e293b; font-size:1.6rem; font-weight:600;">—</div>
              </div>
              <div style="flex:1; background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px;">
                <div style="color:#64748b; font-size:0.8rem; font-weight:500;">Tempo Gasto</div>
                <div id="tempo-gasto" style="color:#1e40af; font-size:1.6rem; font-weight:600;">0 segundos</div>
              </div>
            </div>
            <script>
              const inicio = new Date("{inicio_iso}");
              function formatarTempo(totalSeg) {{
                if (totalSeg < 60) return totalSeg + " segundos";
                const min = Math.floor(totalSeg / 60);
                const seg = totalSeg % 60;
                if (min < 60) return min + " min " + seg + " seg";
                const h = Math.floor(min / 60);
                const m = min % 60;
                return h + " h " + m + " min";
              }}
              function atualizar() {{
                const agora = new Date();
                const seg = Math.floor((agora - inicio) / 1000);
                document.getElementById("tempo-gasto").textContent = formatarTempo(seg);
              }}
              atualizar();
              setInterval(atualizar, 1000);
            </script>
            """,
            height=110,
        )
    else:
        c1, c2, c3 = st.columns(3)
        if hora_inicio and hora_fim and duracao_segundos is not None:
            c1.metric("Hora Inicial", hora_inicio.strftime("%H:%M:%S"))
            c2.metric("Hora Final", hora_fim.strftime("%H:%M:%S"))
            c3.metric("Tempo Gasto", formatar_duracao(duracao_segundos))
        else:
            c1.metric("Hora Inicial", "—")
            c2.metric("Hora Final", "—")
            c3.metric("Tempo Gasto", "—")


def iso_para_br(data_iso):
    """Converte data ISO (YYYY-MM-DD) para formato brasileiro (DD/MM/YYYY)."""
    if not data_iso:
        return ""
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return ""


def br_para_iso(data_br):
    """Converte data brasileira (DD/MM/YYYY) para ISO (YYYY-MM-DD)."""
    if not data_br or not str(data_br).strip():
        return None
    try:
        return datetime.strptime(str(data_br).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return "INVALID"


MODALIDADES_INCLUSAO = ["Remoto", "Híbrido", "Presencial"]
NIVEIS_INCLUSAO = ["Pleno", "Senior", "Junior"]


def iso_para_date(data_iso):
    """Converte ISO para objeto date (calendário)."""
    if not data_iso:
        return None
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").date()
    except ValueError:
        return None


def resolver_data_salvar(texto_br, data_picker):
    """Prioriza texto digitado; se vazio, usa data do calendário."""
    texto = (texto_br or "").strip()
    if texto:
        return br_para_iso(texto)
    if data_picker:
        return data_picker.strftime("%Y-%m-%d")
    return None


def _init_estado_inclusao():
    if "inclusao_modalidade" not in st.session_state:
        st.session_state.inclusao_modalidade = None
    if "inclusao_nivel" not in st.session_state:
        st.session_state.inclusao_nivel = None
    if "novo_termo_cargo" not in st.session_state:
        st.session_state.novo_termo_cargo = ""
    for mod in MODALIDADES_INCLUSAO:
        key = f"chk_mod_{mod}"
        if key not in st.session_state:
            st.session_state[key] = False
    for niv in NIVEIS_INCLUSAO:
        key = f"chk_niv_{niv}"
        if key not in st.session_state:
            st.session_state[key] = False


def _callback_checkbox_inclusao(grupo, label, opcoes, prefix):
    chk_key = f"chk_{prefix}_{label}"
    state_key = f"inclusao_{grupo}"
    if st.session_state[chk_key]:
        st.session_state[state_key] = label
        for op in opcoes:
            if op != label:
                st.session_state[f"chk_{prefix}_{op}"] = False
    elif st.session_state[state_key] == label:
        st.session_state[state_key] = None


def _render_checkboxes_exclusivos(opcoes, grupo, prefix):
    cols = st.columns(len(opcoes))
    selecionado = st.session_state.get(f"inclusao_{grupo}")
    for col, opcao in zip(cols, opcoes):
        with col:
            st.checkbox(
                opcao,
                key=f"chk_{prefix}_{opcao}",
                disabled=selecionado is not None and selecionado != opcao,
                on_change=_callback_checkbox_inclusao,
                args=(grupo, opcao, opcoes, prefix),
            )


def _sanitizar_valor_data(valor):
    """Remove valores corrompidos gravados por componentes HTML."""
    if not valor:
        return ""
    texto = str(valor).strip()
    if "DeltaGenerator" in texto or "LockedCursor" in texto:
        return ""
    return texto


def _aplicar_pendencias_busca():
    """Aplica alterações no session_state antes de instanciar os widgets."""
    if st.session_state.get("_limpar_inclusao_pendente"):
        st.session_state.novo_termo_cargo = ""
        st.session_state.inclusao_modalidade = None
        st.session_state.inclusao_nivel = None
        for mod in MODALIDADES_INCLUSAO:
            st.session_state[f"chk_mod_{mod}"] = False
        for niv in NIVEIS_INCLUSAO:
            st.session_state[f"chk_niv_{niv}"] = False
        st.session_state._limpar_inclusao_pendente = False


def _init_datas_busca(inicio_atual, fim_atual):
    if "data_inicio_busca" not in st.session_state:
        st.session_state.data_inicio_busca = iso_para_br(inicio_atual)
    else:
        st.session_state.data_inicio_busca = _sanitizar_valor_data(st.session_state.data_inicio_busca)
    if "data_fim_busca" not in st.session_state:
        st.session_state.data_fim_busca = iso_para_br(fim_atual)
    else:
        st.session_state.data_fim_busca = _sanitizar_valor_data(st.session_state.data_fim_busca)


def montar_termo_inclusao(cargo):
    """Monta o termo com aspas: cargo + nível + modalidade."""
    partes = []
    if cargo and str(cargo).strip():
        partes.append(str(cargo).strip())
    if st.session_state.get("inclusao_nivel"):
        partes.append(st.session_state.inclusao_nivel)
    if st.session_state.get("inclusao_modalidade"):
        partes.append(st.session_state.inclusao_modalidade)
    if not partes:
        return ""
    return f'"{" ".join(partes)}"'


def aplicar_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        .app-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
            border-radius: 12px;
            padding: 1.5rem 2rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .app-title {
            font-size: 1.75rem;
            font-weight: 700;
            color: #ffffff;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .app-subtitle {
            font-size: 0.95rem;
            color: #bfdbfe;
            margin-top: 0.25rem;
        }

        .page-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 0.25rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetric"] label {
            color: #64748b !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #1e293b !important;
            font-weight: 600 !important;
        }

        .vaga-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
            transition: box-shadow 0.15s ease;
        }
        .vaga-card:hover {
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        }
        .vaga-card-contato {
            border-left: 4px solid #f59e0b;
            background: linear-gradient(90deg, #fffbeb 0%, #ffffff 12%);
        }
        .vaga-card-normal {
            border-left: 4px solid #3b82f6;
        }
        .vaga-empresa-cargo {
            font-size: 1.05rem;
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 0.35rem;
            line-height: 1.4;
        }
        .vaga-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 0.5rem 0;
        }
        .vaga-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        .vaga-detalhe {
            font-size: 0.82rem;
            color: #64748b;
            margin-top: 0.25rem;
            line-height: 1.5;
        }
        .vaga-detalhe strong { color: #475569; }

        .vaga-contato {
            background-color: #fffbeb;
            border-left: 4px solid #f59e0b;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .vaga-normal {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #94a3b8;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.5rem;
        }

        div[data-testid="stHorizontalBlock"] button[kind="primary"] {
            background-color: #1e40af !important;
            border: none !important;
            font-weight: 500 !important;
        }
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
            background-color: #f8fafc !important;
            color: #475569 !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 500 !important;
        }
        div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
            background-color: #f1f5f9 !important;
            border-color: #94a3b8 !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        h1 { font-weight: 600 !important; color: #1e293b !important; }
        h2, h3 { font-weight: 600 !important; color: #334155 !important; }

        div[data-testid="stExpander"], div[data-testid="stContainer"] {
            border-color: #e2e8f0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )





def _cargo(vaga):
    return vaga.get("cargo") or vaga.get("titulo") or "—"


def _hydrate_vagas(vagas):
    """Preenche campos derivados para vagas antigas ou incompletas."""
    return [enriquecer_vaga(v, v.get("palavra_chave")) for v in vagas]


def _html_badge(texto, cor_texto, cor_fundo):
    return (
        f'<span class="vaga-badge" style="color:{cor_texto};background:{cor_fundo};">'
        f"{texto}</span>"
    )


def renderizar_card_vaga(vaga, prefixo_key, mostrar_acoes=True, mostrar_score=True):
    """Card rico com Empresa, Cargo, Score, localização, tipo e dias publicados."""
    contato = tem_contato(vaga)
    classe = "vaga-card-contato" if contato else "vaga-card-normal"
    empresa = vaga.get("empresa") or "Não informada"
    cargo = _cargo(vaga)
    score = vaga.get("score")
    tipo = vaga.get("tipo_vaga") or "Não informado"
    fonte = vaga.get("fonte") or "—"
    dias_txt = formatar_dias_postado(vaga.get("dias_postado"))
    local_txt = formatar_localizacao(vaga)
    status = vaga.get("status") or "—"
    palavra = vaga.get("palavra_chave") or ""

    badges = ""
    if mostrar_score and score is not None:
        ct, cf = cor_score(score)
        badges += _html_badge(f"Score {score}", ct, cf)
    tt, tf = cor_tipo_vaga(tipo)
    badges += _html_badge(tipo, tt, tf)
    if contato:
        badges += _html_badge("Contato", "#92400e", "#fef3c7")
    if fonte and fonte != "—":
        badges += _html_badge(fonte, "#1e3a5f", "#e0f2fe")

    extras = []
    if palavra:
        extras.append(f"<strong>Inclusão:</strong> {palavra}")
    extras.append(f"<strong>Publicada:</strong> {dias_txt}")
    extras.append(f"<strong>Status:</strong> {status}")
    detalhes = " · ".join(extras)

    st.markdown(
        f'<div class="vaga-card {classe}">'
        f'<div class="vaga-empresa-cargo">{empresa} — {cargo}</div>'
        f'<div class="vaga-meta">{badges}</div>'
        f'<div class="vaga-detalhe"><strong>Local:</strong> {local_txt}</div>'
        f'<div class="vaga-detalhe">{detalhes}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    if mostrar_acoes:
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            if vaga.get("link"):
                st.link_button("Abrir vaga", vaga["link"], use_container_width=True)
        with c2:
            if st.button("Editar", key=f"edit_{prefixo_key}_{vaga['id']}", use_container_width=True):
                st.session_state.editar_vaga_id = vaga["id"]
                st.session_state.mostrar_nova_vaga = False
                st.rerun()
        with c3:
            if st.button("Excluir", key=f"del_{prefixo_key}_{vaga['id']}", use_container_width=True):
                db.excluir_vaga(vaga["id"])
                if st.session_state.get("editar_vaga_id") == vaga["id"]:
                    st.session_state.editar_vaga_id = None
                st.rerun()


def renderizar_linha_vaga(vaga, prefixo_key, mostrar_acoes=True):
    """Compatibilidade — delega ao card enriquecido."""
    renderizar_card_vaga(vaga, prefixo_key, mostrar_acoes=mostrar_acoes)





def formulario_vaga(vaga=None, form_key="form_vaga"):
    """Formulário de cadastro/edição de vaga."""
    editando = vaga is not None
    empresa_padrao = (vaga.get("empresa") or "") if editando else ""
    cargo_padrao = _cargo(vaga) if editando else ""
    link_padrao = vaga["link"] if editando else ""
    cidade_padrao = (vaga.get("cidade") or "") if editando else ""
    estado_padrao = (vaga.get("estado") or "") if editando else ""
    pais_padrao = (vaga.get("pais") or "Brasil") if editando else "Brasil"
    tipo_idx = list(TIPOS_VAGA).index(vaga.get("tipo_vaga") or "Não informado") if editando else 3
    fonte_padrao = (vaga.get("fonte") or "") if editando else ""
    desc_padrao = (vaga.get("descricao") or "") if editando else ""
    data_pub_padrao = (vaga.get("data_publicacao") or "") if editando else ""
    obs_padrao = (vaga.get("obs") or "") if editando else ""
    status_idx = STATUS_OPCOES.index(vaga["status"]) if editando else 0

    with st.form(form_key):
        col_a, col_b = st.columns(2)
        with col_a:
            empresa = st.text_input("Empresa", value=empresa_padrao)
            cargo = st.text_input("Cargo *", value=cargo_padrao)
            link = st.text_input("Link da vaga *", value=link_padrao)
            fonte = st.text_input("Site da vaga", value=fonte_padrao, placeholder="Ex: LinkedIn, Indeed")
        with col_b:
            cidade = st.text_input("Cidade", value=cidade_padrao)
            estado = st.text_input("Estado", value=estado_padrao)
            pais = st.text_input("País", value=pais_padrao)
            tipo_vaga = st.selectbox("Tipo da vaga", list(TIPOS_VAGA), index=tipo_idx)
            data_pub = st.text_input("Data de publicação", value=data_pub_padrao, placeholder="AAAA-MM-DD")

        descricao = st.text_area("Descrição", value=desc_padrao)
        col_s, col_o = st.columns(2)
        with col_s:
            status = st.selectbox("Status", STATUS_OPCOES, index=status_idx)
        with col_o:
            obs = st.text_area("Observações", value=obs_padrao, placeholder="Recrutador, WhatsApp, etc.")

        if st.form_submit_button("Salvar" if editando else "Cadastrar Vaga", type="primary"):
            if not cargo or not link:
                st.error("Cargo e Link são obrigatórios.")
            else:
                dados = enriquecer_vaga({
                    "titulo": cargo,
                    "cargo": cargo,
                    "empresa": empresa,
                    "link": link,
                    "cidade": cidade,
                    "estado": estado,
                    "pais": pais,
                    "localizacao": ", ".join(p for p in [cidade, estado, pais] if p),
                    "tipo_vaga": tipo_vaga if tipo_vaga != "Não informado" else "",
                    "fonte": fonte,
                    "descricao": descricao,
                    "data_publicacao": data_pub or None,
                    "status": status,
                    "obs": obs,
                })
                if editando:
                    db.atualizar_vaga(vaga["id"], **{
                        k: dados[k] for k in (
                            "titulo", "cargo", "empresa", "link", "cidade", "estado", "pais",
                            "localizacao", "tipo_vaga", "fonte", "descricao", "data_publicacao",
                            "dias_postado", "score", "status", "obs",
                        )
                    })
                    st.session_state.editar_vaga_id = None
                    st.success("Vaga atualizada!")
                    st.rerun()
                else:
                    inserido = db.inserir_vaga(dados)
                    if inserido:
                        st.session_state.mostrar_nova_vaga = False
                        st.success("Vaga cadastrada!")
                        st.rerun()
                    else:
                        st.warning("Vaga já existe (link duplicado).")





def pagina_dashboard():
    st.markdown('<p class="page-title">Dashboard</p>', unsafe_allow_html=True)

    vagas = _hydrate_vagas(db.listar_vagas())

    df = pd.DataFrame(vagas) if vagas else pd.DataFrame()



    total = len(df)

    pendentes = len(df[df["status"] == "Pendente"]) if not df.empty else 0

    candidatadas = len(df[df["status"] == "Candidatado"]) if not df.empty else 0

    entrevistas = len(df[df["status"] == "Entrevista"]) if not df.empty else 0

    com_contato = sum(1 for v in vagas if tem_contato(v)) if vagas else 0
    remotas = sum(1 for v in vagas if v.get("tipo_vaga") == "Remota") if vagas else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total", total)
    c2.metric("Pendentes", pendentes)
    c3.metric("Candidaturas", candidatadas)
    c4.metric("Entrevistas", entrevistas)
    c5.metric("Remotas", remotas)
    c6.metric("Com Contato", com_contato, help="Vagas com e-mail ou telefone detectado")



    st.divider()



    with st.container(border=True):

        st.markdown("**Filtros**")

        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:

            filtro_tec = st.text_input("Tecnologia", placeholder="Ex: Python, C#, Delphi", key="dash_tec")

        with col_f2:

            filtro_modelo = st.selectbox("Modelo", ["Todos", "Remoto", "Híbrido", "Presencial"], key="dash_modelo")

        with col_f3:

            filtro_nivel = st.selectbox("Nível", ["Todos", "Júnior", "Pleno", "Sênior"], key="dash_nivel")



    if not df.empty and (filtro_tec or filtro_modelo != "Todos" or filtro_nivel != "Todos"):

        mask = pd.Series([True] * len(df))

        if filtro_tec:

            termo = filtro_tec.lower()

            mask &= (

                df["titulo"].str.lower().str.contains(termo, na=False)

                | df["descricao"].str.lower().str.contains(termo, na=False)

                | df["palavra_chave"].str.lower().str.contains(termo, na=False)

            )

        if filtro_modelo != "Todos":
            if "tipo_vaga" in df.columns:
                mask &= df["tipo_vaga"].fillna("").str.lower() == filtro_modelo.lower()
            else:
                mask &= df["descricao"].str.lower().str.contains(filtro_modelo.lower(), na=False) | df[
                    "localizacao"
                ].str.lower().str.contains(filtro_modelo.lower(), na=False)

        if filtro_nivel != "Todos":

            mask &= df["titulo"].str.lower().str.contains(filtro_nivel.lower(), na=False) | df[

                "descricao"

            ].str.lower().str.contains(filtro_nivel.lower(), na=False)

        df_filtrado = df[mask]

    else:

        df_filtrado = df



    col_g1, col_g2, col_g3 = st.columns([2, 1, 1])



    with col_g1:

        st.subheader("Funil de Candidaturas")

        if not df_filtrado.empty:

            contagens = df_filtrado["status"].value_counts().reindex(FUNIL_ORDEM, fill_value=0)

            fig_funil = go.Figure(go.Funnel(

                y=list(contagens.index),

                x=list(contagens.values),

                textinfo="value+percent initial",

            ))

            fig_funil.update_layout(height=420, margin=dict(t=10, b=10, l=10, r=10))

            st.plotly_chart(fig_funil, use_container_width=True)

        else:

            st.info("Nenhuma vaga para exibir no funil.")



    with col_g2:

        st.subheader("Por Status")

        if not df_filtrado.empty:

            fig_pizza = px.pie(

                df_filtrado,

                names="status",

                hole=0.45,

                color_discrete_sequence=px.colors.qualitative.Set2,

            )

            fig_pizza.update_layout(height=420, margin=dict(t=10, b=10), showlegend=True)

            st.plotly_chart(fig_pizza, use_container_width=True)

        else:

            st.info("Sem dados.")



    with col_g3:

        st.subheader("Por Termo")

        por_chave = db.contar_vagas_por_palavra_chave()

        if por_chave:

            df_chave = pd.DataFrame(list(por_chave.items()), columns=["Termo", "Total"])

            fig_bar = px.bar(

                df_chave.head(8),

                x="Total",

                y="Termo",

                orientation="h",

                color="Total",

                color_continuous_scale="Blues",

            )

            fig_bar.update_layout(height=420, showlegend=False, margin=dict(t=10, b=10))

            st.plotly_chart(fig_bar, use_container_width=True)

        else:

            st.info("Sem termos.")



    st.subheader("Evolução Diária de Capturas")

    por_dia = db.vagas_por_dia()

    if por_dia:

        df_dia = pd.DataFrame(por_dia, columns=["Data", "Vagas"])

        fig_linha = px.area(df_dia, x="Data", y="Vagas", markers=True)

        fig_linha.update_layout(height=300, margin=dict(t=10, b=10))

        st.plotly_chart(fig_linha, use_container_width=True)

    else:

        st.info("Sem histórico de capturas.")



    st.divider()

    with st.expander("⚡ Atualizar Status Rápido", expanded=False):

        pendentes_lista = db.listar_vagas(status="Pendente")

        if pendentes_lista:

            col_s, col_u, col_b = st.columns([3, 1, 1])

            with col_s:

                opcoes = {f"{v['id']} - {v['titulo'][:60]}": v["id"] for v in pendentes_lista}

                selecionada = st.selectbox("Selecione a vaga", list(opcoes.keys()), key="dash_status_sel")

            with col_u:

                novo_status = st.selectbox("Novo status", STATUS_OPCOES[1:], key="dash_novo_status")

            with col_b:

                st.write("")

                st.write("")

                if st.button("Atualizar", type="primary", key="dash_atualizar"):

                    db.atualizar_vaga(opcoes[selecionada], status=novo_status)

                    st.success("Status atualizado!")

                    st.rerun()

        else:

            st.info("Não há vagas pendentes para atualizar.")





def pagina_cadastro_vagas():
    st.markdown('<p class="page-title">Cadastro de Vagas</p>', unsafe_allow_html=True)



    if "mostrar_nova_vaga" not in st.session_state:

        st.session_state.mostrar_nova_vaga = False

    if "editar_vaga_id" not in st.session_state:

        st.session_state.editar_vaga_id = None



    col_titulo, col_btn = st.columns([4, 1])

    with col_btn:

        st.write("")

        if st.button("Cadastrar Vaga", type="primary", use_container_width=True):

            st.session_state.mostrar_nova_vaga = not st.session_state.mostrar_nova_vaga

            st.session_state.editar_vaga_id = None

            st.rerun()



    if st.session_state.mostrar_nova_vaga:

        with st.container(border=True):

            st.subheader("Nova Vaga")

            formulario_vaga(form_key="form_nova_vaga")



    if st.session_state.editar_vaga_id:

        vaga_edit = db.get_vaga(st.session_state.editar_vaga_id)

        if vaga_edit:

            with st.container(border=True):

                st.subheader(f"Editar Vaga #{vaga_edit['id']}")

                if st.button("Fechar edição", key="fechar_edicao"):

                    st.session_state.editar_vaga_id = None

                    st.rerun()

                formulario_vaga(vaga_edit, form_key=f"form_edit_{vaga_edit['id']}")



    st.divider()



    busca = st.text_input("Buscar vagas", placeholder="Empresa, cargo, cidade...", key="cad_busca")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_status = st.selectbox("Status", ["Todos"] + STATUS_OPCOES, key="filtro_status_lista")
    with col_f2:
        chaves = ["Todos"] + [p["termo"] for p in db.listar_palavras_chave()]
        filtro_chave = st.selectbox("Inclusão na pesquisa", chaves, key="filtro_chave_lista")
    with col_f3:
        filtro_tipo = st.selectbox("Tipo da vaga", ["Todos"] + list(TIPOS_VAGA), key="filtro_tipo_lista")

    vagas = _hydrate_vagas(db.listar_vagas(
        filtro_texto=busca or None,
        status=filtro_status,
        palavra_chave=filtro_chave,
        tipo_vaga=filtro_tipo,
    ))

    st.caption(
        f"{len(vagas)} vaga(s) · ordenadas por score e data de captura"
    )

    if vagas:

        for v in vagas:

            renderizar_linha_vaga(v, prefixo_key="cad")

    else:

        st.info("Nenhuma vaga encontrada.")





def pagina_busca_vagas():
    _aplicar_pendencias_busca()

    st.markdown('<p class="page-title">Buscar Vagas</p>', unsafe_allow_html=True)
    st.caption("Critérios de inclusão na pesquisa que o robô utilizará para buscar vagas na internet.")
    st.markdown("**Sites consultados:** " + ", ".join(SITES_DISPONIVEIS))

    inicio_atual, fim_atual = db.get_intervalo_busca()
    _init_datas_busca(inicio_atual, fim_atual)

    with st.container(border=True):
        st.subheader("Intervalo de Datas")
        st.caption("Informe as datas no formato DD/MM/AAAA (ex: 15/06/2026).")
        col1, col2, col3, _ = st.columns([1, 1, 1, 3])
        with col1:
            st.text_input(
                "Data inicial",
                placeholder="DD/MM/AAAA",
                key="data_inicio_busca",
                max_chars=10,
            )
        with col2:
            st.text_input(
                "Data final",
                placeholder="DD/MM/AAAA",
                key="data_fim_busca",
                max_chars=10,
            )
        with col3:
            st.write("")
            st.write("")
            if st.button("Salvar Intervalo", type="primary", use_container_width=True):
                ini = br_para_iso(st.session_state.data_inicio_busca)
                fim = br_para_iso(st.session_state.data_fim_busca)
                if ini == "INVALID" or fim == "INVALID":
                    st.error("Use o formato de data DD/MM/AAAA (ex: 14/07/2026).")
                elif ini and fim and ini > fim:
                    st.error("A data inicial não pode ser maior que a data final.")
                else:
                    db.salvar_intervalo_busca(ini, fim)
                    st.success("Intervalo salvo!")
                    st.rerun()
        if not inicio_atual and not fim_atual:
            st.info("Sem intervalo definido — o robô buscará vagas de qualquer data.")



    st.divider()

    st.subheader("Inclusão na Pesquisa")
    st.caption(
        "Informe o cargo ou tecnologia e marque tipo de trabalho e senioridade. "
        "O sistema monta o termo com aspas automaticamente."
    )
    _init_estado_inclusao()

    novo_termo = st.text_input(
        "Cargo / tecnologia",
        placeholder="Ex: Desenvolvedor Delphi",
        key="novo_termo_cargo",
    )

    st.markdown("**Tipo de trabalho**")
    _render_checkboxes_exclusivos(MODALIDADES_INCLUSAO, "modalidade", "mod")

    st.markdown("**Senioridade**")
    _render_checkboxes_exclusivos(NIVEIS_INCLUSAO, "nivel", "niv")

    termo_preview = montar_termo_inclusao(novo_termo)
    if termo_preview:
        st.caption(f"Termo que será salvo: **{termo_preview}**")

    if st.button("Adicionar inclusão", type="primary", key="btn_add_inclusao"):
        termo_final = montar_termo_inclusao(novo_termo)
        if not novo_termo or not str(novo_termo).strip():
            st.error("Informe o cargo ou tecnologia.")
        elif not termo_final:
            st.error("Não foi possível montar o termo de busca.")
        else:
            db.adicionar_palavra_chave(termo_final)
            st.session_state._limpar_inclusao_pendente = True
            st.success(f"{termo_final} adicionado à pesquisa!")
            st.rerun()



    termos = db.listar_palavras_chave()

    if termos:

        for t in termos:

            col1, col2, col3 = st.columns([4, 1, 1])

            col1.write(f"**{t['termo']}** {'(Ativo)' if t['ativo'] else '(Inativo)'}")

            if col2.button("Ativar/Desativar", key=f"toggle_{t['id']}"):

                db.toggle_palavra_chave(t["id"], not t["ativo"])

                st.rerun()

            if col3.button("Remover", key=f"del_{t['id']}"):

                db.remover_palavra_chave(t["id"])

                st.rerun()

    else:

        st.info("Nenhuma inclusão cadastrada. Adicione critérios para o robô buscar vagas.")



    st.divider()

    st.subheader("Executar Busca")

    if "busca_em_andamento" not in st.session_state:
        st.session_state.busca_em_andamento = False
    if "mostrar_confirmacao_zerar" not in st.session_state:
        st.session_state.mostrar_confirmacao_zerar = False

    inicio, fim = db.get_intervalo_busca()
    max_pag = st.slider("Páginas por site/inclusão", 1, 5, 3, key="max_pag_busca")

    st.markdown("**⏱️ Tempo da busca**")
    if st.session_state.busca_em_andamento:
        renderizar_cronometro_busca(
            hora_inicio=st.session_state.hora_inicio_busca,
            em_andamento=True,
        )
    elif st.session_state.get("ultimo_resultado_busca"):
        resultado_timer = st.session_state.ultimo_resultado_busca
        renderizar_cronometro_busca(
            hora_inicio=resultado_timer.get("hora_inicio"),
            hora_fim=resultado_timer.get("hora_fim"),
            duracao_segundos=resultado_timer.get("duracao_segundos"),
        )
    else:
        renderizar_cronometro_busca()

    col_busca, col_zerar = st.columns([2, 1])
    with col_busca:
        iniciar_busca = st.button(
            "Iniciar Busca", type="primary", use_container_width=True, key="btn_iniciar_busca"
        )
    with col_zerar:
        if st.button(
            "Zerar Banco de Dados",
            type="secondary",
            use_container_width=True,
            key="btn_zerar_banco",
        ):
            st.session_state.mostrar_confirmacao_zerar = True
            st.rerun()

    if st.session_state.mostrar_confirmacao_zerar:
        st.warning(
            "⚠️ **Confirma a exclusão de todos os dados?**\n\n"
            "Serão apagados: vagas, histórico de buscas e inclusões cadastradas. "
            "O intervalo de datas será mantido. **Esta ação é irreversível.**"
        )
        col_sim, col_nao = st.columns(2)
        with col_sim:
            if st.button("Sim, excluir", type="primary", key="confirmar_sim_zerar"):
                db.zerar_banco()
                st.session_state.ultimo_resultado_busca = None
                st.session_state.busca_em_andamento = False
                st.session_state.mostrar_confirmacao_zerar = False
                st.success("Banco de dados zerado com sucesso!")
                st.rerun()
        with col_nao:
            if st.button("Cancelar", key="confirmar_nao_zerar"):
                st.session_state.mostrar_confirmacao_zerar = False
                st.rerun()

    if iniciar_busca:
        st.session_state.ultimo_resultado_busca = None
        st.session_state.busca_em_andamento = True
        st.session_state.hora_inicio_busca = datetime.now()
        st.session_state.max_pag_busca_exec = max_pag
        st.rerun()
    elif st.session_state.busca_em_andamento:
        with st.spinner("Buscando vagas na internet..."):
            max_pag_exec = st.session_state.get("max_pag_busca_exec", max_pag)
            try:
                resultado = executar_busca(max_paginas=max_pag_exec, data_inicio=inicio, data_fim=fim)
            except Exception as exc:
                st.session_state.busca_em_andamento = False
                st.session_state.ultimo_resultado_busca = None
                st.error(f"Erro ao executar a busca: {exc}")
                st.rerun()
                return
        st.session_state.busca_em_andamento = False
        st.session_state.ultimo_resultado_busca = resultado
        st.rerun()

    if st.session_state.get("ultimo_resultado_busca") and not st.session_state.busca_em_andamento:
        resultado = st.session_state.ultimo_resultado_busca

        c_res1, c_res2, c_res3, c_res4 = st.columns(4)
        c_res1.metric("Vagas únicas encontradas", resultado.get("total_unicas", 0))
        c_res2.metric("Novas no cadastro", resultado.get("total_novas", 0))
        c_res3.metric("Já existiam", resultado.get("total_ja_existentes", 0))
        c_res4.metric("Total no cadastro", resultado.get("total_cadastro", db.contar_vagas()))

        st.success(
            f"Busca concluída! {resultado.get('total_unicas', 0)} vagas únicas, "
            f"{resultado.get('total_novas', 0)} novas gravadas, "
            f"{resultado.get('total_filtradas', 0)} descartadas pelo filtro, "
            f"{resultado.get('total_brutas', 0)} coletadas antes do filtro."
        )
        for aviso in resultado.get("avisos", []):
            st.warning(aviso)
        for t in resultado["termos"]:
            st.write(
                f"- **Inclusão '{t['termo']}'**: {t.get('brutas', 0)} coletadas → "
                f"{t['encontradas']} relevantes → {t['novas']} novas, "
                f"{t.get('ja_existentes', 0)} já cadastradas, "
                f"{t.get('descartadas', 0)} descartadas"
            )

        vagas_resultado = resultado.get("vagas", [])
        if vagas_resultado:
            st.divider()
            st.subheader(f"Vagas Encontradas ({len(vagas_resultado)} únicas)")
            st.caption(
                "Empresa — Cargo · Score · Local · Tipo · Site · Dias publicados. "
                "Cards em destaque contêm e-mail ou telefone."
            )
            for i, v in enumerate(vagas_resultado):
                renderizar_card_vaga(
                    v,
                    prefixo_key=f"busca_{i}",
                    mostrar_acoes=False,
                )
                if v.get("link"):
                    st.link_button("Abrir vaga", v["link"], key=f"busca_link_{i}")





def pagina_kanban():
    st.markdown('<p class="page-title">Quadro Kanban</p>', unsafe_allow_html=True)

    st.caption("Visualize e mova vagas entre os estágios do processo seletivo.")



    vagas = _hydrate_vagas(db.listar_vagas())

    if not vagas:

        st.info("Nenhuma vaga cadastrada.")

        return



    colunas_visiveis = ["Pendente", "Interessado", "Candidatado", "Entrevista", "Proposta", "Rejeitado"]

    cols = st.columns(len(colunas_visiveis))



    for i, status_col in enumerate(colunas_visiveis):

        with cols[i]:

            st.markdown(f"### {status_col}")

            vagas_col = [v for v in vagas if v["status"] == status_col]

            st.caption(f"{len(vagas_col)} vagas")

            for v in vagas_col:
                contato = tem_contato(v)
                border_color = COR_CONTATO_BORDA if contato else "#3b82f6"
                tipo = v.get("tipo_vaga") or "—"
                score = v.get("score")
                score_txt = f" · {score}pts" if score is not None else ""
                with st.container(border=True):
                    st.markdown(
                        f'<div style="border-left:3px solid {border_color}; padding-left:8px;">'
                        f'<strong>{v.get("empresa") or "—"}</strong><br>'
                        f'<span style="font-size:0.9rem;">{_cargo(v)[:35]}</span>'
                        f'{" · 📞" if contato else ""}{score_txt}<br>'
                        f'<small>{tipo} · {formatar_dias_postado(v.get("dias_postado"))}</small></div>',
                        unsafe_allow_html=True,
                    )

                    if v.get("link"):

                        st.link_button("Abrir", v["link"], key=f"kanban_link_{v['id']}", use_container_width=True)

                    outros = [s for s in STATUS_OPCOES if s != status_col]
                    col_sel, col_btn = st.columns([2, 1])
                    with col_sel:
                        novo = st.selectbox(
                            "Mover",
                            outros,
                            key=f"kanban_{v['id']}",
                            label_visibility="visible",
                        )
                    with col_btn:
                        st.write("")
                        if st.button("Mover", key=f"move_{v['id']}", use_container_width=True):
                            db.atualizar_vaga(v["id"], status=novo)
                            st.rerun()

                    if st.button("Excluir", key=f"del_kanban_{v['id']}", use_container_width=True):

                        db.excluir_vaga(v["id"])

                        st.rerun()





def pagina_historico():
    st.markdown('<p class="page-title">Histórico de Buscas</p>', unsafe_allow_html=True)

    historico = db.listar_historico_buscas(100)

    if historico:

        df = pd.DataFrame(historico)

        colunas = ["data_execucao", "palavra_chave", "vagas_encontradas", "vagas_novas", "mensagem"]

        st.dataframe(df[[c for c in colunas if c in df.columns]], use_container_width=True, hide_index=True)



        df_agg = df.groupby(df["data_execucao"].str[:10]).agg(

            encontradas=("vagas_encontradas", "sum"),

            novas=("vagas_novas", "sum"),

        ).reset_index()

        df_agg.columns = ["Data", "Encontradas", "Novas"]

        fig = px.bar(df_agg, x="Data", y=["Encontradas", "Novas"], barmode="group")

        fig.update_layout(height=350)

        st.plotly_chart(fig, use_container_width=True)

    else:

        st.info("Nenhuma busca executada ainda. Configure inclusões e execute o robô.")





PAGINAS = {

    "Dashboard": pagina_dashboard,

    "Kanban": pagina_kanban,

    "Cadastro de Vagas": pagina_cadastro_vagas,

    "Buscar Vagas": pagina_busca_vagas,

    "Histórico de Buscas": pagina_historico,

}



aplicar_css()

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">Gestão de Vagas</div>
        <div class="app-subtitle">Plataforma de busca e gestão de candidaturas</div>
    </div>
    """,
    unsafe_allow_html=True,
)



if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Dashboard"

nav_cols = st.columns(len(PAGINAS))
for i, nome in enumerate(PAGINAS.keys()):
    with nav_cols[i]:
        ativo = st.session_state.pagina_atual == nome
        if st.button(
            nome,
            key=f"nav_btn_{nome}",
            use_container_width=True,
            type="primary" if ativo else "secondary",
        ):
            st.session_state.pagina_atual = nome
            st.rerun()

st.divider()

PAGINAS[st.session_state.pagina_atual]()


