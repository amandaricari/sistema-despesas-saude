
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Sistema de Despesas - Saúde", layout="centered")

# Estilo com rótulos (labels) do login corrigidos
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
        }
        .stApp {
            background-color: #ffffff;
            color: #004C98;
        }
        input, select, textarea {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #cccccc !important;
        }
        .stTextInput > div > div > input {
            background-color: white !important;
            color: black !important;
        }
        button[kind="primary"] {
            background-color: #004C98 !important;
            color: white !important;
        }
        label, .css-1cpxqw2, .css-1c7y2kd, .css-1bzt6gz, .css-1v0mbdj {
            color: #004C98 !important;
            font-weight: 500 !important;
        }
        .css-1c7y2kd {
            margin-bottom: 6px;
            display: block;
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
                st.session_state["perfil"] = usuario_encontrado.iloc[0]['perfil']
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

    if perfil in ["admin", "dashboard"]:
        aba = st.sidebar.radio("Menu", ["Formulário", "Dashboard"])
        if aba == "Formulário":
            formulario_despesas()
        else:
            dashboard()
    else:
        formulario_despesas()
