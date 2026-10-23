import streamlit as st

# 1. Configuração da página
st.set_page_config(
    page_title="Central de Ajuda - Ellenco",
    page_icon="🛟",
    layout="wide",
)

# 2. Injeção de CSS para forçar o fundo branco em toda a aplicação
st.markdown(
    """
    <style>
        /* Fundo principal da página */
        .stApp {
            background-color: #FFFFFF !important;
        }
        /* Cor de fundo para blocos de contêineres, formulários e expansores */
        div[data-testid="stForm"], div[data-testid="stExpander"] {
            background-color: #F8F9FA !important;
            border-radius: 8px;
            border: 1px solid #E9ECEF;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Cabeçalho com Logo da Ellenco à esquerda
col_logo, col_titulo = st.columns([1, 4], vertical_alignment="center")

with col_logo:
    try:
        st.image("logo_ellenco.png", width=180)
    except Exception:
        st.markdown("### **[ ELLENCO ]**")

with col_titulo:
    st.title("🛟 Central de Ajuda - Suporte T.I.")
    st.caption("Autoatendimento e Abertura de Chamados Técnicos")

st.divider()

# 4. Base de conhecimento simulada
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
        "solucao": "Verifique com seu superior se perfil de acesso necessário foi concedido para o seu usuário no SISMA.",
    },
]

# Inicializa o estado de controle
if "abrir_chamado" not in st.session_state:
    st.session_state.abrir_chamado = False

# Layout principal
col_main, col_info = st.columns([2, 1], gap="large")

with col_main:
    st.subheader("1. Descreva a sua dúvida ou problema")

    problema_usuario = st.text_area(
        label="Descrição do problema",
        placeholder="Ex: Não consigo acessar o módulo no Sistema SISMA ou erro de rede...",
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

        # 5. Deflection (Sugestões automáticas)
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
                        key=f"res_{item['id']}",
                        horizontal=True,
                    )

                    if resolvido == "Sim, resolveu!":
                        st.success(
                            "🎉 Que ótimo! Chamado encerrado por autoatendimento."
                        )
                        st.session_state.abrir_chamado = False
                        st.stop()
                    elif resolvido == "Não, preciso abrir chamado":
                        st.session_state.abrir_chamado = True

        # 6. Formulário de Chamado
        if not sugestoes or st.session_state.abrir_chamado:
            if not sugestoes:
                st.info(
                    "ℹ️ Nenhuma solução automática foi encontrada. Vamos abrir"
                    " um chamado para a equipe."
                )

            st.markdown("---")
            st.subheader("📝 Formulário de Abertura de Chamado")

            with st.form(key="form_chamado", border=True):
                col_c1, col_c2 = st.columns(2)

                with col_c1:
                    nome_solicitante = st.text_input("Seu Nome")

                with col_c2:
                    # Opções atualizadas conforme solicitado
                    categoria = st.selectbox(
                        "Categoria do Chamado",
                        ["Redes", "Sistema RM", "Sistema SISMA", "Automação"],
                    )

                detalhes = st.text_area(
                    "Detalhes adicionais para a equipe de T.I.",
                    value=problema_usuario,
                )

                submit = st.form_submit_button(
                    "🚀 Enviar Chamado para T.I.", use_container_width=True
                )

                if submit:
                    if not nome_solicitante:
                        st.error(
                            "Por favor, preencha o seu nome antes de enviar."
                        )
                    else:
                        # Lógica de salvamento no Banco de Dados / API entra aqui
                        st.success(
                            f"✅ Chamado da categoria '{categoria}' aberto com"
                            " sucesso! Nossa equipe entrará em contato."
                        )
                        st.session_state.abrir_chamado = False

# Coluna lateral
with col_info:
    st.subheader("ℹ️ Atendimento T.I.")

    with st.container(border=True):
        st.markdown("**⏰ Horário de Funcionamento**")
        st.write("Segunda a Sexta: 08:00 às 18:00")

        st.markdown("**📞 Contatos Rápidos**")
        st.write("Suporte Interno: **#1020**")

        st.markdown("**📌 Categorias Suportadas**")
        st.caption(
            "• Redes\n• Sistema RM\n• Sistema SISMA\n• Processos de Automação"
