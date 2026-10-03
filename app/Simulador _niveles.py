import streamlit as st
from openai import OpenAI

# ------------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTADO GLOBAL
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Simulador SIPRAI - Formulación y Evaluación",
    page_icon="🎯",
    layout="wide"
)

if "nivel_actual" not in st.session_state:
    st.session_state.nivel_actual = 1
if "idea_validada" not in st.session_state:
    st.session_state.idea_validada = ""
if "informe_perfil" not in st.session_state:
    st.session_state.informe_perfil = ""
if "evidencias_campo" not in st.session_state:
    st.session_state.evidencias_campo = ""
if "messages_n1" not in st.session_state:
    st.session_state.messages_n1 = []
if "messages_n4" not in st.session_state:
    st.session_state.messages_n4 = []

# Configuración de clave API de OpenAI
api_key = st.sidebar.text_input("Clave API de OpenAI", type="password")

if not api_key:
    st.warning("⚠️ Ingrese su API Key en la barra lateral para activar los Agentes.")
    st.stop()

client = OpenAI(api_key=api_key)

# ------------------------------------------------------------------------------
# BARRA LATERAL: NAVEGACIÓN Y PROGRESO
# ------------------------------------------------------------------------------
st.sidebar.title("📌 Estado del Proyecto")
st.sidebar.markdown(f"**Nivel Actual:** {st.session_state.nivel_actual} / 4")
st.sidebar.progress((st.session_state.nivel_actual - 1) / 3.0)

niveles_labels = {
    1: "1. Validación de Idea (Customer Discovery)",
    2: "2. Proyecto a Nivel de Perfil (IA Autónoma)",
    3: "3. Prefactibilidad (Fuentes Primarias)",
    4: "4. Factibilidad y Comité de Inversionistas"
}
st.sidebar.info(f"**Fase Activa:**\n{niveles_labels[st.session_state.nivel_actual]}")

if st.sidebar.button("🔄 Reiniciar Simulador"):
    st.session_state.clear()
    st.rerun()

# ------------------------------------------------------------------------------
# NIVEL 1: VALIDACIÓN DE IDEA (STEVE BLANK)
# ------------------------------------------------------------------------------
if st.session_state.nivel_actual == 1:
    st.title("💡 Nivel 1: Validación de la Idea")
    st.subheader("Agente 1: Asistente de Customer Discovery")
    st.write("Interactúa con el agente para demostrar que tu idea resuelve un problema real.")

    system_prompt_n1 = """
    Eres el "Agente de Customer Discovery", experto en Lean Startup y Steve Blank.
    Cuestiona al estudiante sobre el problema real, el cliente objetivo y sus evidencias preliminares.
    Cuando consideres que la idea está SUFICIENTEMENTE VALIDADA, escribe al final de tu mensaje: '[APROBADO_NIVEL_1]'.
    """

    for msg in st.session_state.messages_n1:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Describe tu idea, problema y cliente objetivo..."):
        st.session_state.messages_n1.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        messages_input = [{"role": "system", "content": system_prompt_n1}] + st.session_state.messages_n1
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages_input, temperature=0.7)
        reply = response.choices[0].message.content

        st.session_state.messages_n1.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

        if "[APROBADO_NIVEL_1]" in reply:
            st.success("¡Idea aprobada! Puedes avanzar al Nivel 2.")
            st.session_state.idea_validada = prompt
            if st.button("Avanzar al Nivel 2 (Perfil Autónomo)"):
                st.session_state.nivel_actual = 2
                st.rerun()

# ------------------------------------------------------------------------------
# NIVEL 2: PERFIL AUTÓNOMO POR IA
# ------------------------------------------------------------------------------
elif st.session_state.nivel_actual == 2:
    st.title("📄 Nivel 2: Proyecto a Nivel de Perfil (Fuentes Secundarias)")
    st.subheader("Agente 2: Investigador Autónomo")
    st.info(f"**Idea Validada:** {st.session_state.idea_validada}")

    if not st.session_state.informe_perfil:
        if st.button("🚀 Generar Informe de Perfil Autónomo"):
            with st.spinner("El Agente 2 está analizando las 4 etapas y 15 fases con fuentes secundarias..."):
                prompt_perfil = f"""
                Analiza el proyecto a NIVEL DE PERFIL: {st.session_state.idea_validada}
                Cubre las 4 etapas y 15 fases. Incluye PROS y CONTRAS en cada fase, un modelo financiero preliminar Top-Down
                y finaliza con '### DIAGNÓSTICO Y PUNTOS CRÍTICOS PARA PREFACTIBILIDAD' listando 3 variables críticas de campo.
                """
                response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt_perfil}], temperature=0.5)
                st.session_state.informe_perfil = response.choices[0].message.content
                st.rerun()
    else:
        st.markdown(st.session_state.informe_perfil)
        if st.button("Avanzar a Nivel 3 (Prefactibilidad)"):
            st.session_state.nivel_actual = 3
            st.rerun()

# ------------------------------------------------------------------------------
# NIVEL 3: PREFACTIBILIDAD (FUENTES PRIMARIAS)
# ------------------------------------------------------------------------------
elif st.session_state.nivel_actual == 3:
    st.title("🔬 Nivel 3: Prefactibilidad y Fuentes Primarias")
    st.subheader("Agente 3: Auditor de Campo")
    evidencias_input = st.text_area("Registra tus hallazgos de campo (muestreo, cotizaciones, costos reales):", height=150)

    if st.button("Auditar Evidencias"):
        if evidencias_input:
            with st.spinner("Auditando datos de campo..."):
                prompt_audit = f"Evalúa estas evidencias primarias: {evidencias_input}. Si son válidas incluye '[APROBADO_NIVEL_3]'."
                response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt_audit}], temperature=0.5)
                reply = response.choices[0].message.content
                st.markdown(reply)
                if "[APROBADO_NIVEL_3]" in reply:
                    st.session_state.evidencias_campo = evidencias_input
                    if st.button("Avanzar a Nivel 4 (Factibilidad)"):
                        st.session_state.nivel_actual = 4
                        st.rerun()

# ------------------------------------------------------------------------------
# NIVEL 4: FACTIBILIDAD Y COMITÉ
# ------------------------------------------------------------------------------
elif st.session_state.nivel_actual == 4:
    st.title("💼 Nivel 4: Factibilidad y Comité de Inversionistas")
    st.subheader("Agente 4: Presidente del Comité")
    st.write("Somete tu proyecto a la evaluación final del inversionista.")

    system_prompt_n4 = f"Eres el Presidente del Comité. Evalúa el proyecto basándote en: {st.session_state.evidencias_campo}. Si responde bien incluye '[APROBADO_FINAL]'."

    for msg in st.session_state.messages_n4:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt_n4 := st.chat_input("Responde a las preguntas del Comité..."):
        st.session_state.messages_n4.append({"role": "user", "content": prompt_n4})
        with st.chat_message("user"):
            st.markdown(prompt_n4)

        messages_input_n4 = [{"role": "system", "content": system_prompt_n4}] + st.session_state.messages_n4
        response_n4 = client.chat.completions.create(model="gpt-4o-mini", messages=messages_input_n4, temperature=0.7)
        reply_n4 = response_n4.choices[0].message.content

        st.session_state.messages_n4.append({"role": "assistant", "content": reply_n4})
        with st.chat_message("assistant"):
            st.markdown(reply_n4)

        if "[APROBADO_FINAL]" in reply_n4:
            st.balloons()
            st.success("🎉 ¡PROYECTO APROBADO PARA INVERSIÓN!")
