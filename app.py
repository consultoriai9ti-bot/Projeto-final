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
from datetime import datetime
from pathlib import Path

import streamlit as st

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

CSS = """
<style>
.stApp {background:#f4f7fb;color:#17243b}
.block-container {padding-top:1.2rem;max-width:1240px;padding-bottom:2rem}
header[data-testid="stHeader"] {background:transparent}
.hero {
    background:linear-gradient(115deg,#090909,#202020);
    padding:22px 30px;border-radius:12px;
    display:flex;align-items:center;justify-content:center;
    gap:28px;flex-wrap:wrap;margin-bottom:22px;
}
.hero-logo {width:140px;max-height:85px;object-fit:contain}
.hero-logo-placeholder {font-weight:800;color:#fff;font-size:22px}
.hero-copy {text-align:left}
.hero h1 {color:white!important;font-size:clamp(1.5rem,3vw,2.15rem);margin:0 0 5px}
.hero p {color:#d1d5db;font-size:.95rem;margin:0}
.kicker {color:#93c5fd;font-weight:700;letter-spacing:1px;font-size:.7rem;margin-bottom:6px}
.small-card {background:white;border:1px solid #e3eaf3;padding:20px;border-radius:12px;min-height:118px}
.small-card h3 {font-size:1.1rem;margin:0 0 8px}
.small-card p {color:#64748b;margin:0}
div[data-testid="stForm"],div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:12px}
[data-testid="stMetric"] {background:white;padding:16px;border-radius:12px;border:1px solid #e3eaf3}
.rodape {border-top:1px solid #d8e0e9;margin-top:26px;padding:14px 8px 4px;text-align:center}
.rodape-titulo {font-size:13px;font-weight:700;color:#17243b;margin-bottom:5px}
.rodape-contatos {font-size:12px;color:#475569;line-height:1.8}
.rodape-final {font-size:11px;color:#64748b;margin-top:5px}
@media(max-width:640px) {
    .hero {padding:18px 12px;gap:10px}
    .hero-copy {text-align:center}
    .hero-logo {width:115px}
    .rodape-contatos {font-size:11px}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

AREAS = {
    "Sistemas": {
        "TOTVS RM": ["Folha / Ponto", "Compras / Estoque", "Financeiro / Fiscal", "Acesso / Permissões", "Outros"],
        "SISMA": ["Acesso / Permissões", "Erro no sistema", "Outros"],
        "Outros sistemas": ["Acesso / Permissões", "Erro no sistema", "Outros"],
    },
    "Infraestrutura": {
        "E-mail": ["Não consigo acessar", "Não envia ou recebe", "Configuração", "Outros"],
        "Computador": ["Não liga", "Lentidão / Travamento", "Instalação de programas", "Outros"],
        "Impressora": ["Não imprime", "Instalação / Configuração", "Atolamento de papel", "Outros"],
        "Telefonia": ["Ramal não funciona", "Telefone sem sinal", "Configuração de ramal", "Outros"],
        "Internet": ["Sem conexão", "Wi-Fi", "Lentidão", "Outros"],
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


def listar_chamados(status="Todos", busca=""):
    sql = "SELECT * FROM chamados WHERE 1=1"
    parametros = []
    if status != "Todos":
        sql += " AND status = ?"
        parametros.append(status)
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
        conn.execute("UPDATE chamados SET status=? WHERE protocolo=?", (status, protocolo))


def anexos_do_chamado(protocolo):
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT id, nome_original, nome_salvo FROM anexos_chamado WHERE protocolo=? ORDER BY id",
            (protocolo,)
        ).fetchall()


inicializar()

# Cabeçalho: logo DENTRO da tarja preta.
logo = next((BASE / nome for nome in ["logo.png", "logo.jpg", "logo.JPG", "logo.jpeg"]
             if (BASE / nome).is_file()), None)
if logo:
    mime = "image/png" if logo.suffix.lower() == ".png" else "image/jpeg"
    codificado = base64.b64encode(logo.read_bytes()).decode("ascii")
    logo_html = f'<img class="hero-logo" src="data:{mime};base64,{codificado}" alt="Logo Ellenco">'
else:
    logo_html = '<div class="hero-logo-placeholder">ELLENCO</div>'

cabecalho = (
    '<div class="hero">'
    + logo_html
    + '<div class="hero-copy">'
    + '<div class="kicker">ELLENCO · TECNOLOGIA DA INFORMAÇÃO</div>'
    + '<h1>Central de Ajuda - Suporte T.I.</h1>'
    + '<p>Autoatendimento, abertura e acompanhamento de chamados técnicos</p>'
    + '</div></div>'
)
st.markdown(cabecalho, unsafe_allow_html=True)

pagina = st.radio(
    "Navegação",
    ["🏠 Início", "➕ Abrir chamado", "🔎 Consultar chamado", "📚 Soluções rápidas", "🔐 Administração"],
    horizontal=True,
    label_visibility="collapsed",
)
st.divider()

if pagina == "🏠 Início":
    st.subheader("Como podemos ajudar?")
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="small-card"><h3>➕ Abrir chamado</h3>'
                    '<p>Registre uma solicitação para Sistemas ou Infraestrutura.</p></div>',
                    unsafe_allow_html=True)
    with b:
        st.markdown('<div class="small-card"><h3>🔎 Acompanhar</h3>'
                    '<p>Consulte o atendimento pelo número do chamado e e-mail.</p></div>',
                    unsafe_allow_html=True)
    with c:
        st.markdown('<div class="small-card"><h3>📚 Autoatendimento</h3>'
                    '<p>Veja procedimentos para resolver dúvidas comuns.</p></div>',
                    unsafe_allow_html=True)
    st.info("Selecione uma das opções no menu acima para começar.")

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

    with st.form("novo_chamado"):
        st.markdown("**1. Seus dados**")
        c1, c2, c3 = st.columns([1.2, 1.4, 1])
        with c1:
            nome = st.text_input("Nome completo *")
        with c2:
            email = st.text_input("E-mail corporativo *")
        with c3:
            setor = st.text_input("Setor / Obra *")

        st.markdown("**2. Sobre o problema**")
        c1, c2, c3 = st.columns(3)
        with c1:
            area = st.selectbox("Área responsável *", list(AREAS))
        with c2:
            servico = st.selectbox("Sistema ou equipamento *", list(AREAS[area]))
        with c3:
            categoria = st.selectbox("Categoria *", AREAS[area][servico])
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
    st.subheader("Acompanhar atendimento")
    with st.form("consulta"):
        protocolo = st.text_input(
            "Número do chamado", placeholder="TI-20261023-ABC123"
        ).strip().upper()
        email_consulta = st.text_input("E-mail usado na abertura").strip().lower()
        buscar = st.form_submit_button("Consultar", type="primary")
    if buscar:
        if not protocolo or not email_consulta:
            st.warning("Informe o número do chamado e o e-mail utilizado na abertura.")
        else:
            registro, anexos = buscar_chamado(protocolo, email_consulta)
            if registro is None:
                st.warning("Chamado não encontrado para este número de chamado e e-mail.")
            else:
                st.success(f"Chamado nº {registro['protocolo']} · {registro['status']}")
                st.markdown(f"**Assunto:** {html.escape(registro['titulo'])}")
                campos = {
                    "Criado em": "criado_em",
                    "Solicitante": "nome",
                    "Setor": "setor",
                    "Área": "area",
                    "Serviço": "servico",
                    "Categoria": "categoria",
                    "Impacto": "prioridade",
                    "Descrição": "descricao",
                }
                for rotulo, coluna in campos.items():
                    st.write(f"**{rotulo}:** {registro[coluna]}")
                if anexos:
                    st.markdown("**📎 Arquivos anexados**")
                    for anexo in anexos:
                        caminho = ANEXOS / protocolo / anexo["nome_salvo"]
                        if caminho.is_file():
                            st.download_button(
                                label=f"📥 {anexo['nome_original']}",
                                data=caminho.read_bytes(),
                                file_name=anexo["nome_original"],
                                mime=mimetypes.guess_type(anexo["nome_original"])[0]
                                     or "application/octet-stream",
                                key=f"anexo_{protocolo}_{anexo['id']}",
                            )
                            if caminho.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                                with st.expander(f"Visualizar: {anexo['nome_original']}"):
                                    st.image(str(caminho), use_container_width=True)
                        else:
                            st.warning(f"Arquivo indisponível: {anexo['nome_original']}")

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
            todos = listar_chamados()
            abertos = sum(c["status"] == "Aberto" for c in todos)
            andamento = sum(c["status"] == "Em andamento" for c in todos)
            resolvidos = sum(c["status"] == "Resolvido" for c in todos)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", len(todos))
            c2.metric("Abertos", abertos)
            c3.metric("Em andamento", andamento)
            c4.metric("Resolvidos", resolvidos)
            c1, c2 = st.columns([1, 2])
            with c1:
                filtro_status = st.selectbox("Filtrar por status", ["Aberto", "Todos"] + [s for s in STATUS_OPCOES if s != "Aberto"])
            with c2:
                pesquisa = st.text_input("Pesquisar número, solicitante ou assunto")
            registros = listar_chamados(filtro_status, pesquisa.strip())
            st.caption(f"{len(registros)} chamado(s) encontrado(s)")
            for chamado in registros:
                with st.expander(f"{chamado['protocolo']} · {chamado['titulo']} · {chamado['status']}"):
                    st.write(f"**Solicitante:** {chamado['nome']} — {chamado['email']}")
                    st.write(f"**Setor/Obra:** {chamado['setor']}")
                    st.write(f"**Data:** {chamado['criado_em']}")
                    st.write(f"**Área:** {chamado['area']} / {chamado['servico']} / {chamado['categoria']}")
                    st.write(f"**Prioridade:** {chamado['prioridade']}")
                    st.write(f"**Descrição:** {chamado['descricao']}")
                    novo_status = st.selectbox(
                        "Situação do chamado", STATUS_OPCOES,
                        index=STATUS_OPCOES.index(chamado["status"]) if chamado["status"] in STATUS_OPCOES else 0,
                        key=f"status_{chamado['protocolo']}"
                    )
                    if st.button("Salvar situação", key=f"salvar_{chamado['protocolo']}"):
                        atualizar_status(chamado["protocolo"], novo_status)
                        st.success("Situação atualizada.")
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
