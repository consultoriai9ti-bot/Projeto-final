import sqlite3
import uuid
import unicodedata
from datetime import datetime
from pathlib import Path

import streamlit as st

BASE = Path(__file__).resolve().parent
DB = BASE / 'chamados.db'
ANEXOS = BASE / 'anexos'
ANEXOS.mkdir(exist_ok=True)

st.set_page_config(page_title='Central de Ajuda | Ellenco', page_icon='🖥️', layout='wide', initial_sidebar_state='collapsed')

CSS = '''<style>
.stApp {background:#f4f7fb;color:#17243b}
.block-container {padding-top:1.2rem;max-width:1240px;padding-bottom:3rem}
header[data-testid="stHeader"] {background:transparent}
.hero {background:linear-gradient(115deg,#0b1220,#172a45);padding:38px 42px;border-radius:18px;color:white;margin-bottom:25px}
.hero h1 {color:white;font-size:2.3rem;margin:0 0 8px}
.hero p {color:#cbd5e1;font-size:1.05rem;margin:0}
.kicker {color:#7dd3fc;font-weight:700;letter-spacing:1.5px;font-size:0.75rem;margin-bottom:10px}
.small-card {background:white;border:1px solid #e3eaf3;padding:22px;border-radius:14px;min-height:125px}
.small-card h3 {font-size:1.12rem;margin:0 0 8px}
.small-card p {color:#64748b;margin:0}
div[data-testid="stForm"],div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px}
.stButton button[kind="primary"],button[data-testid="stFormSubmitButton"] {background:#1265a8;border-radius:9px;border:0}
[data-testid="stMetric"] {background:white;padding:16px;border-radius:12px;border:1px solid #e3eaf3}
</style>'''
st.markdown(CSS, unsafe_allow_html=True)

AREAS = {
    'Sistemas': {'TOTVS RM': ['Folha / Ponto', 'Compras / Estoque', 'Financeiro / Fiscal', 'Acesso / Permissões', 'Outros'],
                 'SISMA': ['Acesso / Permissões', 'Erro no sistema', 'Outros'],
                 'Outros sistemas': ['Acesso / Permissões', 'Erro no sistema', 'Outros']},
    'Infraestrutura': {'Computador / Notebook': ['Não liga', 'Lentidão / Travamento', 'Instalação', 'Outros'],
                       'Rede / Internet': ['Sem conexão', 'Wi-Fi', 'Lentidão', 'Outros'],
                       'Impressora': ['Não imprime', 'Instalação', 'Outros'],
                       'E-mail': ['Acesso', 'Envio / Recebimento', 'Outros']}
}
BASE_CONHECIMENTO = [
    ('Não consigo acessar o TOTVS RM', ['rm','login','senha','acesso','entrar'], 'Confira o usuário e a conexão com a rede corporativa. Se houver bloqueio de acesso, abra um chamado para Sistemas.'),
    ('Internet ou rede indisponível', ['internet','rede','wifi','wi-fi','conexao'], 'Verifique a conexão do cabo ou do Wi-Fi e teste outro site. Se a falha persistir, abra um chamado para Infraestrutura.'),
    ('Computador lento ou travando', ['computador','lento','travando','trava','notebook'], 'Salve seus arquivos, feche programas desnecessários e reinicie normalmente o computador. Persistindo, abra um chamado.'),
    ('Impressora não imprime', ['impressora','imprimir','impressao'], 'Confira se a impressora está ligada, se há papel e se ela está selecionada corretamente. Persistindo, abra um chamado.'),
    ('Permissão de acesso ao SISMA', ['sisma','permissao','modulo'], 'Confirme com seu gestor qual perfil é necessário e abra um chamado de Sistemas informando o módulo e a mensagem de erro.')
]

def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.lower()) if not unicodedata.combining(c))

