# app.py - Sistema de Despesas da Saúde

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import bcrypt
import os
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

import json
from google.oauth2.service_account import Credentials
import gspread

def salvar_em_google_sheets(dados_dict):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    client = gspread.authorize(creds)

    # Abre a planilha pelo nome
    sheet = client.open("dados_despesas").sheet1

    headers = list(dados_dict.keys())
    values = list(dados_dict.values())

    # Insere cabeçalhos se estiver vazia
    if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
        sheet.insert_row(headers, 1)

    sheet.append_row(values, value_input_option="USER_ENTERED")

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

col1, col2 = st.columns([1, 2])

with col1:
    st.image("logo-2025.png", width=240)

with col2:
    st.markdown(
        "<h4 style='text-align: right; color: #004C98; padding-top: 20px;'>Secretaria Municipal de Saúde</h4>",
        unsafe_allow_html=True
    )

st.markdown("<hr style='margin-top: 10px; border: none; border-top: 2px solid #004C98;'>", unsafe_allow_html=True)

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
    except FileNotFoundError:
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
                    # 🔒 Padroniza o perfil
                    st.session_state["perfil"] = user.iloc[0]["perfil"].strip().lower()
                    registrar_log(usuario, "login")
                    st.rerun()
                else:
                    st.error("🔐 Senha incorreta.")
            else:
                st.error("🧑 Usuário não encontrado.")

