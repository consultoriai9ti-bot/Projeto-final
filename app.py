import base64
import html
import hmac
import os
import mimetypes
import requests
import re
import sqlite3
import uuid
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Central de Ajuda | Ellenco",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE = Path(__file__).resolve().parent
DB = BASE / "chamados.db"
ANEXOS = BASE / "anexos"
ANEXOS.mkdir(exist_ok=True)
TIPOS = ["png", "jpg", "jpeg", "pdf", "txt", "docx", "xlsx"]
LIMITE_BYTES = 5 * 1024 * 1024
# SLA em horas corridas, contado a partir da abertura. Ajuste conforme a política da T.I.
SLA_HORAS = {"Baixo": 72, "Médio": 48, "Alto": 24, "Crítico": 8}
STATUS_FINAL = {"Resolvido", "Cancelado"}
FORMATO_DATA = "%d/%m/%Y %H:%M"


def interpretar_data(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, FORMATO_DATA)
    except (ValueError, TypeError):
        return None


def prazo_sla(chamado):
    abertura = interpretar_data(chamado["criado_em"])
    if abertura is None:
        return None
    prioridade = chamado["prioridade"].split(" — ")[0].strip()
    return abertura + timedelta(hours=SLA_HORAS.get(prioridade, 48))


def situacao_sla(chamado, agora=None):
    prazo = prazo_sla(chamado)
    if prazo is None:
        return "Sem data", None
    agora = agora or datetime.now()
    encerramento = interpretar_data(chamado["finalizado_em"]) if "finalizado_em" in chamado.keys() else None
    if chamado["status"] in STATUS_FINAL:
        if encerramento is None:
            return "Finalizado (sem histórico de SLA)", prazo
        return ("Cumprido" if encerramento <= prazo else "Finalizado em atraso"), prazo
    return ("Atrasado" if agora > prazo else "No prazo"), prazo


