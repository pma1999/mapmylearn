import streamlit as st
import asyncio
import os
import json
from main import generate_learning_path

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

                # Download button for JSON result
                json_result = json.dumps(result, ensure_ascii=False, indent=4)
                st.download_button("Descargar Ruta de Aprendizaje (JSON)", json_result, file_name="learning_path.json")
            else:
                st.error("No se pudo generar la ruta de aprendizaje. Verifica los logs y la configuración.")


if __name__ == "__main__":
    main()