def gerar_pdf(df, unidade, competencia):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Relatório de Despesas por Unidade")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Unidade: {unidade}")
    c.drawString(50, height - 90, f"Competência: {competencia}")
    c.setFont("Helvetica", 10)
    y = height - 120
    for i, (col, val) in enumerate(df.items()):
        c.drawString(50, y, f"{col}: R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        y -= 15
        if y < 60:
            c.showPage()
            y = height - 60
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def formulario_despesas():
    df_unidades = pd.read_csv("ESTABELECIMENTO DE SAUDE.csv", encoding="latin1")
    df_despesas = pd.read_csv("DESPESA.csv", encoding="latin1")

    st.title("📋 Formulário de Despesas - Unidades de Saúde")
    unidade = st.selectbox("Unidade de Saúde:", df_unidades.iloc[:, 0].tolist())

    from datetime import datetime
    meses = [f"{str(mes).zfill(2)}/{datetime.now().year}" for mes in range(1, 13)]
    competencia = st.selectbox("Competência (MM/AAAA):", meses)

    st.subheader("💰 Despesas")

    perfil = st.session_state.get("perfil", "")
    valores = {}

    permissoes_despesas = {
        "administrador": "all",
        "gerencia": "all",
        "coordenadores": [
            "Embasa", "Coelba", "Aluguel", "Internet",
            "Manutencao preventiva equipamentos medicos",
            "Monitoramento eletronico (seguranca)", "Sistema administrativo",
            "Medicamentos", "Material medico/hospitalar"
        ],
        "odonto": [
            "Material odontologico", "Manutencao preventiva equipamentos odontologicos"
        ],
        "manutencao I": ["Produtos alimenticios", "Material de Limpeza"],
        "transporte": ["Transporte"],
        "manutencao II": ["Manutencao Predial", "Ar Condicionado"],
        "rh": ["Folha de Pagamento"],
        "manutencao III": ["Manutencao de Informatica"]
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

    # ⚠️ Botão deve ficar fora do loop acima
    if st.button("Salvar Dados"):
        if not unidade or not competencia:
            st.warning("Por favor, selecione a unidade e a competência.")
            st.stop()

        if not valores or all(v == 0.0 for v in valores.values()):
            st.warning("Preencha pelo menos uma despesa antes de salvar.")
            st.stop()

        dados = {
            "Unidade": unidade,
            "Competência": competencia,
            "Usuário": st.session_state.get("usuario", "N/A")
        }
        dados.update(valores)

        salvar_em_google_sheets(dados)

        registrar_log(st.session_state["usuario"], "salvou dados")
        st.session_state["dados_salvos"] = True
        st.rerun()

    # Mensagem de sucesso pós-rerun
    if st.session_state.get("dados_salvos", False):
        st.success("✅ Dados salvos com sucesso!")
        st.session_state["dados_salvos"] = False

def gerenciar_usuarios():
    st.title("👥 Gerenciador de Usuários")

    df_usuarios = pd.read_csv("usuarios.csv")
    st.dataframe(df_usuarios)

    st.markdown("### ➕ Adicionar Novo Usuário")
    with st.form("form_add_user"):
        novo_usuario = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Senha", type="password")
        novo_perfil = st.selectbox("Perfil", ["administrador", "gerencia", "coordenadores", "odonto", "manutenção I", "transporte", "manutenção II", "rh", "manutenção III"])
        submit_add = st.form_submit_button("Cadastrar")
        if submit_add:
            hash_senha = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
            novo_dado = pd.DataFrame([[novo_usuario, hash_senha, novo_perfil]], columns=["usuario", "senha", "perfil"])
            df_usuarios = pd.concat([df_usuarios, novo_dado], ignore_index=True)
            df_usuarios.to_csv("usuarios.csv", index=False)
            st.success("✅ Usuário cadastrado com sucesso!")

    st.markdown("### 🗑️ Excluir Usuário")
    usuario_excluir = st.selectbox("Selecionar usuário para excluir", df_usuarios["usuario"].tolist())
    if st.button("Excluir"):
        df_usuarios = df_usuarios[df_usuarios["usuario"] != usuario_excluir]
        df_usuarios.to_csv("usuarios.csv", index=False)
        st.success(f"✅ Usuário '{usuario_excluir}' excluído com sucesso!")

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
    totais = df_filtrado[colunas_despesa].sum().sort_values(ascending=False)

    st.subheader("📌 Total por Categoria de Despesa")
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
    fig3, ax3 = plt.subplots(figsize=(8, 6))
    totais.plot(
    kind="pie", 
    ax=ax3, 
    startangle=90, 
    labels=None,
    autopct="%1.1f%%"
    )
    ax3.set_ylabel("")
    ax3.set_title("Distribuição das Despesas")
    ax3.legend(
    labels=totais.index, 
    loc="center left", 
    bbox_to_anchor=(1.0, 0.5), 
    title="Categorias"
    )
    st.pyplot(fig3)

    st.subheader("📤 Exportar Relatório")
    col1, col2 = st.columns(2)
    with col1:
        excel_buffer = BytesIO()
        df_filtrado.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)
        st.download_button("📥 Baixar Excel", data=excel_buffer, file_name="despesas_filtradas.xlsx")

    with col2:
        pdf_buffer = gerar_pdf(totais, unidade_sel, competencia_sel)
        st.download_button("📄 Gerar PDF", data=pdf_buffer, file_name="relatorio_despesas.pdf")

    st.subheader("📊 Comparativo de Despesas por Ano")
    df["Ano"] = df["Competência"].str[-4:]
    anos_disponiveis = sorted(df["Ano"].dropna().unique().tolist())

    col1, col2 = st.columns(2)
    with col1:
        ano1 = st.selectbox("Selecionar Ano 1", anos_disponiveis, key="ano1")
    with col2:
        ano2 = st.selectbox("Selecionar Ano 2", anos_disponiveis, index=1 if len(anos_disponiveis) > 1 else 0, key="ano2")

    if ano1 != ano2:
        df_ano1 = df[df["Ano"] == ano1]
        df_ano2 = df[df["Ano"] == ano2]

        soma1 = df_ano1[colunas_despesa].sum()
        soma2 = df_ano2[colunas_despesa].sum()

        df_comparativo = pd.DataFrame({
            ano1: soma1,
            ano2: soma2
        })

        st.markdown("#### 💹 Comparativo Total por Categoria")
        fig4, ax4 = plt.subplots(figsize=(10, 5))
        df_comparativo.plot(kind="bar", ax=ax4)
        ax4.set_ylabel("Valor (R$)")
        ax4.set_title("Totais por Tipo de Despesa")
        st.pyplot(fig4)

        st.markdown("#### 📈 Evolução Mensal Comparativa")
        df["Mês"] = df["Competência"].str[:2]
        df["Ano-Mês"] = df["Ano"] + "-" + df["Mês"]

        df_mensal = df.groupby(["Ano", "Mês"])[colunas_despesa].sum().reset_index()
        df_mensal["Ano-Mês"] = df_mensal["Ano"] + "-" + df_mensal["Mês"]

        fig5, ax5 = plt.subplots(figsize=(10, 5))
        for col in colunas_despesa:
            dados1 = df_mensal[df_mensal["Ano"] == ano1].set_index("Ano-Mês")[col]
            dados2 = df_mensal[df_mensal["Ano"] == ano2].set_index("Ano-Mês")[col]
            dados1.plot(ax=ax5, label=f"{col} ({ano1})", linestyle="--")
            dados2.plot(ax=ax5, label=f"{col} ({ano2})")
        ax5.set_ylabel("Valor (R$)")
        ax5.set_title("Evolução Mensal das Despesas")
        ax5.legend(loc="upper left", bbox_to_anchor=(1, 1))
        st.pyplot(fig5)
    else:
        st.info("Selecione dois anos diferentes para comparar.")
        
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    check_login()
else:
    st.sidebar.markdown(f"🧍‍♂️ Usuário: `{st.session_state['usuario']}`")
    st.sidebar.markdown(f"🔐 Perfil: `{st.session_state['perfil']}`")

    perfil = st.session_state.get("perfil", "")

    if perfil == "administrador":
        abas = ["Formulário", "Dashboard", "Gerenciar Usuários"]
    elif perfil == "gerencia":
        abas = ["Formulário", "Dashboard"]
    else:
        abas = ["Formulário"]

    aba = st.sidebar.radio("Menu", abas)

    if st.sidebar.button("🚪 Sair"):
        usuario = st.session_state.get("usuario", "desconhecido")
        registrar_log(usuario, "logout")
        st.session_state.clear()
        st.rerun()

    if aba == "Formulário":
        formulario_despesas()
    elif aba == "Dashboard":
        dashboard()
    elif aba == "Gerenciar Usuários" and perfil == "administrador":
        gerenciar_usuarios()