CSS = """<style>
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#f5f7fa!important;color:#243247!important}
[data-testid="stHeader"]{background:#f5f7fa!important}
/* Cabeçalho e navegação em uma única área azul, sem cortes. */
.st-key-cabecalho_ellenco{background:linear-gradient(115deg,#061b35 0%,#092d4d 68%,#073b62 100%)!important;border:1px solid #145578!important;border-radius:18px!important;padding:clamp(16px,2.4vw,30px)!important;box-shadow:0 8px 24px #0a284321!important;overflow:visible!important}
.st-key-cabecalho_ellenco [data-testid="stVerticalBlock"]{gap:clamp(12px,1.5vw,18px)!important}
.st-key-cabecalho_ellenco [data-testid="stElementContainer"]{min-width:0}

.block-container{max-width:1360px!important;width:100%!important;padding:1.2rem clamp(12px,3vw,38px) 2rem!important}
[data-testid="stMainBlockContainer"]{overflow-x:clip}
.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label{color:#243247}
[data-testid="stWidgetLabel"] p{color:#344054!important}
/* Logo não usa altura fixa nem recorte. */
.top-brand{display:flex;align-items:center;flex-wrap:wrap;gap:clamp(12px,2vw,24px);width:100%;min-height:74px;padding:0;margin:0;box-sizing:border-box}
.top-brand .logo-frame{display:flex;align-items:center;justify-content:center;background:#fff;border-radius:9px;padding:9px 15px;min-height:62px;max-width:100%;box-sizing:border-box}
.top-brand .hero-logo{display:block;width:clamp(115px,13vw,185px);height:auto;max-height:68px;object-fit:contain;object-position:center}
.top-brand .hero-logo-placeholder{color:#1466a3;font-weight:900;font-size:1.3rem}
.top-brand-title{border-left:1px solid #4c89a7;padding-left:clamp(12px,2vw,24px);color:#fff!important;font-size:clamp(1.1rem,2vw,1.65rem);font-weight:750;line-height:1.3;overflow-wrap:anywhere}
.st-key-cabecalho_ellenco .stButton button{background:#092744!important;border:1px solid #1884bc!important;border-radius:11px!important;color:#fff!important;min-height:50px!important;padding:9px 6px!important;width:100%!important;white-space:normal!important;box-shadow:none!important}
.st-key-cabecalho_ellenco .stButton button p{color:#fff!important;font-weight:700!important;font-size:clamp(.72rem,.98vw,.98rem)!important;line-height:1.25!important}
.st-key-cabecalho_ellenco .stButton button:hover{border-color:#19d3e5!important;background:#0a4365!important}
.st-key-cabecalho_ellenco .stButton button[kind="primary"]{background:linear-gradient(115deg,#027a9f,#075c83)!important;border-color:#1cc9e6!important}
.home-hero{background:linear-gradient(120deg,#071b32 0%,#0a2c4c 60%,#123b59 100%);border:1px solid #225373;border-radius:18px;padding:clamp(24px,4vw,52px);margin-top:12px;box-shadow:0 8px 26px #071b3222;width:100%;box-sizing:border-box;overflow-wrap:anywhere}
.home-hero .eyebrow{font-size:.76rem;font-weight:800;letter-spacing:2px;color:#4de1e5!important}
.home-hero h1{font-size:clamp(1.7rem,3vw,2.8rem);line-height:1.15;margin:12px 0;color:#ffffff!important}
.home-hero p{font-size:clamp(.95rem,1.3vw,1.12rem);color:#d6e6f5!important;max-width:650px}
.home-intro{text-align:center;margin:18px 0 18px}.home-intro h2{font-size:clamp(1.25rem,2vw,1.75rem);color:#243247!important;margin:4px 0}.home-intro p{color:#65768b!important;margin:0}.home-kicker{color:#168ca4!important;font-size:.75rem;letter-spacing:2px;font-weight:750}
.home-card{background:#fff;border:1px solid #b9d9ed;color:#243247;border-radius:13px;padding:clamp(13px,1.5vw,22px);min-height:145px;margin-bottom:12px;box-shadow:0 3px 12px #142c4408}.home-card.teal{border-color:#a4ddd8}.home-card.slate{border-color:#d6dde5}.home-card h3{font-size:clamp(.9rem,1.1vw,1.05rem);color:#243247;margin:0 0 12px}.home-card p{font-size:.86rem;color:#65768b;margin:0}
.small-card,[data-testid="stMetric"]{background:#fff!important;border:1px solid #dbe4ee!important;color:#243247!important;border-radius:12px;padding:14px}.small-card p,[data-testid="stMetric"] *{color:#243247!important}
[data-testid="stForm"],[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-color:#dbe4ee!important;border-radius:12px}
.rodape{border-top:1px solid #d9e3ec;margin-top:24px;padding:14px 8px 4px;text-align:center}.rodape-titulo,.rodape-contatos,.rodape-final{color:#64748b!important}.rodape-titulo{font-size:13px;font-weight:700}.rodape-contatos{font-size:12px;line-height:1.8}.rodape-final{font-size:11px}
@media(max-width:760px){.top-brand{flex-wrap:wrap}.top-brand-title{font-size:1rem}.block-container{padding-left:12px!important;padding-right:12px!important}.st-key-cabecalho_ellenco{padding:14px!important}}
@media(max-width:950px){.top-brand-title{font-size:clamp(1rem,2.4vw,1.3rem)}}

/* Página inicial: composição compacta, centralizada e coerente com o topo */
.home-hero {
    margin-top: 14px!important;
    margin-bottom: 8px!important;
    padding: clamp(26px,3.5vw,44px)!important;
    background: linear-gradient(120deg,#071b32 0%,#0a2c4c 60%,#123b59 100%)!important;
}
.home-hero h1 {font-size:clamp(1.6rem,3vw,2.65rem)!important}
.home-intro {text-align:center!important;margin:16px auto 16px!important}
.home-intro h2 {color:#0b2c4b!important;font-size:clamp(1.2rem,2vw,1.6rem)!important;margin:0 0 4px!important}
.home-intro p {color:#53677e!important;font-size:.92rem!important}
.home-card {
    background:linear-gradient(140deg,#08213b,#103654)!important;
    border:1px solid #28749a!important;
    border-radius:14px!important;
    padding:clamp(16px,1.6vw,24px)!important;
    min-height:132px!important;
    margin-bottom:4px!important;
    box-shadow:0 6px 18px #0a29441a!important;
    text-align:center!important;
}
.home-card.teal {border-color:#1cbac2!important}
.home-card.slate {border-color:#4e8aa8!important}
.home-card h3 {color:#fff!important;font-size:clamp(.93rem,1.2vw,1.08rem)!important;margin:0 0 9px!important}
.home-card p {color:#d4e7f3!important;font-size:clamp(.79rem,1vw,.9rem)!important;line-height:1.5!important}
.rodape {
    background:linear-gradient(120deg,#071b32,#103654)!important;
    border:1px solid #255575!important;
    border-radius:14px!important;
    margin-top:18px!important;
    padding:16px 12px!important;
    text-align:center!important;
}
.rodape-titulo,.rodape-contatos,.rodape-final {color:#e0edf8!important}
.rodape-contatos {font-size:clamp(.73rem,1vw,.86rem)!important}
.rodape-final {opacity:.8!important}
@media(max-width:800px){
  .home-card{min-height:115px!important}
  .home-hero{padding:24px!important}
}

</style>"""
st.markdown(CSS, unsafe_allow_html=True)

