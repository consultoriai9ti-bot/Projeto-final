
import streamlit as st
import base64
from pathlib import Path

# ==========================================
# CABEÇALHO COM LOGO ELLENCO
# ==========================================

def carregar_logo():
    caminho = Path(__file__).parent / "logo_ellenco.png"

    if caminho.exists():
        with open(caminho, "rb") as arquivo:
            return base64.b64encode(arquivo.read()).decode()

    return None


logo = carregar_logo()

if logo:
    imagem_logo = (
        f'<img src="data:image/png;base64,{logo}" '
        'class="logo-ellenco">'
    )
else:
    imagem_logo = ""

st.markdown(
    """
    <style>
    .cabecalho-ellenco {
        background-color: #111111;
        border-radius: 10px;
        padding: 18px 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 22px;
        margin-bottom: 22px;
    }

    .logo-ellenco {
        width: 110px;
        max-height: 65px;
        object-fit: contain;
    }

    .titulo-ellenco {
        color: white;
        font-size: 25px;
        font-weight: 700;
        margin: 0;
        line-height: 1.3;
    }

    @media (max-width: 600px) {
        .cabecalho-ellenco {
            flex-direction: column;
            gap: 10px;
            padding: 15px;
        }

        .titulo-ellenco {
            font-size: 20px;
            text-align: center;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="cabecalho-ellenco">
        {imagem_logo}
        <h1 class="titulo-ellenco">
            Central de Atendimento - T.I.
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)
