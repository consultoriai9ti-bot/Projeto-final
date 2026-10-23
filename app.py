import streamlit as str_app

# 1. Configuração da página
str_app.set_page_config(
    page_title="Central de Ajuda - Ellenco",
    page_icon="🖥️",
    layout="wide",
)

# 2. Injeção de CSS para forçar o fundo branco e padronizar o visual
str_app.markdown(
    """
    <style>
        .stApp {
            background-color: #FFFFFF !important;
        }
        div[data-testid="stForm"], div[data-testid="stExpander"] {
            background-color: #F8F9FA !important;
            border-radius: 8px;
            border: 1px solid #E9ECEF;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Cabeçalho com Logo e Título com computador
col_logo, col_titulo = str_app.columns([1, 4], vertical_alignment="center")

with col_logo:
    try:
        # Busca o arquivo logo.JPG na mesma pasta do script
        str_app.image("logo.JPG", width=180)
    except Exception:
        try:
            str_app.image("logo.jpg", width=180)
        except Exception:
            str_app.markdown("### **🖥️ [ ELLENCO ]**")

with col_titulo:
    str_app.title("🖥️ Central de Ajuda - Suporte T.I.")
    str_app.caption("Autoatendimento e Abertura de Chamados Técnicos")

str_app.divider()

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
if "abrir_chamado" not in str_app.session_state:
    str_app.session_state.abrir_chamado = False

# Layout principal em 2 colunas
col_main, col_info = str_app.columns([2, 1], gap="large")

with col_main:
    str_app.subheader("1. Descreva a sua dúvida ou problema")

    problema_usuario = str_app.text_area(
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
            str_app.warning(
                "💡 Encontramos alguns procedimentos automáticos que podem te"
                " ajudar:"
            )

            for _, item in sugestoes[:2]:
                with str_app.expander(f"📄 **{item['titulo']}**", expanded=True):
                    str_app.write(item["solucao"])
                    str_app.markdown("---")

                    resolvido = str_app.radio(
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
                        str_app.success(
                            "🎉 Que ótimo! Chamado encerrado por autoatendimento."
                        )
                        str_app.session_state.abrir_chamado = False
                        str_app.stop()
                    elif resolvido == "Não, preciso abrir chamado":
                        str_app.session_state.abrir_chamado = True

        # Formulário com ramificação de áreas
        if not sugestoes or str_app.session_state.abrir_chamado:
            if not sugestoes:
                str_app.info(
                    "ℹ️ Nenhuma solução automática foi encontrada. Vamos abrir"
                    " um chamado para a equipe."
                )

            str_app.markdown("---")
            str_app.subheader("📝 Formulário de Abertura de Chamado")

            with str_app.form(key="form_chamado", border=True):
                col_c1, col_c2 = str_app.columns(2)

                with col_c1:
                    nome_solicitante = str_app.text_input("Seu Nome")

                with col_c2:
                    # 1º Nível: Escolha da Área Principal
                    area_principal = str_app.selectbox(
                        "Área de Destino",
                        ["Selecione a área...", "Sistemas", "Infraestrutura"],
                    )

                # 2º Nível: Ramificação dinâmica solicitada
                subcategoria = "Nenhuma"
                if area_principal == "Sistemas":
                    subcategoria = str_app.selectbox(
                        "Sistema Específico", ["Sistema RM", "Sistema SISMA"]
                    )
                elif area_principal == "Infraestrutura":
                    subcategoria = str_app.selectbox(
                        "Serviço Específico", ["Redes", "Computador"]
                    )

                detalhes = str_app.text_area(
                    "Detalhes adicionais para a equipe", value=problema_usuario
                )

                submit = str_app.form_submit_button(
                    "🚀 Enviar Chamado para T.I.", use_container_width=True
                )

                if submit:
                    if not nome_solicitante:
                        str_app.error(
                            "Por favor, preencha o seu nome antes de enviar."
                        )
                    elif area_principal == "Selecione a área...":
                        str_app.error("Por favor, selecione uma área de destino.")
                    else:
                        str_app.success(
                            f"✅ Chamado aberto com sucesso na área de **{area_principal} -> {subcategoria}**! Nossa equipe entrará em contato."
                        )
                        str_app.session_state.abrir_chamado = False

# Coluna lateral com informações
with col_info:
    str_app.subheader("ℹ️ Atendimento T.I.")

    with str_app.container(border=True):
        str_app.markdown("**⏰ Horário de Funcionamento**")
        str_app.write("Segunda a Sexta: 08:00 às 18:00")

        str_app.markdown("**📞 Contatos Rápidos**")
        str_app.write("Suporte Interno: **#1020**")

        str_app.markdown("**🗂️ Áreas e Ramificações**")
        str_app.markdown(
            "• **Sistemas:**\n"
            "  - Sistema RM\n"
            "  - Sistema SISMA\n"
            "• **Infraestrutura:**\n"
            "  - Redes\n"
            "  - Computador"
        )