AREAS = {
    "Sistemas": {
        "Sistema RM": ["Folha / Ponto", "Compras / Estoque", "Financeiro / Fiscal", "Acesso / Permissões", "Outros"],
        "SISMA": ["Acesso / Permissões", "Erro no sistema", "Outros"],
    },
    "Infraestrutura": {
        "Redes": ["Sem acesso à rede", "Rede lenta", "Compartilhamento de pastas", "Outros"],
        "Internet": ["Sem conexão", "Wi-Fi", "Lentidão", "Outros"],
        "E-mail": ["Não consigo acessar", "Não envia ou recebe", "Configuração", "Outros"],
        "Impressoras": ["Não imprime", "Instalação / Configuração", "Atolamento de papel", "Outros"],
        "Notebook": ["Não liga", "Lentidão / Travamento", "Instalação de programas", "Outros"],
    },
}
BASE_CONHECIMENTO = [
    ("Não consigo acessar o TOTVS RM", ["rm", "login", "senha", "acesso", "entrar"],
     "Confira o usuário e a conexão com a rede corporativa. Se houver bloqueio, abra um chamado para Sistemas."),
    ("Internet ou rede indisponível", ["internet", "rede", "wifi", "wi-fi", "conexao"],
     "Verifique o cabo ou Wi-Fi e teste outro site. Persistindo, abra um chamado para Infraestrutura."),
    ("Computador lento ou travando", ["computador", "lento", "travando", "trava", "notebook"],
     "Salve seus arquivos, feche programas desnecessários e reinicie normalmente o computador."),
    ("Impressora não imprime", ["impressora", "imprimir", "impressao"],
     "Confira se a impressora está ligada, tem papel e está selecionada corretamente."),
    ("Permissão de acesso ao SISMA", ["sisma", "permissao", "modulo"],
     "Confirme com seu gestor o perfil necessário e abra um chamado informando o módulo."),
]


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto.lower())
                   if not unicodedata.combining(c))


def conectar():
    conn = sqlite3.connect(DB, timeout=20)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def inicializar():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                protocolo TEXT PRIMARY KEY,
                criado_em TEXT NOT NULL,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                setor TEXT NOT NULL,
                area TEXT NOT NULL,
                servico TEXT NOT NULL,
                categoria TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                anexo TEXT,
                status TEXT NOT NULL DEFAULT 'Aberto'
            )
        """)
        # Migração segura de bases antigas: não apaga chamados existentes.
        colunas = {col[1] for col in conn.execute("PRAGMA table_info(chamados)")}
        if "finalizado_em" not in colunas:
            conn.execute("ALTER TABLE chamados ADD COLUMN finalizado_em TEXT")
        if "responsavel" not in colunas:
            conn.execute("ALTER TABLE chamados ADD COLUMN responsavel TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS anexos_chamado (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocolo TEXT NOT NULL,
                nome_original TEXT NOT NULL,
                nome_salvo TEXT NOT NULL,
                FOREIGN KEY(protocolo) REFERENCES chamados(protocolo)
            )
        """)


