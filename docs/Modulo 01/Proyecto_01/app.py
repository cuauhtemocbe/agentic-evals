import os
import sys

import streamlit as st
from PIL import Image

# Cargar módulos del proyecto (ancla el import a la ubicación de este archivo,
# igual que agent.py, para que funcione sin importar el cwd desde el que se
# lance `streamlit run`).
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent import DataClassifierAgent
from main import is_ollama_active

st.set_page_config(
    page_title="Agente de Clasificación de Datos",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_TEXT_CATEGORIES = [
    "Queja",
    "Felicitación",
    "Duda",
    "Alerta de Infraestructura",
    "Error de Base de Datos",
]
DEFAULT_IMAGE_CATEGORIES = ["Factura", "Ticket", "Logo", "Otro"]


@st.cache_resource
def get_agent() -> DataClassifierAgent:
    return DataClassifierAgent()


agent = get_agent()

with st.sidebar:
    st.title("🧠 Panel de Control")
    st.markdown("---")

    if is_ollama_active():
        st.success("🟢 Ollama: Activo")
    else:
        st.error("🔴 Ollama: Inaccesible")
        st.warning(
            "Iniciá la aplicación de Ollama en tu máquina y asegurate de tener "
            f"el modelo `{agent.model}` descargado (`ollama pull {agent.model}`)."
        )

    st.caption(f"Modelo: `{agent.model}`")
    st.caption(f"Endpoint: `{agent.api_url}`")

st.title("🧠 Agente de Clasificación de Datos")
st.markdown(
    "Interfaz gráfica para el agente de clasificación de texto y análisis de "
    "imágenes con LLM local (Ollama + Qwen3-VL). Ver `agent.py` para la lógica "
    "y `main.py`/`Proyecto_01.ipynb` para la demo por consola/notebook."
)

tab_text, tab_image = st.tabs(["📝 Clasificar Texto", "🖼️ Analizar Imagen"])

with tab_text:
    st.subheader("Clasificación de texto no estructurado")

    text_input = st.text_area(
        "Texto a clasificar",
        placeholder="Pegá un comentario de cliente, log de error, etc.",
        height=150,
    )
    categories_input = st.text_input(
        "Categorías posibles (separadas por coma)",
        value=", ".join(DEFAULT_TEXT_CATEGORIES),
    )

    if st.button("Clasificar", type="primary", key="classify_text_btn"):
        categories = [c.strip() for c in categories_input.split(",") if c.strip()]
        if not text_input.strip():
            st.error("Ingresá un texto para clasificar.")
        elif not categories:
            st.error("Ingresá al menos una categoría.")
        else:
            with st.spinner("Clasificando con el LLM local..."):
                result = agent.classify_text(text_input, categories)

            if result["success"]:
                col1, col2 = st.columns(2)
                col1.metric("Categoría", result["category"])
                col2.metric("Confianza", f"{result['confidence'] * 100:.1f}%")
                st.progress(min(max(result["confidence"], 0.0), 1.0))
                st.markdown(f"**Justificación:** {result['description']}")
                st.caption(f"Latencia: {result['latency_sec']:.2f} s")
            else:
                st.error(result["description"])

with tab_image:
    st.subheader("Análisis de imágenes (facturas, tickets, logos)")

    uploaded_file = st.file_uploader("Subí una imagen", type=["png", "jpg", "jpeg"])
    image_categories_input = st.text_input(
        "Categorías posibles (separadas por coma)",
        value=", ".join(DEFAULT_IMAGE_CATEGORIES),
        key="image_categories_input",
    )

    if uploaded_file is not None:
        st.image(Image.open(uploaded_file), caption=uploaded_file.name, width=350)

    if st.button("Analizar imagen", type="primary", key="analyze_image_btn"):
        if uploaded_file is None:
            st.error("Subí una imagen para analizar.")
        else:
            categories = [
                c.strip() for c in image_categories_input.split(",") if c.strip()
            ]

            # agent.analyze_image lee la imagen desde disco, así que guardamos
            # el archivo subido a una ruta temporal dentro de data/ antes de analizarlo.
            temp_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "data", "uploads"
            )
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Analizando la imagen con el LLM de visión local..."):
                result = agent.analyze_image(temp_path, categories=categories)

            if result["success"]:
                col1, col2 = st.columns(2)
                col1.metric("Categoría", result["category"])
                col2.metric("Confianza", f"{result['confidence'] * 100:.1f}%")
                st.progress(min(max(result["confidence"], 0.0), 1.0))
                st.markdown(f"**Descripción:** {result['description']}")
                st.caption(f"Latencia: {result['latency_sec']:.2f} s")
            else:
                st.error(result["description"])
