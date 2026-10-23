
import streamlit as st
import base64
from pathlib import Path

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================

st.set_page_config(
    page_title="Central de Atendimento - T.I. | Ellenco",
    page_icon="🖥️",
    layout="wide"
)

# ==========================================
# CARREGAR LOGO ELLENCO
# ==========================================

def carregar_logo():
    caminho = Path(__file__).parent / "logo_ellenco.png"

    if caminho.exists():
        with open(caminho, "rb") as arquivo:
            logo_base64 = base64.b64encode(
                arquivo.read()
            ).decode("utf-8")

        return (
            f'<img src="data:image/png;base64,{logo_base64}" '
            'class="logo-ellenco" alt="Ellenco">'
        )

    return ""


logo_html = carregar_logo()

# ==========================================
# ESTILO VISUAL
# ==========================================

st.markdown("""
<style>

/* Cabeçalho preto */
.cabecalho-ellenco {
    background: #111111;
    border-radius: 12px;
    padding: 18px 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 24px;
    width: 100%;
    box-sizing: border-box;
    margin-bottom: 25px;
}

/* Logo */
.logo-ellenco {
    width: 115px;
    max-height: 65px;
    object-fit: contain;
}

/* Título */
.titulo-ellenco {
    color: #ffffff !important;
    font-size: 26px !important;
    font-weight: 700;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.3;
}

/* Rodapé */
.rodape-ellenco {
    text-align: center;
    padding: 12px 0;
    font-family: Arial, sans-serif;
    font-size: 12px;
    color: #666666;
    line-height: 1.8;
}

.rodape-titulo {
    font-size: 14px;
    font-weight: 600;
    color: #222222;
}

.rodape-email {
    font-weight: 600;
    color: #333333;
}

.rodape-horario {
    font-size: 11px;
    color: #888888;
}

/* Responsividade */
@media (max-width: 600px) {
    .cabecalho-ellenco {
        flex-direction: column;
        gap: 10px;
        padding: 16px;
    }

    .titulo-ellenco {
        font-size: 20px !important;
        text-align: center;
    }

    .logo-ellenco {
        width: 95px;
    }
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# CABEÇALHO COM LOGO
# ==========================================

st.markdown(
    f"""
    <div class="cabecalho-ellenco">
        {logo_html}
        <h1 class="titulo-ellenco">
            Central de Atendimento - T.I.
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================
# CONTEÚDO PRINCIPAL
# ==========================================

st.write("Bem-vindo à Central de Atendimento de T.I.")

# MANTENHA AQUI O CÓDIGO EXISTENTE DO SISTEMA:
# - Abertura de chamados
# - Consulta de chamados
# - Acompanhamento de status
# - Dashboard e indicadores

# ==========================================
# RODAPÉ COMPACTO
# ==========================================

st.divider()

st.markdown(
    """
    <div class="rodape-ellenco">

        <div class="rodape-titulo">
            🖥️ Central de Atendimento - T.I.
        </div>

        <div>
            📞 (11) 4000-1020 &nbsp; | &nbsp;
            📱 (11) 90000-1020 &nbsp; | &nbsp;
            ☎️ Ramal 1020
        </div>

        <div class="rodape-email">
            ✉️ ti@ellenco.com.br
        </div>

        <div class="rodape-horario">
            Segunda a sexta | 08h às 18h
            | © 2026 Ellenco Construções
        </div>

    </div>
    """,
    unsafe_allow_html=True
)