def criar_chamado(dados, arquivos):
    protocolo = f"TI-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
    preparados = []
    for arquivo in arquivos:
        conteudo = arquivo.getvalue()
        if len(conteudo) > LIMITE_BYTES:
            raise ValueError(f"O arquivo {arquivo.name} ultrapassa 5 MB.")
        extensao = Path(arquivo.name).suffix.lower().lstrip(".")
        if extensao not in TIPOS:
            raise ValueError(f"Formato não permitido: {arquivo.name}")
        preparados.append((Path(arquivo.name).name, extensao, conteudo))

    pasta = ANEXOS / protocolo
    salvos = []
    try:
        with conectar() as conn:
            conn.execute("""
                INSERT INTO chamados
                (protocolo,criado_em,nome,email,setor,area,servico,categoria,
                 prioridade,titulo,descricao,anexo,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (protocolo, datetime.now().strftime("%d/%m/%Y %H:%M"), *dados, None, "Aberto"))
            for nome_original, extensao, conteudo in preparados:
                pasta.mkdir(parents=True, exist_ok=True)
                nome_salvo = f"{uuid.uuid4().hex}.{extensao}"
                destino = pasta / nome_salvo
                destino.write_bytes(conteudo)
                salvos.append(destino)
                conn.execute("""
                    INSERT INTO anexos_chamado(protocolo,nome_original,nome_salvo)
                    VALUES (?,?,?)
                """, (protocolo, nome_original, nome_salvo))
            # Commit automático ao sair do contexto sem exceções.
    except Exception:
        for destino in salvos:
            destino.unlink(missing_ok=True)
        raise
    return protocolo


def buscar_chamado(protocolo, email):
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        chamado = conn.execute(
            "SELECT * FROM chamados WHERE protocolo=? AND lower(email)=?",
            (protocolo, email.lower()),
        ).fetchone()
        if chamado is None:
            return None, []
        anexos = conn.execute(
            "SELECT id,nome_original,nome_salvo FROM anexos_chamado WHERE protocolo=? ORDER BY id",
            (protocolo,),
        ).fetchall()
        return chamado, anexos


TOTVS_URL = "https://centraldeatendimento.totvs.com/hc/pt-br/sections/360002878291-TOTVS-Linha-RM"
ARTIGOS_REFERENCIA = [
    ("RH - RM - FOP - Liberação de competência", "https://centraldeatendimento.totvs.com/hc/pt-br/articles/360060636393-RH-RM-FOP-Libera%C3%A7%C3%A3o-de-compet%C3%AAncia"),
    ("RH - RM - Meu RH - Erro ao chamar serviço do RM Labore: Funcionário não tem grupo de acesso ao RM Portal associado", "https://centraldeatendimento.totvs.com/hc/pt-br/articles/10385790728983-RH-RM-Meu-RH-Erro-ao-chamar-servi%C3%A7o-do-RM-Labore-Funcion%C3%A1rio-n%C3%A3o-tem-grupo-de-acesso-ao-RM-Portal-associado"),
    ("Framework - Linha RM - Processos não executam", "https://centraldeatendimento.totvs.com/hc/pt-br/articles/115015986907-Framework-Linha-RM-Frame-Processos-n%C3%A3o-executam"),
]


def termos(texto):
    ignorar = {"para", "com", "uma", "que", "não", "nao", "erro", "sistema", "totvs", "linha", "como", "meu", "dos", "das", "por", "rm"}
    return {p for p in re.findall(r"[a-z0-9]+", normalizar(texto)) if len(p) >= 3 and p not in ignorar}


@st.cache_data(ttl=3600, show_spinner=False)
def pesquisar_totvs(assunto):
    # API pública de pesquisa Zendesk: pode exigir autenticação ou ficar indisponível.
    artigos = list(ARTIGOS_REFERENCIA)
    try:
        resposta = requests.get(
            "https://centraldeatendimento.totvs.com/api/v2/help_center/articles/search.json",
            params={"query": assunto, "locale": "pt-br", "per_page": 30},
            headers={"Accept": "application/json", "User-Agent": "EllencoHelpdesk/1.0"},
            timeout=8,
        )
        resposta.raise_for_status()
        for item in resposta.json().get("results", []):
            titulo = item.get("title", "")
            url = item.get("html_url", "")
            if titulo and url.startswith("https://centraldeatendimento.totvs.com/hc/pt-br/articles/"):
                artigos.append((titulo, url))
    except (requests.RequestException, ValueError):
        pass

    palavras = termos(assunto)
    if len(palavras) < 2:
        return [], False
    pontuados = []
    vistos = set()
    for titulo, url in artigos:
        if url in vistos:
            continue
        vistos.add(url)
        titulo_termos = termos(titulo)
        correspondencia = len(palavras & titulo_termos) / len(palavras)
        if correspondencia >= 0.45 and len(palavras & titulo_termos) >= 2:
            pontuados.append((correspondencia, titulo, url))
    pontuados.sort(reverse=True)
    return pontuados[:3], len(artigos) > len(ARTIGOS_REFERENCIA)


STATUS_OPCOES = ["Aberto", "Em andamento", "Aguardando usuário", "Resolvido", "Cancelado"]


def credenciais_admin():
    # Configure em Streamlit Cloud > App settings > Secrets.
    try:
        usuario = st.secrets.get("ADMIN_USER", "")
        senha = st.secrets.get("ADMIN_PASSWORD", "")
    except (FileNotFoundError, KeyError):
        usuario, senha = "", ""
    return str(usuario or os.getenv("ADMIN_USER", "")), str(senha or os.getenv("ADMIN_PASSWORD", ""))


TECNICOS = ["Vanessa Lopes", "Renato Horta"]


def listar_chamados(status="Todos", busca="", tecnico="Todos"):
    sql = "SELECT * FROM chamados WHERE 1=1"
    parametros = []
    if status != "Todos":
        sql += " AND status = ?"
        parametros.append(status)
    if tecnico == "Não atribuído":
        sql += " AND (responsavel IS NULL OR trim(responsavel) = '')"
    elif tecnico != "Todos":
        sql += " AND responsavel = ?"
        parametros.append(tecnico)
    if busca:
        sql += " AND (upper(protocolo) LIKE ? OR lower(nome) LIKE ? OR lower(titulo) LIKE ?)"
        parametros.extend([f"%{busca.upper()}%", f"%{busca.lower()}%", f"%{busca.lower()}%"])
    sql += " ORDER BY substr(criado_em,7,4) DESC, substr(criado_em,4,2) DESC, substr(criado_em,1,2) DESC, substr(criado_em,12,5) DESC"
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(sql, parametros).fetchall()


def atualizar_status(protocolo, status):
    if status not in STATUS_OPCOES:
        raise ValueError("Status inválido")
    with conectar() as conn:
        registro = conn.execute("SELECT status, finalizado_em FROM chamados WHERE protocolo=?", (protocolo,)).fetchone()
        if registro is None:
            raise ValueError("Chamado não encontrado")
        status_anterior, finalizado_anterior = registro
        if status in STATUS_FINAL:
            finalizado_em = finalizado_anterior if status_anterior in STATUS_FINAL and finalizado_anterior else datetime.now().strftime(FORMATO_DATA)
        else:
            finalizado_em = None
        conn.execute("UPDATE chamados SET status=?, finalizado_em=? WHERE protocolo=?", (status, finalizado_em, protocolo))


def anexos_do_chamado(protocolo):
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT id, nome_original, nome_salvo FROM anexos_chamado WHERE protocolo=? ORDER BY id",
            (protocolo,)
        ).fetchall()


inicializar()

# Cabeçalho e navegação na MESMA faixa horizontal.
logo = next((BASE / nome for nome in ["logo.png", "logo.jpg", "logo.JPG", "logo.jpeg"]
             if (BASE / nome).is_file()), None)
if logo:
    mime = "image/png" if logo.suffix.lower() == ".png" else "image/jpeg"
    codificado = base64.b64encode(logo.read_bytes()).decode("ascii")
    logo_html = f'<img class="hero-logo" src="data:{mime};base64,{codificado}" alt="Logo Ellenco">'
else:
    logo_html = '<div class="hero-logo-placeholder">ELLENCO</div>'

cabecalho = (
    '<div class="top-brand"><div class="logo-frame">' + logo_html +
    '</div><div class="top-brand-title">Central de Atendimento - T.I.</div></div>'
)
# Área única: marca e menu, ambos sobre o mesmo azul-marinho.
PAGINAS = ["🏠 Início", "➕ Abrir chamado", "🔎 Consultar chamado", "📚 Soluções rápidas", "🔐 Administração"]
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = PAGINAS[0]
nomes_botoes = ["menu_inicio", "menu_abrir", "menu_consultar", "menu_solucoes", "menu_admin"]
with st.container(key="cabecalho_ellenco"):
    st.markdown(cabecalho, unsafe_allow_html=True)
    colunas_menu = st.columns(5, gap="small")
    for i, coluna in enumerate(colunas_menu):
        with coluna:
            if st.button(PAGINAS[i], key=nomes_botoes[i], use_container_width=True,
                         type="primary" if st.session_state.pagina_atual == PAGINAS[i] else "secondary"):
                st.session_state.pagina_atual = PAGINAS[i]
                st.rerun()
pagina = st.session_state.pagina_atual

if pagina == "🏠 Início":
    st.markdown(
        '<section class="home-hero">'
        '<div class="eyebrow">ELLENCO · TECNOLOGIA DA INFORMAÇÃO</div>'
        '<h1>Central de Atendimento - T.I.</h1>'
        '<p>Abra, consulte e acompanhe seus chamados em um só lugar. '
        'Atendimento de Sistemas e Infraestrutura com praticidade e organização.</p>'
        '</section>', unsafe_allow_html=True
    )
    a, b, c, d = st.columns(4, gap="small")
    cards = [
        (a, "➕ Abrir chamado", "Solicite um novo atendimento para a equipe de T.I.", "blue"),
        (b, "🔎 Consultar chamado", "Acompanhe o atendimento e acesse a TOTVS.", "teal"),
        (c, "📊 Painel administrativo", "Gerencie os chamados, técnicos e indicadores.", "blue"),
        (d, "📚 Base de conhecimento", "Consulte soluções e orientações sobre sistemas.", "slate"),
    ]
    for coluna, titulo_card, descricao_card, cor in cards:
        with coluna:
            st.markdown(f'<div class="home-card {cor}"><h3>{titulo_card}</h3><p>{descricao_card}</p></div>', unsafe_allow_html=True)


elif pagina == "➕ Abrir chamado":
    st.subheader("Novo chamado de suporte")
    st.write("Preencha os dados. Você receberá um número do chamado ao registrar.")
    with st.expander("🔍 Buscar solução na base oficial TOTVS RM antes de abrir", expanded=False):
        st.caption("Para chamados do TOTVS RM, pesquise usando o assunto e a mensagem de erro, sem informar dados pessoais.")
        consulta_rm = st.text_input("Assunto do problema no RM", key="consulta_totvs", placeholder="Ex.: liberar competência folha de pagamento")
        if st.button("Pesquisar artigos TOTVS", key="pesquisar_rm"):
            if len(termos(consulta_rm)) < 2:
                st.warning("Informe pelo menos duas palavras relevantes sobre o problema.")
            else:
                with st.spinner("Procurando orientações da TOTVS..."):
                    sugestoes, api_ok = pesquisar_totvs(consulta_rm)
                if sugestoes:
                    st.success("Encontramos artigos que podem ajudar. Confira se correspondem ao seu caso:")
                    for score, titulo_artigo, link_artigo in sugestoes:
                        st.markdown(f"📄 [{titulo_artigo}]({link_artigo}) — similaridade aproximada: {score:.0%}")
                    st.info("Se algum artigo resolver seu problema, não é necessário abrir chamado. Caso contrário, continue abaixo.")
                else:
                    st.info("Nenhum artigo com correspondência suficiente foi encontrado. Continue com a abertura do chamado.")
                if not api_ok:
                    st.caption("A pesquisa automática completa da TOTVS não está disponível neste momento; foram consultados artigos de referência. Acesse também a base oficial abaixo.")
                st.markdown(f"[Abrir Base de Conhecimento TOTVS Linha RM]({TOTVS_URL})")

    # Seletores fora do st.form: atualizam imediatamente a cada alteração.
    st.markdown("**1. Selecione o tipo de atendimento**")
    c_area, c_servico, c_categoria = st.columns(3)
    with c_area:
        area = st.selectbox("Área responsável *", list(AREAS), key="area_chamado")
    with c_servico:
        servico = st.selectbox("Sistema ou equipamento *", list(AREAS[area]), key=f"servico_{area}")
    with c_categoria:
        categoria = st.selectbox("Categoria *", AREAS[area][servico], key=f"categoria_{area}_{servico}")

    with st.form("novo_chamado"):
        st.markdown("**2. Seus dados**")
        c1, c2, c3 = st.columns([1.2, 1.4, 1])
        with c1:
            nome = st.text_input("Nome completo *")
        with c2:
            email = st.text_input("E-mail corporativo *")
        with c3:
            setor = st.text_input("Setor / Obra *")

        st.markdown("**3. Descrição do problema**")
        titulo = st.text_input("Assunto do chamado *", placeholder="Ex.: Erro ao acessar o RM")
        descricao = st.text_area(
            "Descreva o problema *", height=135,
            placeholder="O que aconteceu? Quando começou? Qual mensagem apareceu?",
        )
        prioridade = st.selectbox("Impacto informado", [
            "Baixo — dúvida ou orientação",
            "Médio — dificulta o trabalho",
            "Alto — impede minha atividade",
            "Crítico — afeta vários usuários",
        ])
        arquivos = st.file_uploader(
            "📎 Anexar imagens ou documentos (opcional)",
            type=TIPOS,
            accept_multiple_files=True,
            help="PNG, JPG, PDF, TXT, DOCX ou XLSX. Até 5 MB por arquivo.",
        )
        st.caption("Não anexe senhas ou dados sigilosos.")
        enviado = st.form_submit_button("🚀 Enviar chamado", use_container_width=True, type="primary")

    if enviado:
        if not all([nome.strip(), email.strip(), setor.strip(), titulo.strip(), descricao.strip()]):
            st.error("Preencha todos os campos obrigatórios (*).")
        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
            st.error("Informe um e-mail válido.")
        elif len(descricao.strip()) < 15:
            st.error("Descreva o problema com pelo menos 15 caracteres.")
        else:
            try:
                dados = (
                    nome.strip(), email.strip().lower(), setor.strip(), area, servico,
                    categoria, prioridade, titulo.strip(), descricao.strip(),
                )
                protocolo = criar_chamado(dados, arquivos or [])
                st.success(f"Chamado registrado! Número do chamado: **{protocolo}**")
                st.info("Guarde o número do chamado e consulte o andamento na opção 'Consultar chamado'.")
            except (OSError, sqlite3.Error, ValueError) as exc:
                st.error(f"Não foi possível registrar o chamado: {exc}")

elif pagina == "🔎 Consultar chamado":
    st.subheader("🔎 Acompanhamento de chamados")
    st.caption("Consulte seus atendimentos internos ou acesse o suporte oficial TOTVS.")

    aba_ellenco, aba_totvs = st.tabs(["🖥️ Chamados Ellenco", "🔗 Chamados TOTVS"])

    with aba_ellenco:
        st.markdown("#### Consultar atendimento interno")
        st.write("Informe os dados utilizados na abertura para acompanhar o andamento do chamado.")
        with st.container(border=True):
            with st.form("consulta"):
                col_num, col_email = st.columns(2)
                with col_num:
                    protocolo = st.text_input("Número do chamado", placeholder="TI-20261023-ABC123").strip().upper()
                with col_email:
                    email_consulta = st.text_input("E-mail usado na abertura", placeholder="usuario@empresa.com.br").strip().lower()
                buscar = st.form_submit_button("🔍 Consultar chamado", type="primary", use_container_width=True)

        if buscar:
            if not protocolo or not email_consulta:
                st.warning("Informe o número do chamado e o e-mail utilizado na abertura.")
            else:
                registro, anexos = buscar_chamado(protocolo, email_consulta)
                if registro is None:
                    st.warning("Não encontramos um chamado com esse número e e-mail. Confira os dados informados.")
                else:
                    st.markdown("#### Detalhes do atendimento")
                    with st.container(border=True):
                        st.markdown(f"### {html.escape(registro['titulo'])}")
                        st.caption(f"Número do chamado: {registro['protocolo']}")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Situação", registro["status"])
                        c2.metric("Prioridade", registro["prioridade"].split(" — ")[0])
                        c3.metric("Técnico responsável", registro["responsavel"] or "Não atribuído")
                        situacao, prazo = situacao_sla(registro)
                        st.write(f"**SLA:** {situacao}  |  **Prazo previsto:** {prazo.strftime(FORMATO_DATA) if prazo else 'Não disponível'}")
                        st.divider()
                        esquerda, direita = st.columns(2)
                        with esquerda:
                            st.write(f"**Solicitante:** {registro['nome']}")
                            st.write(f"**Setor / Obra:** {registro['setor']}")
                            st.write(f"**Abertura:** {registro['criado_em']}")
                        with direita:
                            st.write(f"**Área:** {registro['area']}")
                            st.write(f"**Serviço:** {registro['servico']}")
                            st.write(f"**Categoria:** {registro['categoria']}")
                        st.markdown("**Descrição do problema**")
                        st.write(registro["descricao"])
                        if registro["finalizado_em"]:
                            st.success(f"Encerrado em {registro['finalizado_em']}")

                    if anexos:
                        with st.expander(f"📎 Arquivos anexados ({len(anexos)})", expanded=False):
                            for anexo in anexos:
                                caminho = ANEXOS / protocolo / anexo["nome_salvo"]
                                if caminho.is_file():
                                    st.download_button(
                                        label=f"📥 {anexo['nome_original']}",
                                        data=caminho.read_bytes(),
                                        file_name=anexo["nome_original"],
                                        mime=mimetypes.guess_type(anexo["nome_original"])[0] or "application/octet-stream",
                                        key=f"anexo_{protocolo}_{anexo['id']}",
                                    )
                                    if caminho.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                                        st.image(str(caminho), width=420)
                                else:
                                    st.warning(f"Arquivo indisponível: {anexo['nome_original']}")

    with aba_totvs:
        st.markdown("#### Portal de atendimento TOTVS")
        with st.container(border=True):
            st.write("Consulte diretamente na TOTVS os chamados relacionados ao sistema RM e demais produtos contratados.")
            st.info("O acesso é feito no ambiente oficial da TOTVS. Utilize seu login e senha da TOTVS na página que será aberta.")
            st.link_button(
                "🔐 Acessar portal TOTVS — entrar com login e senha",
                "https://totvs.fluigidentity.com/ui/login-saml",
                type="primary",
                use_container_width=True,
            )
        st.caption("Os chamados TOTVS não são importados automaticamente para a Central de Ajuda Ellenco.")

elif pagina == "📚 Soluções rápidas":
    st.subheader("Soluções rápidas")
    termo = st.text_input("Pesquise sua dúvida", placeholder="Ex.: não consigo acessar o RM")
    resultados = []
    for titulo, palavras, solucao in BASE_CONHECIMENTO:
        busca = normalizar(termo.strip())
        if not busca or any(p in busca or busca in p for p in palavras) or busca in normalizar(titulo):
            resultados.append((titulo, solucao))
    if not resultados:
        st.info("Não encontramos um procedimento. Use a opção 'Abrir chamado'.")
    for titulo, solucao in resultados:
        with st.expander(titulo):
            st.write(solucao)

elif pagina == "🔐 Administração":
    st.subheader("Painel administrativo de chamados")
    admin_user, admin_password = credenciais_admin()
    if not admin_user or not admin_password:
        st.warning("Acesso administrativo não configurado. Defina ADMIN_USER e ADMIN_PASSWORD nos Secrets do Streamlit Cloud.")
    else:
        if "admin_autenticado" not in st.session_state:
            st.session_state.admin_autenticado = False
        if not st.session_state.admin_autenticado:
            with st.form("login_admin"):
                usuario = st.text_input("Usuário administrador")
                senha = st.text_input("Senha", type="password")
                entrar = st.form_submit_button("Entrar", type="primary")
            if entrar:
                if hmac.compare_digest(usuario, admin_user) and hmac.compare_digest(senha, admin_password):
                    st.session_state.admin_autenticado = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
        else:
            if st.button("Sair da administração"):
                st.session_state.admin_autenticado = False
                st.rerun()
            st.markdown("### 👥 Filtrar painel por técnico")
            filtro_tecnico = st.selectbox("Técnico responsável", ["Todos", *TECNICOS, "Não atribuído"], key="filtro_tecnico_painel")
            todos = listar_chamados(tecnico=filtro_tecnico)
            agora = datetime.now()
            mes_atual = (agora.year, agora.month)
            pendentes = [c for c in todos if c["status"] not in STATUS_FINAL]
            abertos_mes = sum(
                1 for c in todos
                if (d := interpretar_data(c["criado_em"])) is not None
                and (d.year, d.month) == mes_atual
            )
            finalizados_mes = sum(
                1 for c in todos
                if c["status"] in STATUS_FINAL
                and (d := interpretar_data(c["finalizado_em"])) is not None
                and (d.year, d.month) == mes_atual
            )
            no_prazo = sum(situacao_sla(c, agora)[0] == "No prazo" for c in pendentes)
            atrasados = sum(situacao_sla(c, agora)[0] == "Atrasado" for c in pendentes)

            st.markdown("### 📊 Indicadores de atendimento")
            a, b, c, d = st.columns(4)
            a.metric("Chamados pendentes", len(pendentes))
            b.metric("Abertos no mês", abertos_mes)
            c.metric("Finalizados no mês", finalizados_mes)
            d.metric("SLA vencido (pendentes)", atrasados)
            e, f, g = st.columns(3)
            e.metric("Pendentes dentro do SLA", no_prazo)
            f.metric("SLA em dia", f"{(no_prazo / len(pendentes) * 100):.1f}%" if pendentes else "—")
            g.metric("Total histórico", len(todos))
            st.caption("SLA contado em horas corridas desde a abertura: Crítico 8h · Alto 24h · Médio 48h · Baixo 72h. "+
                       "Finalizados no mês usa a data de encerramento registrada a partir desta versão; chamados encerrados anteriormente não possuem essa data.")

            st.markdown("### 📋 Painel de chamados pendentes e SLA")
            linhas = []
            for c in pendentes:
                situacao, prazo = situacao_sla(c, agora)
                linhas.append({
                    "Número": c["protocolo"], "Abertura": c["criado_em"],
                    "Solicitante": c["nome"], "Assunto": c["titulo"],
                    "Prioridade": c["prioridade"], "Status": c["status"],
                    "Responsável": c["responsavel"] or "Não atribuído",
                    "Prazo SLA": prazo.strftime(FORMATO_DATA) if prazo else "—",
                    "SLA": situacao,
                })
            if linhas:
                linhas.sort(key=lambda x: (x["SLA"] != "Atrasado", datetime.strptime(x["Prazo SLA"], FORMATO_DATA) if x["Prazo SLA"] != "—" else datetime.max))
                st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)
            else:
                st.success("Não há chamados pendentes.")

            st.markdown("### 🔎 Consultar e atualizar chamados")
            c1, c2 = st.columns([1, 2])
            with c1:
                filtro_status = st.selectbox("Filtrar por status", ["Aberto", "Todos"] + [s for s in STATUS_OPCOES if s != "Aberto"])
            with c2:
                pesquisa = st.text_input("Pesquisar número, solicitante ou assunto")
            registros = listar_chamados(filtro_status, pesquisa.strip(), filtro_tecnico)
            st.caption(f"{len(registros)} chamado(s) encontrado(s)")
            for chamado in registros:
                with st.expander(f"{chamado['protocolo']} · {chamado['titulo']} · {chamado['status']}"):
                    st.write(f"**Solicitante:** {chamado['nome']} — {chamado['email']}")
                    st.write(f"**Setor/Obra:** {chamado['setor']}")
                    st.write(f"**Data:** {chamado['criado_em']}")
                    st.write(f"**Área:** {chamado['area']} / {chamado['servico']} / {chamado['categoria']}")
                    st.write(f"**Prioridade:** {chamado['prioridade']}")
                    st.write(f"**Descrição:** {chamado['descricao']}")
                    sla_atual, prazo_atual = situacao_sla(chamado)
                    st.write(f"**SLA:** {sla_atual} | **Prazo:** {prazo_atual.strftime(FORMATO_DATA) if prazo_atual else '—'}")
                    responsavel_atual = chamado["responsavel"] or "Não atribuído"
                    opcoes_responsavel = ["Não atribuído", *TECNICOS]
                    if responsavel_atual not in opcoes_responsavel:
                        opcoes_responsavel.append(responsavel_atual)
                    responsavel = st.selectbox("Técnico responsável", opcoes_responsavel, index=opcoes_responsavel.index(responsavel_atual), key=f"resp_{chamado['protocolo']}")
                    novo_status = st.selectbox(
                        "Situação do chamado", STATUS_OPCOES,
                        index=STATUS_OPCOES.index(chamado["status"]) if chamado["status"] in STATUS_OPCOES else 0,
                        key=f"status_{chamado['protocolo']}"
                    )
                    if st.button("Salvar situação", key=f"salvar_{chamado['protocolo']}"):
                        atualizar_status(chamado["protocolo"], novo_status)
                        with conectar() as conn:
                            conn.execute("UPDATE chamados SET responsavel=? WHERE protocolo=?", (None if responsavel == "Não atribuído" else responsavel, chamado["protocolo"]))
                        st.success("Chamado atualizado.")
                        st.rerun()
                    for anexo in anexos_do_chamado(chamado["protocolo"]):
                        arquivo = ANEXOS / chamado["protocolo"] / anexo["nome_salvo"]
                        if arquivo.is_file():
                            st.download_button(
                                f"📎 {anexo['nome_original']}", arquivo.read_bytes(),
                                file_name=anexo["nome_original"],
                                mime=mimetypes.guess_type(anexo["nome_original"])[0] or "application/octet-stream",
                                key=f"admin_anexo_{anexo['id']}"
                            )
                        else:
                            st.caption(f"Anexo indisponível: {anexo['nome_original']}")

# Rodapé compacto e centralizado. HTML em uma única string sem indentação.
rodape = (
    '<div class="rodape">'
    '<div class="rodape-titulo">🖥️ Central de Atendimento - T.I.</div>'
    '<div class="rodape-contatos">'
    '📞 (11) 4000-1020 &nbsp; | &nbsp; '
    '📱 (11) 90000-1020 &nbsp; | &nbsp; '
    '☎️ Ramal 1020 &nbsp; | &nbsp; '
    '✉️ ti@ellenco.com.br'
    '</div>'
    '<div class="rodape-final">'
    'Segunda a sexta · 08h às 18h &nbsp; | &nbsp; © 2026 Ellenco Construções'
    '</div></div>'
)
st.markdown(rodape, unsafe_allow_html=True)