def conectar():
    conn = sqlite3.connect(DB, timeout=20)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def inicializar():
    with conectar() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS chamados (
            protocolo TEXT PRIMARY KEY, criado_em TEXT NOT NULL, nome TEXT NOT NULL,
            email TEXT NOT NULL, setor TEXT NOT NULL, area TEXT NOT NULL,
            servico TEXT NOT NULL, categoria TEXT NOT NULL, prioridade TEXT NOT NULL,
            titulo TEXT NOT NULL, descricao TEXT NOT NULL, anexo TEXT,
            status TEXT NOT NULL DEFAULT 'Aberto')''')

def criar_chamado(dados, arquivo):
    protocolo = f"TI-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
    caminho = None
    if arquivo is not None:
        extensao = Path(arquivo.name).suffix.lower()
        if extensao not in {'.png','.jpg','.jpeg','.pdf','.txt'}:
            raise ValueError('Tipo de anexo não permitido.')
        conteudo = arquivo.getvalue()
        if len(conteudo) > 5 * 1024 * 1024:
            raise ValueError('O anexo deve ter no máximo 5 MB.')
        caminho = str(ANEXOS / f'{protocolo}{extensao}')
        Path(caminho).write_bytes(conteudo)
    try:
        with conectar() as conn:
            conn.execute('''INSERT INTO chamados
            (protocolo,criado_em,nome,email,setor,area,servico,categoria,prioridade,titulo,descricao,anexo,status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (protocolo,datetime.now().strftime('%d/%m/%Y %H:%M'),*dados,caminho,'Aberto'))
    except Exception:
        if caminho:
            Path(caminho).unlink(missing_ok=True)
        raise
    return protocolo

inicializar()

logo = next((BASE / nome for nome in ['logo.png','logo.jpg','logo.JPG','logo.jpeg'] if (BASE / nome).exists()), None)
if logo:
    st.image(str(logo), width=155)
st.markdown('''<div class="hero"><div class="kicker">ELLENCO · TECNOLOGIA DA INFORMAÇÃO</div>
<h1>Central de Ajuda</h1><p>Encontre respostas, solicite suporte e acompanhe seu atendimento em um só lugar.</p></div>''', unsafe_allow_html=True)

pagina = st.radio('Navegação', ['🏠 Início','➕ Abrir chamado','🔎 Consultar chamado','📚 Soluções rápidas'], horizontal=True, label_visibility='collapsed')
st.divider()

if pagina == '🏠 Início':
    st.subheader('Como podemos ajudar?')
    a,b,c = st.columns(3)
    with a:
        st.markdown('<div class="small-card"><h3>➕ Abrir chamado</h3><p>Registre uma solicitação para Sistemas ou Infraestrutura.</p></div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="small-card"><h3>🔎 Acompanhar</h3><p>Consulte a situação do seu atendimento pelo protocolo.</p></div>',unsafe_allow_html=True)
    with c:
        st.markdown('<div class="small-card"><h3>📚 Autoatendimento</h3><p>Veja procedimentos para resolver dúvidas comuns.</p></div>',unsafe_allow_html=True)
    st.info('Selecione uma das opções no menu acima para começar.')
    st.caption('Atendimento T.I.: segunda a sexta, das 08h às 18h · Ramal interno: #1020')

