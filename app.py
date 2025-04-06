
import streamlit as st
import pandas as pd
import os

# ---- LOGIN SIMPLES ----
def check_login():
    usuarios = {
        "admin": "123456",
        "ubs1": "ubs123",
        "ubs2": "ubs456"
    }
    
    with st.form("login_form"):
        st.write("🔐 Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            if usuario in usuarios and senha == usuarios[usuario]:
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
            else:
                st.error("Usuário ou senha inválidos.")

# ---- APP PRINCIPAL ----
def main():
    # Carrega arquivos
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

# ---- EXECUÇÃO ----
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    check_login()
else:
    main()
