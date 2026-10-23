import base64
import sqlite3
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from html import escape

import streamlit as st

st.set_page_config(page_title="Central de Ajuda | Ellenco", page_icon="🖥️", layout="wide")
BASE = Path(__file__).resolve().parent
DB = BASE / "chamados.db"


def conectar():
    return sqlite3.connect(DB, timeout=15)


def iniciar_banco():
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
                assunto TEXT NOT NULL,
                descricao TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Aberto'
            )
        """)
        conn.commit()


def registrar_chamado(nome, email, setor, area, servico, assunto, descricao, prioridade):
    protocolo = "TI-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()
    with conectar() as conn:
        conn.execute("""
            INSERT INTO chamados
            (protocolo, criado_em, nome, email, setor, area, servico, assunto, descricao, prioridade, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Aberto')
        """, (protocolo, datetime.now().strftime("%d/%m/%Y %H:%M"),
              nome, email.lower().strip(), setor, area, servico, assunto, descricao, prioridade))
        conn.commit()
    return protocolo


def buscar_chamado(protocolo, email):
    with conectar() as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM chamados WHERE UPPER(protocolo) = ? AND LOWER(email) = ?",
            (protocolo.strip().upper(), email.strip().lower()),
        ).fetchone()


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                   if unicodedata.category(c) != "Mn")


def obter_logo():
    for nome in ("logo.JPG", "logo.jpg", "logo.jpeg", "logo.png", "logo.PNG"):
        caminho = BASE / nome
        if caminho.is_file():
            extensao = "png" if caminho.suffix.lower() == ".png" else "jpeg"
            codificado = base64.b64encode(caminho.read_bytes()).decode("ascii")
            return f'<img src="data:image/{extensao};base64,{codificado}" alt="Logo Ellenco" class="logo">'
    return '<span class="marca-fallback">ELLENCO</span>'


iniciar_banco()

st.markdown("""
<style>
.stApp {background: #f7f9fc; color: #142035;}
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1250px;}
.hero {display:flex; align-items:center; justify-content:center; gap:24px; background:#111827;
       border-radius:13px; padding:20px 28px; margin-bottom:18px; flex-wrap:wrap;}
.hero .logo {max-width:150px; max-height:75px; object-fit:contain; background:white; padding:8px; border-radius:7px;}
.marca-fallback {font-weight:800; color:white; letter-spacing:2px; font-size:19px;}
.hero h1 {font-size:26px !important; color:white !important; margin:0 !important; padding:0 !important; line-height:1.25;}
.hero p {font-size:13px; color:#cbd5e1; margin:5px 0 0;}
.stButton > button[kind="primary"], .stFormSubmitButton button[kind="primary"] {background:#1767ab; border-color:#1767ab;}
.rodape {text-align:center; font-size:12px; line-height:1.7; color:#64748b; margin-top:20px;
         padding:12px 5px; border-top:1px solid #dce3eb;}
.rodape strong {color:#334155; font-size:13px;}
@media(max-width:650px){.hero h1{font-size:21px !important;} .hero {padding:16px; gap:12px;}}
</style>
""", unsafe_allow_html=True)

# HTML em uma única linha evita que o Markdown o interprete como bloco de código.
logo = obter_logo()
st.markdown(f'<div class="hero">{logo}<div><h1>Central de Ajuda – Suporte T.I.</h1><p>Autoatendimento e abertura de chamados técnicos</p></div></div>', unsafe_allow_html=True)

BASE_CONHECIMENTO = [
    {"titulo": "RM Labore: competência fechada", "palavras": ["rm", "labore", "competencia", "folha", "fechada"],
     "solucao": "Confirme a competência selecionada e solicite à equipe responsável a verificação do período. Não altere parâmetros de fechamento sem autorização."},
    {"titulo": "Sem acesso à internet ou rede", "palavras": ["internet", "rede", "wifi", "conexao", "sem acesso"],
     "solucao": "Verifique a conexão de rede, teste outro site e reinicie o computador. Se o problema continuar, abra um chamado de Infraestrutura."},
    {"titulo": "Problemas de acesso ao SISMA", "palavras": ["sisma", "permissao", "usuario", "acesso"],
     "solucao": "Confirme seu usuário e solicite ao gestor a validação das permissões de acesso. Não compartilhe sua senha."},
    {"titulo": "Computador lento ou travando", "palavras": ["computador", "lento", "travando", "pc", "notebook"],
     "solucao": "Salve seus arquivos, feche programas desnecessários e reinicie normalmente o equipamento. Caso persista, registre um chamado."},
]

SERVICOS = {
    "Sistemas": ["TOTVS RM", "SISMA", "MeuRH", "Clockin", "Outros sistemas"],
    "Infraestrutura": ["Computador / Notebook", "Rede / Internet", "Impressora", "E-mail", "Outros serviços"],
}

aba_inicio, aba_abrir, aba_consultar, aba_ajuda = st.tabs(
    ["🏠 Início", "📝 Abrir chamado", "🔎 Consultar chamado", "💡 Soluções rápidas"]
)

with aba_inicio:
    st.subheader("Como podemos ajudar?")
    st.write("Use **Abrir chamado** para enviar sua solicitação à T.I. ou consulte as soluções rápidas antes de registrar um problema.")
    a, b, c = st.columns(3)
    with a:
        with st.container(border=True):
            st.markdown("**📝 Abrir chamado**")
            st.write("Descreva seu problema e receba um protocolo para consulta.")
    with b:
        with st.container(border=True):
            st.markdown("**🔎 Acompanhar solicitação**")
            st.write("Consulte o chamado usando o protocolo e e-mail cadastrado.")
    with c:
        with st.container(border=True):
            st.markdown("**💡 Autoatendimento**")
            st.write("Encontre orientações para problemas comuns.")
    st.info("Para abrir ou consultar um chamado, selecione a aba correspondente acima.")

with aba_abrir:
    st.subheader("Novo chamado")
    st.caption("Preencha os dados abaixo. Não informe senhas ou dados sigilosos na descrição.")
    with st.form("novo_chamado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo *")
            email = st.text_input("E-mail corporativo *")
            setor = st.text_input("Setor / Departamento *", placeholder="Ex.: RH, Obras, Financeiro")
        with col2:
            area = st.selectbox("Área de atendimento *", list(SERVICOS))
            servico = st.selectbox("Sistema ou serviço *", SERVICOS[area])
            prioridade = st.selectbox("Prioridade *", ["Baixa", "Média", "Alta", "Crítica"])
        assunto = st.text_input("Assunto *", placeholder="Resumo do problema")
        descricao = st.text_area("Descreva o problema *", height=140,
                                 placeholder="O que aconteceu? Quando começou? Qual mensagem de erro apareceu?")
        enviar = st.form_submit_button("🚀 Registrar chamado", type="primary", use_container_width=True)
        if enviar:
            if not all([nome.strip(), email.strip(), setor.strip(), assunto.strip(), descricao.strip()]):
                st.error("Preencha todos os campos obrigatórios (*).")
            elif "@" not in email or "." not in email.split("@")[-1]:
                st.error("Informe um e-mail válido.")
            else:
                try:
                    protocolo = registrar_chamado(nome.strip(), email, setor.strip(), area,
                                                 servico, assunto.strip(), descricao.strip(), prioridade)
                    st.success(f"✅ Chamado registrado! Protocolo: **{protocolo}**")
                    st.info("Guarde o protocolo e o e-mail informado para consultar o chamado.")
                except sqlite3.Error:
                    st.error("Não foi possível salvar o chamado. Entre em contato com a T.I.")

with aba_consultar:
    st.subheader("Consultar chamado")
    with st.form("consulta"):
        protocolo_busca = st.text_input("Número do protocolo", placeholder="TI-20261023-ABC123")
        email_busca = st.text_input("E-mail utilizado na abertura")
        consultar = st.form_submit_button("🔎 Consultar", type="primary")
    if consultar:
        if not protocolo_busca.strip() or not email_busca.strip():
            st.warning("Informe o protocolo e o e-mail.")
        else:
            registro = buscar_chamado(protocolo_busca, email_busca)
            if registro is None:
                st.warning("Chamado não encontrado para o protocolo e o e-mail informados.")
            else:
                with st.container(border=True):
                    st.write(f"**Protocolo:** {registro['protocolo']}")
                    st.write(f"**Status:** {registro['status']}")
                    st.write(f"**Abertura:** {registro['criado_em']}")
                    st.write(f"**Área / serviço:** {registro['area']} / {registro['servico']}")
                    st.write(f"**Prioridade:** {registro['prioridade']}")
                    st.write(f"**Assunto:** {registro['assunto']}")
                    st.write(f"**Descrição:** {registro['descricao']}")

with aba_ajuda:
    st.subheader("Base de conhecimento")
    busca = st.text_input("Pesquise seu problema", placeholder="Ex.: internet, RM, SISMA, computador")
    if busca.strip():
        palavras_busca = normalizar(busca).split()
        resultados = [item for item in BASE_CONHECIMENTO if
                      any(p in normalizar(item["titulo"] + " " + " ".join(item["palavras"])) for p in palavras_busca)]
    else:
        resultados = BASE_CONHECIMENTO
    if not resultados:
        st.info("Nenhuma orientação encontrada. Você pode abrir um chamado na aba correspondente.")
    for item in resultados:
        with st.expander(item["titulo"]):
            st.write(item["solucao"])

# Rodapé compacto. Uma única linha de HTML para evitar renderização como código.
st.markdown('<div class="rodape"><strong>🖥️ Atendimento T.I. – Ellenco</strong><div>📞 (11) 4000-1020 &nbsp;·&nbsp; 📱 (11) 90000-1020 &nbsp;·&nbsp; ☎️ Ramal 1020 &nbsp;·&nbsp; ✉️ ti@ellenco.com.br</div><div>Segunda a sexta · 08h às 18h &nbsp;|&nbsp; © 2026 Ellenco Construções</div></div>', unsafe_allow_html=True)
