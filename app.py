import streamlit as st

# 1. Configuração da página (deve ser o primeiro comando)
st.set_page_config(
    page_title="Central de Ajuda - Ellenco",
    page_icon="🖥️",
    layout="wide",
)

# 2. Injeção de CSS para o fundo branco, faixas e centralização do título
st.markdown(
    """
    <style>
        /* Fundo principal da página */
        .stApp {
            background-color: #FFFFFF !important;
        }
        
        /* Remove o espaçamento superior padrão do Streamlit para a faixa colar no topo */
        .block-container {
            padding-top: 0rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* Faixa preta de ponta a ponta no topo com texto centralizado */
        .faixa-topo {
            background-color: #000000;
            width: 100vw;
            position: relative;
            left: calc(-50vw + 50%);
            right: calc(-50vw + 50%);
            padding: 20px 40px;
            margin-bottom: 2rem;
            text-align: center; /* Centraliza o conteúdo */
        }

        /* Cores e estilos dos textos dentro da faixa preta */
        .faixa-topo h1 {
            color: #FFFFFF !important;
            font-size: 2rem !important;
            margin: 0 !important;
            font-weight: 600;
        }
        
        .faixa-topo p {
            color: #CCCCCC !important;
            margin: 5px 0 0 0 !important;
            font-size: 1rem;
        }

        /* Estilo dos containers e formulários */
        div[data-testid="stForm"], div[data-testid="stExpander"] {
            background-color: #F8F9FA !important;
            border-radius: 8px;
            border: 1px solid #E9ECEF;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Cabeçalho com faixa preta de ponta a ponta centralizada
st.markdown(
    """
    <div class="faixa-topo">
        <h1>🖥️ Central de Ajuda - Suporte T.I.</h1>
        <p>Autoatendimento e Abertura de Chamados Técnicos</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Logo da Ellenco posicionada logo abaixo da faixa (ou ajuste conforme desejar)
col_logo_dir, _ = st.columns([1, 4])
with col_logo_dir:
    try:
        st.image("logo.JPG", width=160)
    except Exception:
        try:
            st.image("logo.jpg", width=160)
        except Exception:
            pass

st.markdown("<br>", unsafe_allow_html=True)

# Base de conhecimento simulada
base_conhecimento = [
    {
        "id": 1,
        "titulo": "Erro: Período de competência fechado no RM Labore",
        "palavras": ["rm", "labore", "competencia", "fechado", "folha"],
        "solucao": "Solicite ao gestor de RH a reabertura do período correspondente através dos parâmetros globais do sistema.",
    },
    {
        "id": 2,
        "titulo": "Falha de Login ou Equipamento Sem Conexão",
        "palavras": ["rede", "internet", "conexao", "wifi", "lento"],
        "solucao": "Verifique se o cabo de rede está conectado corretamente ou reinicie o seu roteador/switch local.",
    },
    {
        "id": 3,
        "titulo": "SISMA: Bloqueio de acesso a módulo",
        "palavras": ["sisma", "modulo", "acesso", "permissao"],
        "solucao": "Verifique com seu superior se o perfil de acesso necessário foi concedido para o seu usuário no SISMA.",
    },
    {
        "id": 4,
        "titulo": "Computador travando ou não liga",
        "palavras": ["computador", "pc", "trava", "lento", "ligar"],
        "solucao": "Reinicie a máquina pressionando o botão power por 5 segundos. Se persistir, abra um chamado para Infraestrutura.",
    },
]

# Inicializa o session_state
if "abrir_chamado" not in st.session_state:
    st.session_state.abrir_chamado = False

# Layout principal em 2 colunas
col_main, col_info = st.columns([2, 1], gap="large")

with col_main:
    st.subheader("1. Descreva a sua dúvida ou problema")

    problema_usuario = st.text_area(
        label="Descrição do problema",
        placeholder="Ex: Não consigo acessar o SISMA ou problema com meu computador...",
        height=120,
        label_visibility="collapsed",
    )

    if problema_usuario:
        texto_usuario = problema_usuario.lower()
        sugestoes = []

        for item in base_conhecimento:
            matches = sum(
                1 for palavra in item["palavras"] if palavra in texto_usuario
            )
            if matches > 0:
                sugestoes.append((matches, item))

        sugestoes.sort(key=lambda x: x[0], reverse=True)

        # Sugestões automáticas (Deflection)
        if sugestoes:
            st.warning(
                "💡 Encontramos alguns procedimentos automáticos que podem te"
                " ajudar:"
            )

            for _, item in sugestoes[:2]:
                with st.expander(f"📄 **{item['titulo']}**", expanded=True):
                    st.write(item["solucao"])
                    st.markdown("---")

                    resolvido = st.radio(
                        "Isso resolveu o seu problema?",
                        [
                            "Selecione...",
                            "Sim, resolveu!",
                            "Não, preciso abrir chamado",
                        ],
