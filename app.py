import streamlit as st

# 1. Configuração da página (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Central de Ajuda - Ellenco",
    page_icon="🛟",
    layout="wide",  # Usa a largura total da tela para um visual mais moderno
)

# 2. Cabeçalho com Logo alinhada à esquerda
col_logo, col_titulo = st.columns([1, 4], vertical_alignment="center")

with col_logo:
    # Substitua 'logo_ellenco.png' pelo caminho/nome do arquivo da sua imagem
    # Se quiser usar um link externo temporário, pode colocar a URL aqui
    try:
        st.image("logo_ellenco.png", width=180)
    except Exception:
        # Fallback visual caso a imagem não seja encontrada na pasta local
        st.markdown("### **[ ELLENCO ]**")

with col_titulo:
    st.title("🛟 Central de Ajuda - Suporte T.I.")
    st.caption("Autoatendimento e Abertura de Chamados Técnicos")

st.divider()

# 3. Base de conhecimento simulada
base_conhecimento = [
    {
        "id": 1,
        "titulo": "Erro: Período de competência fechado no RM Labore",
        "palavras": ["rm", "labore", "competencia", "fechado", "folha"],
        "solucao": "Solicite ao gestor de RH a reabertura do período correspondente através dos parâmetros globais do sistema.",
    },
    {
        "id": 2,
        "titulo": "Impressora travada ou sem comunicação",
        "palavras": ["impressora", "imprimir", "papel", "rede"],
        "solucao": "Reinicie o spooler de impressão no Windows ou verifique o cabo de rede da multifuncional.",
    },
]

# Inicializa o session_state para controlar a abertura do formulário
if "abrir_chamado" not in st.session_state:
    st.session_state.abrir_chamado = False

# Layout principal em 2 colunas: Entrada de dados / Procedimentos
col_main, col_info = st.columns([2, 1], gap="large")

with col_main:
    st.subheader("1. Descreva a sua dúvida ou problema")
    
    problema_usuario = st.text_area(
        label="Descrição do problema",
        placeholder="Ex: Não consigo calcular a folha no RM Labore...",
        height=130,
        label_visibility="collapsed"
    )

    if problema_usuario:
        texto_usuario = problema_usuario.lower()
        sugestoes = []

        for item in base_conhecimento:
            matches = sum(1 for palavra in item["palavras"] if palavra in texto_usuario)
            if matches > 0:
                sugestoes.append((matches, item))

        sugestoes.sort(key=lambda x: x[0], reverse=True)

        if sugestoes:
            st.warning("💡 Encontramos alguns procedimentos automáticos que podem te ajudar:")
            
            for _, item in sugestoes[:2]:
                with st.expander(f"📄 **{item['titulo']}**", expanded=True):
                    st.write(item["solucao"])
                    st.markdown("---")
                    
                    resolvido = st.radio(
                        "Isso resolveu o seu problema?",
                        ["Selecione...", "Sim, resolveu!", "Não, preciso abrir chamado"],
                        key=f"res_{item['id']}",
                        horizontal=True
                    )

                    if resolvido == "Sim, resolveu!":
                        st.success("🎉 Que ótimo! Chamado encerrado por autoatendimento.")
                        st.session_state.abrir_chamado = False
                        st.stop()
                    elif resolvido == "Não, preciso abrir chamado":
                        st.session_state.abrir_chamado = True

        # Exibe o formulário de chamado se não houver sugestões ou se o usuário optou por abrir
        if not sugestoes or st.session_state.abrir_chamado:
            if not sugestoes:
                st.info("ℹ️ Nenhuma solução automática foi encontrada. Vamos abrir um chamado para a equipe.")

            st.markdown("---")
            st.subheader("📝 Formulário de Abertura de Chamado")

            with st.form(key="form_chamado", border=True):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    nome_solicitante = st.text_input("Seu Nome")
                with col_c2:
                    categoria = st.selectbox(
                        "Categoria do Problema",
                        ["Sistemas/RM", "Infraestrutura/Redes", "Hardware", "Outros"]
                    )
                
                detalhes = st.text_area("Detalhes adicionais para o técnico", value=problema_usuario)
                
                submit = st.form_submit_button("🚀 Enviar Chamado para T.I.", use_container_width=True)
                
                if submit:
                    if not nome_solicitante:
                        st.error("Por favor, preencha o seu nome antes de enviar.")
                    else:
                        st.success("✅ Chamado aberto com sucesso! Nossa equipe entrará em contato.")
                        st.session_state.abrir_chamado = False

# Coluna lateral com informações adicionais e contatos úteis
with col_info:
    st.subheader("ℹ️ Informações Úteis")
    
    with st.container(border=True):
        st.markdown("**⏰ Horário de Atendimento**")
        st.write("Segunda a Sexta: 08:00 às 18:00")
        
        st.markdown("**📞 Ramais de Emergência**")
        st.write("Suporte Interno: **#1020**")
        
        st.markdown("**📌 Dica**")
        st.caption("Detalhe bem o seu problema no campo de texto para receber soluções mais precisas.")
