import streamlit as st
import asyncio
import os
import json
from datetime import datetime
from main import generate_learning_path

# Importar el sistema de historial
import history_service as hs
from history_ui import manage_history_ui, save_generated_learning_path

# ------------------------------------------------------------------------------
# Helper: Asynchronous progress callback for updating progress logs in the UI
# ------------------------------------------------------------------------------
async def progress_callback(message: str):
    if "progress_log" not in st.session_state:
        st.session_state.progress_log = []
    st.session_state.progress_log.append(message)
    if "progress_placeholder" in st.session_state:
        st.session_state.progress_placeholder.text("\n".join(st.session_state.progress_log))


# ------------------------------------------------------------------------------
# Main function: Sets up the UI and launches the generation process
# ------------------------------------------------------------------------------
def main():
    st.title("Generador de Rutas de Aprendizaje")

    # -------------------------------
    # Tabs: Main Navigation
    # -------------------------------
    tab1, tab2 = st.tabs(["Generador", "Historial"])
    
    with tab1:
        generate_tab()
    
    with tab2:
        manage_history_ui()

def generate_tab():
    """Contenido de la pestaña de generación de rutas de aprendizaje."""
    # -------------------------------
    # Sidebar: Configuration and API Keys
    # -------------------------------
    st.sidebar.header("Configuración")
    
    # Input for topic
    topic = st.sidebar.text_input("Tema de la ruta de aprendizaje", value="Historia de España")
    
    # Parallelism parameters
    parallel_count = st.sidebar.number_input("Módulos paralelos", min_value=1, max_value=10, value=2, step=1)
    search_parallel_count = st.sidebar.number_input("Búsquedas paralelas", min_value=1, max_value=10, value=3, step=1)
    submodule_parallel_count = st.sidebar.number_input("Submódulos paralelos", min_value=1, max_value=10, value=2, step=1)
    
    # API keys: Check in environment; if missing, let user enter them
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

    # Opciones adicionales
    st.sidebar.markdown("---")
    save_to_history = st.sidebar.checkbox("Guardar automáticamente en historial", value=True)

    generate_button = st.sidebar.button("Generar Ruta de Aprendizaje")

    # Placeholders for progress and output
    progress_placeholder = st.empty()
    st.session_state.progress_placeholder = progress_placeholder
    output_placeholder = st.empty()

    # -------------------------------
    # Main Panel: Generation process and results
    # -------------------------------
    if generate_button:
        if not topic:
            st.error("Por favor, ingresa un tema para generar la ruta de aprendizaje.")
        elif not os.environ.get("OPENAI_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
            st.error("Falta alguna API key necesaria. Ingresa ambas API keys en el sidebar.")
        else:
            st.info("Generando ruta de aprendizaje. Este proceso puede tardar varios minutos...")
            # Reset progress log
            st.session_state.progress_log = []
            progress_placeholder.text("Iniciando el proceso...")
            try:
                # Run the asynchronous learning path generation process
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

            # ------------------------------------------------------------------------------
            # Display the final learning path result if available
            # ------------------------------------------------------------------------------
            if result:
                output_placeholder.header(f"Ruta de Aprendizaje para: {result.get('topic', topic)}")
                
                # Show execution steps in an expander (single level)
                if result.get("execution_steps"):
                    with st.expander("Pasos de ejecución"):
                        for step in result["execution_steps"]:
                            st.write(step)
                
                modules = result.get("modules", [])
                if modules:
                    for module in modules:
                        with st.expander(f"Módulo: {module.get('title', 'Sin título')}"):
                            st.write(module.get("description", "Sin descripción"))
                            
                            # List submodules (if available) without nesting expanders
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
                                # Fallback if module content is provided directly
                                content = module.get("content", "")
                                if content:
                                    st.write(content)
                                else:
                                    st.warning("No se encontraron submódulos ni contenido para este módulo.")
                else:
                    st.error("La generación no produjo módulos. Revisa los logs para más detalles.")

                # Acciones con el resultado
                col1, col2 = st.columns(2)
                
                with col1:
                    # Download button for JSON result
                    json_result = json.dumps(result, ensure_ascii=False, indent=4)
                    st.download_button("⬇️ Descargar Ruta (JSON)", json_result, 
                                      file_name=f"learning_path_{result.get('topic', 'learning_path').replace(' ', '_')}.json",
                                      key=f"download_generated_{datetime.now().strftime('%Y%m%d%H%M%S')}")
                
                with col2:
                    # Guarda en historial (si está habilitado)
                    if save_to_history:
                        save_generated_learning_path(result)
                    else:
                        # Ofrecer la opción manual
                        if st.button("💾 Guardar en historial"):
                            save_generated_learning_path(result)
            else:
                st.error("No se pudo generar la ruta de aprendizaje. Verifica los logs y la configuración.")

    # Área para importar un JSON directamente
    st.markdown("---")
    with st.expander("Importar ruta de aprendizaje desde JSON"):
        uploaded_file = st.file_uploader("Selecciona un archivo JSON", type=["json"], key="import_json_generator")
        if uploaded_file is not None:
            try:
                string_data = uploaded_file.getvalue().decode("utf-8")
                json_data = json.loads(string_data)
                
                if isinstance(json_data, dict) and "topic" in json_data and "modules" in json_data:
                    st.success(f"Ruta de aprendizaje válida para el tema: {json_data.get('topic')}")
                    
                    # Opciones después de cargar
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
                    st.error("El archivo JSON no tiene el formato esperado de una ruta de aprendizaje.")
            except json.JSONDecodeError:
                st.error("El archivo no es un JSON válido.")
            except Exception as e:
                st.error(f"Error al procesar el archivo: {str(e)}")
    
    # Mostrar una ruta importada si existe
    if "imported_path" in st.session_state:
        imported_path = st.session_state["imported_path"]
        st.markdown("---")
        st.header(f"Ruta Importada: {imported_path.get('topic', 'Sin título')}")
        
        # Botón para cerrar la vista
        if st.button("✕ Cerrar vista"):
            del st.session_state["imported_path"]
            st.rerun()
        
        # Mostrar contenido igual que con las rutas generadas
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
                            st.warning("No se encontraron submódulos ni contenido para este módulo.")
        else:
            st.error("No se encontraron módulos en esta ruta importada.")


if __name__ == "__main__":
    main()
