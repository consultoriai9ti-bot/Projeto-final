import streamlit as st

st.title("🛟 Central de Ajuda - Suporte T.I.")

# Base de conhecimento simulada (pode vir de um banco SQL)
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

# 1. Usuário digita o problema
problema_usuario = st.text_area(
    "Descreva o seu problema ou dúvida:",
    placeholder="Ex: Não consigo calcular a folha no RM Labore...",
)

if problema_usuario:
  # 2. Lógica de busca por palavras-chave na base
  texto_usuario = problema_usuario.lower()
  sugestoes = []

  for item in base_conhecimento:
    # Conta quantas palavras-chave batem com o texto do usuário
    matches = sum(1 for palavra in item["palavras"] if palavra in texto_usuario)
    if matches > 0:
      sugestoes.append((matches, item))

  # Ordena pelos mais relevantes
  sugestoes.sort(key=lambda x: x[0], reverse=True)

  # 3. Exibe procedimentos sugeridos (Deflection)
  if sugestoes:
    st.warning(
        "💡 Encontramos alguns procedimentos que podem resolver seu problema"
        " imediatamente:"
    )
    for _, item in sugestoes[:2]:  # Mostra até 2 sugestões
      with st.expander(f"📄 {item['titulo']}"):
        st.write(item["solucao"])
        resolvido = st.radio(
            "Isso resolveu o seu problema?",
            ["Selecione...", "Sim, resolveu!", "Não, preciso abrir chamado"],
            key=f"res_{item['id']}",
        )

        if resolvido == "Sim, resolveu!":
          st.success(
              "Que ótimo! Chamado encerrado automaticamente por"
              " autoatendimento."
          )
          st.stop()
        elif resolvido == "Não, preciso abrir chamado":
          st.info("Prosseguindo com a abertura do chamado...")

  # 4. Botão para abrir o chamado oficial caso nada tenha resolvido
  if st.button("Enviar Chamado para a T.I."):
    st.success(
        "Chamado aberto com sucesso! Nossa equipe entrará em contato em breve."
    )
    # Aqui entra a lógica de salvar no banco de dados (ex: INSERT SQL)
