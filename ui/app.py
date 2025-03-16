import streamlit as st
import asyncio
import os
import json
from datetime import datetime
from main import generate_learning_path
from history import history_service as hs
from history.history_ui import manage_history_ui, save_generated_learning_path

async def progress_callback(message: str):
    if "progress_log" not in st.session_state:
        st.session_state.progress_log = []
    st.session_state.progress_log.append(message)
    if "progress_placeholder" in st.session_state:
        st.session_state.progress_placeholder.text("\n".join(st.session_state.progress_log))

def main():
    st.title("Generador de Rutas de Aprendizaje")
    tab1, tab2 = st.tabs(["Generador", "Historial"])
    with tab1:
        generate_tab()
    with tab2:
        manage_history_ui()

def generate_tab():
    st.sidebar.header("Configuración")
    topic = st.sidebar.text_input("Tema de la ruta de aprendizaje", value="Historia de España")
    parallel_count = st.sidebar.number_input("Módulos paralelos", min_value=1, max_value=10, value=2, step=1)
    search_parallel_count = st.sidebar.number_input("Búsquedas paralelas", min_value=1, max_value=10, value=3, step=1)
    submodule_parallel_count = st.sidebar.number_input("Submódulos paralelos", min_value=1, max_value=10, value=2, step=1)
    openai_key = os.environ.get("OPENAI_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not openai_key:
        openai_key = st.sidebar.text_input("OPENAI_API_KEY", type="password")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
    if not tavily_key:
        tavily_key = st.sidebar.text_input("TAVILY_API_KEY", type="password")
        if tavily_key:
            os.environ["TAVILY_API_KEY"] = tavily_key
    st.sidebar.markdown("---")
    save_to_history = st.sidebar.checkbox("Guardar automáticamente en historial", value=True)
    generate_button = st.sidebar.button("Generar Ruta de Aprendizaje")
    progress_placeholder = st.empty()
    st.session_state.progress_placeholder = progress_placeholder
    output_placeholder = st.empty()
    if generate_button:
        if not topic:
            st.error("Ingresa un tema.")
        elif not os.environ.get("OPENAI_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
            st.error("Faltan API keys necesarias.")
        else:
            st.info("Generando ruta... Puede tardar varios minutos.")
            st.session_state.progress_log = []
            progress_placeholder.text("Iniciando el proceso...")
            try:
                result = asyncio.run(generate_learning_path(
                    topic=topic,
                    parallel_count=parallel_count,
                    search_parallel_count=search_parallel_count,
                    submodule_parallel_count=submodule_parallel_count,
                    progress_callback=progress_callback
                ))
            except Exception as e:
                st.error(f"Error durante la generación: {str(e)}")
                result = None
            if result:
                output_placeholder.header(f"Ruta de Aprendizaje para: {result.get('topic', topic)}")
                if result.get("execution_steps"):
                    with st.expander("Pasos de ejecución"):
                        for step in result["execution_steps"]:
                            st.write(step)
                modules = result.get("modules", [])
                if modules:
                    for module in modules:
                        with st.expander(f"Módulo: {module.get('title', 'Sin título')}"):
                            st.write(module.get("description", "Sin descripción"))
                            submodules = module.get("submodules", [])
                            if submodules:
                                st.markdown("##### Submódulos:")
                                for sub in submodules:
                                    st.markdown(f"**{sub.get('title', 'Sin título')}**")
                                    st.write(sub.get("description", "Sin descripción"))
                                    content = sub.get("content", "")
                                    if content:
                                        st.write(content)
                                    else:
                                        st.warning("Sin contenido generado.")
                            else:
                                content = module.get("content", "")
                                if content:
                                    st.write(content)
                                else:
                                    st.warning("No se encontró contenido.")
                else:
                    st.error("No se generaron módulos. Revisa los logs.")
                col1, col2 = st.columns(2)
                with col1:
                    json_result = json.dumps(result, ensure_ascii=False, indent=4)
                    st.download_button("⬇️ Descargar Ruta (JSON)", json_result, 
                                       file_name=f"learning_path_{result.get('topic', 'learning_path').replace(' ', '_')}.json",
                                       key=f"download_{datetime.now().strftime('%Y%m%d%H%M%S')}")
                with col2:
                    if save_to_history:
                        save_generated_learning_path(result)
                    else:
                        if st.button("💾 Guardar en historial"):
                            save_generated_learning_path(result)
            else:
                st.error("No se pudo generar la ruta.")
    st.markdown("---")
    with st.expander("Importar ruta desde JSON"):
        uploaded_file = st.file_uploader("Selecciona un archivo JSON", type=["json"], key="import_json_generator")
        if uploaded_file is not None:
            try:
                string_data = uploaded_file.getvalue().decode("utf-8")
                json_data = json.loads(string_data)
                if isinstance(json_data, dict) and "topic" in json_data and "modules" in json_data:
                    st.success(f"Ruta válida para: {json_data.get('topic')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📋 Ver contenido"):
                            st.session_state["imported_path"] = json_data
                            st.rerun()
                    with col2:
                        if st.button("💾 Guardar en historial", key="save_imported"):
                            success, msg = hs.import_learning_path(string_data)
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)
                else:
                    st.error("El JSON no tiene el formato correcto.")
            except json.JSONDecodeError:
                st.error("Archivo no es un JSON válido.")
            except Exception as e:
                st.error(f"Error al procesar el archivo: {str(e)}")
    if "imported_path" in st.session_state:
        imported_path = st.session_state["imported_path"]
        st.markdown("---")
        st.header(f"Ruta Importada: {imported_path.get('topic', 'Sin título')}")
        if st.button("✕ Cerrar vista"):
            del st.session_state["imported_path"]
            st.rerun()
        modules = imported_path.get("modules", [])
        if modules:
            for module in modules:
                with st.expander(f"Módulo: {module.get('title', 'Sin título')}"):
                    st.write(module.get("description", "Sin descripción"))
                    submodules = module.get("submodules", [])
                    if submodules:
                        st.markdown("##### Submódulos:")
                        for sub in submodules:
                            st.markdown(f"**{sub.get('title', 'Sin título')}**")
                            st.write(sub.get("description", "Sin descripción"))
                            content = sub.get("content", "")
                            if content:
                                st.write(content)
                            else:
                                st.warning("Sin contenido generado.")
                    else:
                        content = module.get("content", "")
                        if content:
                            st.write(content)
                        else:
                            st.warning("No se encontró contenido.")
        else:
            st.error("No se encontraron módulos en esta ruta importada.")

if __name__ == "__main__":
    main()
