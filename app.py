import streamlit as st
import pandas as pd
from pypdf import PdfReader

# Configuração da página
st.set_page_config(page_title="Tradutor de Laudos para LIBRAS", layout="wide")

st.title("🩺 Tradutor Assistivo de Laudos Médicos")
st.markdown("Faça o upload do seu laudo médico e visualize os termos e explicações em LIBRAS.")

# URL da sua planilha publicada como CSV no Google Sheets
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSvbw2ebNuVIG6VW0aL8aSkYHumixO8HqE3ZgOHsoAozlLQQDOGgoc112Ppc1eMpl_uTfZYiU6ZgNPJ/pub?output=csv"

@st.cache_data(ttl=600)  # Guarda em cache por 10 min para ser rápido
def carregar_glossario(url):
    try:
        df = pd.read_csv(url)
        # Garante que os termos fiquem minúsculos e sem espaços sobrando
        df['termo'] = df['termo'].astype(str).str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar glossário online: {e}")
        return pd.DataFrame(columns=["termo", "sinal", "explicacao"])

# Função para converter qualquer formato de link do Google Drive para visualização embutida (embed)
def formatar_drive_embed(url_ou_id: str) -> str:
    url_str = str(url_ou_id).strip()
    if "drive.google.com" in url_str:
        if "/d/" in url_str:
            file_id = url_str.split("/d/")[1].split("/")[0]
        elif "id=" in url_str:
            file_id = url_str.split("id=")[1].split("&")[0]
        else:
            file_id = url_str
    else:
        file_id = url_str
    return f"https://drive.google.com/file/d/{file_id}/preview"

# Carregamento do banco de dados
df_glossario = carregar_glossario(URL_PLANILHA_CSV)

# Upload do laudo
uploaded_file = st.file_uploader("Escolha o arquivo do laudo (PDF ou TXT)", type=['txt', 'pdf'])

if uploaded_file is not None:
    conteudo_bruto = ""

    # Extração de texto
    if uploaded_file.name.endswith(".pdf"):
        try:
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                texto_pagina = page.extract_text()
                if texto_pagina:
                    conteudo_bruto += texto_pagina + " "
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {e}")
    else:
        try:
            conteudo_bruto = uploaded_file.read().decode("utf-8")
        except Exception:
            conteudo_bruto = uploaded_file.read().decode("latin-1", errors="ignore")

    conteudo_limpo = " ".join(conteudo_bruto.split()).lower()

    # Priorização das seções de conclusão/impressão diagnóstica
    secoes_relevantes = [
        "conclusão", "conclusao", "impressão diagnóstica", 
        "impressao diagnostica", "diagnóstico", "diagnostico", "comentários"
    ]
    texto_analise = conteudo_limpo

    for secao in secoes_relevantes:
        if secao in conteudo_limpo:
            texto_analise = conteudo_limpo.split(secao, 1)[1]
            st.info(f"Análise focada a partir da seção: **{secao.upper()}**")
            break

    with st.expander("📄 Ver texto processado do laudo"):
        st.write(texto_analise)

    # Identificação dos termos presentes no laudo a partir da planilha
    termos_cadastrados = df_glossario['termo'].tolist()
    termos_encontrados = [t for t in termos_cadastrados if str(t) in texto_analise]

    if termos_encontrados:
        st.success(f"{len(termos_encontrados)} termo(s) clínico(s) identificado(s): **{', '.join([t.upper() for t in termos_encontrados])}**")
        st.markdown("---")

        abas = st.tabs([f"📌 {t.upper()}" for t in termos_encontrados])

        for aba, t in zip(abas, termos_encontrados):
            with aba:
                linha = df_glossario[df_glossario['termo'] == t].iloc[0]
                url_sinal = formatar_drive_embed(linha['sinal'])
                url_expl = formatar_drive_embed(linha['explicacao'])

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🤲 Sinal em LIBRAS")
                    st.markdown(
                        f'<iframe src="{url_sinal}" width="100%" height="340" style="border:none; border-radius:8px;" allow="autoplay"></iframe>',
                        unsafe_allow_html=True
                    )
                with col2:
                    st.subheader("💡 Explicação Clínica")
                    st.markdown(
                        f'<iframe src="{url_expl}" width="100%" height="340" style="border:none; border-radius:8px;" allow="autoplay"></iframe>',
                        unsafe_allow_html=True
                    )
    else:
        st.warning("Nenhum termo clínico cadastrado no glossário foi identificado neste laudo.")
else:
    st.info("Faça o upload de um laudo para iniciar a análise.")
