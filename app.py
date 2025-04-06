
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Sistema de Despesas - Saúde", layout="centered")

# Estilo visual completo e padronizado
st.markdown("""
    <style>
        body, .stApp {
            background-color: #ffffff;
            color: #004C98;
        }

        header, footer, .css-18ni7ap {
            visibility: hidden;
        }

        label, .css-1c7y2kd, .css-1bzt6gz, .css-1v0mbdj,
        .css-qbe2hs, .css-1wvake5, .css-16idsys,
        .stRadio > div > label,
        .stRadio div[role="radiogroup"] > label {
            color: #004C98 !important;
            font-weight: 500 !important;
        }

        input, select, textarea {
            background-color: #ffffff !important;
            color: #004C98 !important;
            border: 1px solid #004C98 !important;
        }

        .stTextInput > div > div > input,
        .stNumberInput input {
            background-color: #ffffff !important;
            color: #004C98 !important;
            border: 1px solid #004C98 !important;
        }

        .stNumberInput button {
            background-color: #004C98 !important;
            color: white !important;
            border: none;
            border-radius: 4px !important;
        }

        .custom-button {
            background-color: #004C98;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            padding: 0.6rem 1.2rem;
            border: none;
            cursor: pointer;
        }

        .custom-button:hover {
            background-color: #003B7A;
        }

        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
            color: #004C98 !important;
            border-right: 2px solid #004C98;
        }

        section[data-testid="stSidebar"] .css-1d391kg,
        section[data-testid="stSidebar"] .css-hxt7ib,
        .css-1v0mbdj {
            color: #004C98 !important;
        }

        button[kind="primary"] {
            background-color: #004C98 !important;
            color: white !important;
            font-weight: bold;
        }

        .stPassword svg {
            color: #004C98 !important;
            fill: #004C98 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Logo
st.image("logo-2025.png", width=300)

# ---- LOGIN ----
def check_login():
    try:
        df_usuarios = pd.read_csv("usuarios.csv")
    except:
        st.error("Arquivo de usuários não encontrado.")
        return

    with st.form("login_form"):
        st.markdown("### 🔐 Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            usuario_encontrado = df_usuarios[(df_usuarios['usuario'] == usuario) & (df_usuarios['senha'] == senha)]
            if not usuario_encontrado.empty:
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["perfil"] = usuario_encontrado.iloc[0]["perfil"]
                st.session_state["despesa"] = usuario_encontrado.iloc[0].get("despesa", "")
            else:
                st.error("Usuário ou senha inválidos.")

# ---- FORMULÁRIO ----
def formulario_despesas():
    df_unidades = pd.read_csv("ESTABELECIMENTO DE SAUDE.csv", encoding="latin1")
    df_despesas = pd.read_csv("DESPESA.csv", encoding="latin1")

    st.title("📋 Formulário de Despesas - Saúde Municipal")
    unidade = st.selectbox("Unidade de Saúde:", df_unidades.iloc[:, 0].tolist())
    competencia = st.text_input("Competência (MM/AAAA):")
    st.subheader("💰 Despesas")

    valores = {}

    if st.session_state["perfil"] == "especifico":
        campo = st.session_state["despesa"]
        valor = st.number_input(f"{campo} (R$)", min_value=0.0, format="%.2f")
        valores[campo] = valor
    else:
        for despesa in df_despesas.iloc[:, 0]:
            valor = st.number_input(f"{despesa} (R$)", min_value=0.0, format="%.2f")
            valores[despesa] = valor

    if st.button("Salvar Dados"):
        dados = {
            "Unidade": unidade,
            "Competência": competencia,
            "Usuário": st.session_state.get("usuario", "N/A")
        }
        dados.update(valores)
        df_novo = pd.DataFrame([dados])

        arquivo_saida = "dados_despesas.xlsx"
        if os.path.exists(arquivo_saida):
            df_existente = pd.read_excel(arquivo_saida)
            df_total = pd.concat([df_existente, df_novo], ignore_index=True)
        else:
            df_total = df_novo

        df_total.to_excel(arquivo_saida, index=False)
        st.success("✅ Dados salvos com sucesso!")

# ---- DASHBOARD ----
def dashboard():
    st.title("📊 Dashboard de Despesas")
    st.info("Área de visualização exclusiva para usuários autorizados.")

# ---- EXECUÇÃO ----
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    check_login()
else:
    perfil = st.session_state.get("perfil", "preenchimento")
    st.sidebar.markdown(f"👤 Usuário: `{st.session_state['usuario']}`")
    st.sidebar.markdown(f"🔐 Perfil: `{perfil}`")

    aba = "Formulário"
    if perfil in ["admin", "dashboard"]:
        aba = st.sidebar.radio("Menu", ["Formulário", "Dashboard"])
    elif perfil == "especifico":
        aba = "Formulário"

    if st.sidebar.button("🚪 Sair"):
        st.session_state.clear()
        st.experimental_rerun()

    if aba == "Formulário":
        formulario_despesas()
    else:
        dashboard()
