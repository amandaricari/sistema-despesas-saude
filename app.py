
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import bcrypt

st.set_page_config(page_title="Sistema de Despesas - Saúde", layout="wide")

st.markdown("""
    <style>
        html, body, .stApp {
            background-color: #ffffff !important;
            color: #004C98 !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 2px solid #004C98;
        }
    </style>
""", unsafe_allow_html=True)

st.image("logo-2025.png", width=300)

def registrar_log(usuario, acao):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = pd.DataFrame([[usuario, acao, agora]], columns=["usuario", "acao", "datahora"])
    log_file = "log_acesso.csv"
    if os.path.exists(log_file):
        log.to_csv(log_file, mode='a', header=False, index=False)
    else:
        log.to_csv(log_file, index=False)

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
            user = df_usuarios[df_usuarios['usuario'] == usuario]
            if not user.empty:
                senha_hash = user.iloc[0]['senha']
                if bcrypt.checkpw(senha.encode(), senha_hash.encode()):
                    st.session_state["logado"] = True
                    st.session_state["usuario"] = usuario
                    st.session_state["perfil"] = user.iloc[0]["perfil"]
                    registrar_log(usuario, "login")
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

def formulario_despesas():
    df_unidades = pd.read_csv("ESTABELECIMENTO DE SAUDE.csv", encoding="latin1")
    df_despesas = pd.read_csv("DESPESA.csv", encoding="latin1")

    st.title("📋 Formulário de Despesas - Saúde Municipal")
    unidade = st.selectbox("Unidade de Saúde:", df_unidades.iloc[:, 0].tolist())
    competencia = st.text_input("Competência (MM/AAAA):")
    st.subheader("💰 Despesas")

    perfil = st.session_state["perfil"]
    valores = {}

    permissoes_despesas = {
        "admin": "all",
        "gerencia": "all",
        "coordenadores": [
            "Embasa", "Coelba", "Aluguel", "Internet",
            "Manutenção preventiva equipamentos médicos",
            "Monitoramento eletrônico (segurança)", "Sistema administrativo",
            "Medicamentos", "Material médico/hospitalar"
        ],
        "odonto": [
            "Material odontológico", "Manutenção preventiva equipamentos odontológicos"
        ],
        "al": ["Produtos alimentícios", "Material de Limpeza"],
        "transporte": ["Transporte"],
        "mp": ["Manutenção Predial", "Ar Condicionado"],
        "rh": ["Folha de Pagamento"],
        "mi": ["Manutenção de Informática"]
    }

    if perfil in permissoes_despesas:
        if permissoes_despesas[perfil] == "all":
            despesas = df_despesas.iloc[:, 0].tolist()
        else:
            despesas = [d for d in df_despesas.iloc[:, 0] if d in permissoes_despesas[perfil]]
    else:
        despesas = []

    for despesa in despesas:
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
        registrar_log(st.session_state["usuario"], "salvou dados")

def dashboard():
    st.title("📊 Dashboard de Despesas por Unidade, Competência e Tipo")

    try:
        df = pd.read_excel("dados_despesas.xlsx")
    except:
        st.warning("Nenhum dado encontrado ainda.")
        return

    unidades = df["Unidade"].dropna().unique().tolist()
    competencias = df["Competência"].dropna().unique().tolist()

    unidade_sel = st.selectbox("Selecionar Unidade", ["Todas"] + unidades)
    competencia_sel = st.selectbox("Selecionar Competência", ["Todas"] + competencias)

    df_filtrado = df.copy()
    if unidade_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Unidade"] == unidade_sel]
    if competencia_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Competência"] == competencia_sel]

    colunas_despesa = [col for col in df.columns if col not in ["Unidade", "Competência", "Usuário"]]

    st.subheader("📌 Total por Categoria de Despesa")
    totais = df_filtrado[colunas_despesa].sum().sort_values(ascending=False)
    fig1, ax1 = plt.subplots()
    totais.plot(kind="barh", ax=ax1, color="#004C98")
    ax1.set_xlabel("Valor total (R$)")
    st.pyplot(fig1)

    st.subheader("📆 Evolução por Competência")
    if "Competência" in df_filtrado.columns:
        df_comp = df_filtrado.groupby("Competência")[colunas_despesa].sum()
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        df_comp.plot(ax=ax2)
        ax2.set_ylabel("Valor (R$)")
        ax2.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        st.pyplot(fig2)

    st.subheader("📎 Composição Percentual")
    fig3, ax3 = plt.subplots()
    totais.plot(kind="pie", ax=ax3, autopct="%1.1f%%", startangle=90)
    ax3.set_ylabel("")
    ax3.set_title("Distribuição das Despesas")
    st.pyplot(fig3)

# Execução principal
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    check_login()
else:
    perfil = st.session_state.get("perfil", "")
    st.sidebar.markdown(f"👤 Usuário: `{st.session_state['usuario']}`")
    st.sidebar.markdown(f"🔐 Perfil: `{perfil}`")

    if perfil in ["admin", "gerencia"]:
        aba = st.sidebar.radio("Menu", ["Formulário", "Dashboard"])
    else:
        aba = "Formulário"

    if st.sidebar.button("🚪 Sair"):
        registrar_log(st.session_state["usuario"], "logout")
        st.session_state.clear()
        st.experimental_rerun()

    if aba == "Formulário":
        formulario_despesas()
    else:
        dashboard()
