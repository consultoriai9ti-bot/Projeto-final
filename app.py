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
