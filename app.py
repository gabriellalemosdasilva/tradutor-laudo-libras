import streamlit as st
from pypdf import PdfReader

# Configuração da página
st.set_page_config(page_title="Tradutor de Laudos para LIBRAS", layout="wide")

st.title("🩺 Tradutor Assistivo de Laudos Médicos")
st.markdown("Faça o upload do seu laudo médico e visualize os termos e explicações em LIBRAS.")

# Função para converter link ou ID do Google Drive em link incorporável (embed)
def get_drive_embed_url(url_ou_id: str) -> str:
    if "drive.google.com" in url_ou_id:
        if "/d/" in url_ou_id:
            file_id = url_ou_id.split("/d/")[1].split("/")[0]
        elif "id=" in url_ou_id:
            file_id = url_ou_id.split("id=")[1].split("&")[0]
        else:
            file_id = url_ou_id
    else:
        file_id = url_ou_id
    return f"https://drive.google.com/file/d/{file_id}/preview"

# Dicionário de conhecimento com links/IDs do Google Drive
# Lembre-se: o vídeo no Drive deve estar com compartilhamento: "Qualquer pessoa com o link pode ver"
base_conhecimento = {
    "escoliose": {
        "sinal": "1ABC123ExemploIDSinalEscoliose",       # Cole o ID ou link completo do Drive
        "explicacao": "1XYZ789ExemploIDDefinicaoEscoliose"
    },
    "cifose": {
        "sinal": "https://drive.google.com/file/d/ID_CIFOSE_EXEMPLO/view",
        "explicacao": "https://drive.google.com/file/d/ID_CIFOSE_EXPLICACAO/view"
    }
}

# Upload do arquivo
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
            st.error(f"Erro ao ler o PDF: {e}")
    else:
        try:
            conteudo_bruto = uploaded_file.read().decode("utf-8")
        except Exception:
            conteudo_bruto = uploaded_file.read().decode("latin-1", errors="ignore")

    conteudo_limpo = " ".join(conteudo_bruto.split()).lower()

    # Filtro de Seção: prioriza seções finais (Conclusão / Impressão diagnóstica)
    secoes_relevantes = ["conclusão", "conclusao", "impressão diagnóstica", "impressao diagnostica", "diagnóstico", "diagnostico"]
    texto_analise = conteudo_limpo

    for secao in secoes_relevantes:
        if secao in conteudo_limpo:
            # Pega o texto a partir do ponto onde a palavra de conclusão aparece
            texto_analise = conteudo_limpo.split(secao, 1)[1]
            st.info(f"Análise focada a partir da seção: **{secao.upper()}**")
            break

    with st.expander("📄 Ver texto processado do laudo"):
        st.write(texto_analise)

    # Identificação de TODOS os termos presentes no laudo
    termos_encontrados = [termo for termo in base_conhecimento.keys() if termo in texto_analise]

    # Exibição dos resultados
    if termos_encontrados:
        st.success(f"{len(termos_encontrados)} termo(s) identificado(s): **{', '.join([t.upper() for t in termos_encontrados])}**")
        st.markdown("---")

        # Cria uma aba para cada termo encontrado
        abas = st.tabs([f"📌 {termo.upper()}" for termo in termos_encontrados])

        for aba, termo in zip(abas, termos_encontrados):
            with aba:
                col1, col2 = st.columns(2)
                url_sinal = get_drive_embed_url(base_conhecimento[termo]["sinal"])
                url_expl = get_drive_embed_url(base_conhecimento[termo]["explicacao"])

                with col1:
                    st.subheader("🤲 Sinal em Libras")
                    st.markdown(
                        f'<iframe src="{url_sinal}" width="100%" height="340" style="border:none; border-radius:8px;" allow="autoplay"></iframe>',
                        unsafe_allow_html=True
                    )

                with col2:
                    st.subheader("💡 Descrição")
                    st.markdown(
                        f'<iframe src="{url_expl}" width="100%" height="340" style="border:none; border-radius:8px;" allow="autoplay"></iframe>',
                        unsafe_allow_html=True
                    )
    else:
        st.warning("Nenhum termo clínico cadastrado no glossário foi identificado neste laudo.")
else:
    st.info("Por favor, faça o upload de um arquivo para iniciar a análise.")