elif pagina == '➕ Abrir chamado':
    st.subheader('Novo chamado de suporte')
    st.write('Preencha os dados abaixo. Ao enviar, você receberá um número de protocolo.')
    with st.form('novo_chamado', clear_on_submit=False):
        st.markdown('**1. Seus dados**')
        c1,c2,c3 = st.columns([1.2,1.4,1])
        with c1: nome = st.text_input('Nome completo *')
        with c2: email = st.text_input('E-mail corporativo *')
        with c3: setor = st.text_input('Setor / Obra *')
        st.markdown('**2. Sobre o problema**')
        c1,c2,c3 = st.columns(3)
        with c1: area = st.selectbox('Área responsável *', list(AREAS))
        with c2: servico = st.selectbox('Sistema ou equipamento *', list(AREAS[area]))
        with c3: categoria = st.selectbox('Categoria *', AREAS[area][servico])
        titulo = st.text_input('Assunto do chamado *', placeholder='Ex.: Erro ao acessar o RM')
        descricao = st.text_area('Descreva o problema *', height=150, placeholder='O que aconteceu? Quando começou? Qual mensagem apareceu?')
        prioridade = st.selectbox('Impacto informado', ['Baixo — dúvida ou orientação','Médio — dificulta o trabalho','Alto — impede minha atividade','Crítico — afeta vários usuários'])
        arquivo = st.file_uploader('Anexar evidência (opcional, até 5 MB)', type=['png','jpg','jpeg','pdf','txt'])
        enviado = st.form_submit_button('🚀 Enviar chamado', use_container_width=True, type='primary')
    if enviado:
        if not all([nome.strip(),email.strip(),setor.strip(),titulo.strip(),descricao.strip()]):
            st.error('Preencha todos os campos obrigatórios (*).')
        elif '@' not in email or '.' not in email.split('@')[-1]:
            st.error('Informe um e-mail válido.')
        elif len(descricao.strip()) < 15:
            st.error('Descreva o problema com pelo menos 15 caracteres.')
        else:
            try:
                protocolo = criar_chamado((nome.strip(),email.strip().lower(),setor.strip(),area,servico,categoria,prioridade,titulo.strip(),descricao.strip()),arquivo)
                st.success(f'Chamado registrado! Protocolo: **{protocolo}**')
                st.info('Guarde seu protocolo e consulte o andamento na opção “Consultar chamado”.')
            except (OSError,sqlite3.Error,ValueError) as exc:
                st.error(f'Não foi possível registrar o chamado: {exc}')

elif pagina == '🔎 Consultar chamado':
    st.subheader('Acompanhar atendimento')
    with st.form('consulta'):
        protocolo = st.text_input('Número do protocolo',placeholder='TI-20261023-ABC123').strip().upper()
        email = st.text_input('E-mail usado na abertura').strip().lower()
        buscar = st.form_submit_button('Consultar',type='primary')
    if buscar:
        if not protocolo or not email:
            st.warning('Informe o protocolo e o e-mail utilizado na abertura.')
        else:
            with conectar() as conn:
                registro = conn.execute('''SELECT protocolo,criado_em,nome,setor,area,servico,categoria,prioridade,titulo,descricao,status
                    FROM chamados WHERE protocolo=? AND lower(email)=?''',(protocolo,email)).fetchone()
            if not registro:
                st.warning('Chamado não encontrado para este protocolo e e-mail.')
            else:
                keys=['Protocolo','Criado em','Solicitante','Setor','Área','Serviço','Categoria','Impacto','Assunto','Descrição','Status']
                d=dict(zip(keys,registro))
                st.success(f"Protocolo {d['Protocolo']} · {d['Status']}")
                st.markdown(f"**Assunto:** {d['Assunto']}")
                for key in ['Criado em','Solicitante','Setor','Área','Serviço','Categoria','Impacto','Descrição']:
                    st.text(f'{key}: {d[key]}')

else:
    st.subheader('Soluções rápidas')
    termo = st.text_input('Pesquise sua dúvida',placeholder='Ex.: não consigo acessar o RM')
    resultados=[]
    for titulo,palavras,solucao in BASE_CONHECIMENTO:
        busca=normalizar(termo)
        if not busca or any(p in busca or busca in p for p in palavras) or busca in normalizar(titulo):
            resultados.append((titulo,solucao))
    if not resultados:
        st.info('Não encontramos um procedimento para essa dúvida. Use a opção “Abrir chamado”.')
    for titulo,solucao in resultados:
        with st.expander(titulo):
            st.write(solucao)
    st.caption('Se o procedimento não resolver, abra um chamado para a equipe de T.I.')

st.divider()
st.caption('Ellenco · Central de Ajuda T.I. | Protótipo interno em Streamlit')
