from typing import Any, Dict
import streamlit as st
import json
from datetime import datetime
from history import history_service as hs

def format_date(date_str: str) -> str:
    try:
        date = datetime.fromisoformat(date_str)
        return date.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str

def render_history_tab():
    st.header("Historial de Rutas de Aprendizaje")
    preview_data = hs.get_history_preview()
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_term = st.text_input("Buscar por tema:", key="history_search")
    with col2:
        sort_options = {"creation_date": "Fecha de creación", "last_modified_date": "Última modificación", "topic": "Tema", "favorite": "Favoritos primero"}
        sort_by = st.selectbox("Ordenar por:", options=list(sort_options.keys()), format_func=lambda x: sort_options[x], key="history_sort")
    with col3:
        source_options = ["Todos", "Generados", "Importados"]
        source_filter = st.selectbox("Origen:", options=source_options, key="history_source")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        uploaded_file = st.file_uploader("Importar JSON:", type=["json"], key="import_json")
        if uploaded_file is not None:
            try:
                string_data = uploaded_file.getvalue().decode("utf-8")
                success, message = hs.import_learning_path(string_data)
                if success:
                    st.success(message)
                    preview_data = hs.get_history_preview()
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error importing: {str(e)}")
    with col2:
        if st.button("Exportar todo el historial"):
            json_data = hs.export_history()
            st.download_button(
                label="Descargar historial completo",
                data=json_data,
                file_name=f"learning_path_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="download_complete_history"
            )
    with col3:
        if st.button("Limpiar historial"):
            if st.session_state.get("confirm_clear", False):
                if hs.clear_history():
                    st.success("Historial eliminado correctamente")
                    preview_data = []
                    st.session_state["confirm_clear"] = False
                else:
                    st.error("Error al eliminar el historial")
            else:
                st.session_state["confirm_clear"] = True
                st.warning("¿Estás seguro? Haz clic de nuevo para confirmar.")
    filtered_data = preview_data
    if search_term:
        filtered_data = [entry for entry in filtered_data if search_term.lower() in entry["topic"].lower()]
    if source_filter == "Generados":
        filtered_data = [entry for entry in filtered_data if entry["source"] == "generated"]
    elif source_filter == "Importados":
        filtered_data = [entry for entry in filtered_data if entry["source"] == "imported"]
    if not filtered_data:
        st.info("No hay rutas en el historial. Genera o importa una ruta para comenzar.")
        return
    for i, entry in enumerate(filtered_data):
        with st.expander(f"📚 {entry['topic']} ({format_date(entry['creation_date'])})", expanded=i==0 and len(filtered_data)==1):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Creado:** {format_date(entry['creation_date'])}")
                if entry['last_modified_date']:
                    st.write(f"**Modificado:** {format_date(entry['last_modified_date'])}")
                st.write(f"**Módulos:** {entry['modules_count']}")
            with col2:
                st.write(f"**Origen:** {'Generado' if entry['source'] == 'generated' else 'Importado'}")
                tags = entry.get('tags', [])
                if tags:
                    st.write("**Etiquetas:** " + ", ".join(tags))
                new_tag = st.text_input("Nueva etiqueta:", key=f"tag_input_{entry['id']}")
                if new_tag:
                    if st.button("Añadir etiqueta", key=f"add_tag_{entry['id']}"):
                        updated_tags = tags + [new_tag]
                        if hs.update_learning_path_metadata(entry['id'], tags=updated_tags):
                            st.success(f"Etiqueta '{new_tag}' añadida")
                            st.rerun()
            with col3:
                is_favorite = entry.get('favorite', False)
                if st.button("★ Favorito" if is_favorite else "☆ Marcar favorito", key=f"fav_{entry['id']}"):
                    if hs.update_learning_path_metadata(entry['id'], favorite=not is_favorite):
                        st.rerun()
                if st.button("🗑️ Eliminar", key=f"del_{entry['id']}"):
                    if st.session_state.get(f"confirm_delete_{entry['id']}", False):
                        if hs.delete_learning_path(entry['id']):
                            st.success("Ruta eliminada correctamente")
                            st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{entry['id']}"] = True
                        st.warning("¿Confirmar eliminación?")
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Ver ruta completa", key=f"view_{entry['id']}"):
                    complete_data = hs.get_learning_path(entry['id'])
                    if complete_data:
                        st.session_state["selected_learning_path"] = complete_data
                        st.session_state["selected_learning_path_id"] = entry['id']
                        st.rerun()
            with col2:
                learning_path = hs.get_learning_path(entry['id'])
                if learning_path:
                    json_result = json.dumps(learning_path, ensure_ascii=False, indent=4)
                    st.download_button("⬇️ Descargar JSON", json_result, 
                                       file_name=f"learning_path_{entry['topic'].replace(' ', '_')}.json",
                                       key=f"download_{entry['id']}")
                    
def render_learning_path_viewer(learning_path: Dict[str, Any], entry_id: str):
    if st.button("← Volver al historial"):
        st.session_state.pop("selected_learning_path", None)
        st.session_state.pop("selected_learning_path_id", None)
        st.rerun()
    st.header(f"Ruta de Aprendizaje: {learning_path.get('topic', 'Sin título')}")
    if learning_path.get("execution_steps"):
        with st.expander("Pasos de ejecución"):
            for step in learning_path["execution_steps"]:
                st.write(step)
    modules = learning_path.get("modules", [])
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
                        st.warning("No se encontraron submódulos ni contenido.")
    else:
        st.error("No se encontraron módulos en esta ruta.")
    json_result = json.dumps(learning_path, ensure_ascii=False, indent=4)
    st.download_button("Descargar Ruta (JSON)", json_result, 
                       file_name=f"learning_path_{learning_path.get('topic', 'learning_path').replace(' ', '_')}.json",
                       key=f"download_detail_{entry_id}")

def save_generated_learning_path(learning_path: Dict[str, Any]) -> None:
    if hs.add_learning_path(learning_path):
        st.sidebar.success("Ruta guardada en el historial")
    else:
        st.sidebar.error("Error al guardar la ruta")

def manage_history_ui():
    if "selected_learning_path" in st.session_state and "selected_learning_path_id" in st.session_state:
        render_learning_path_viewer(st.session_state["selected_learning_path"], st.session_state["selected_learning_path_id"])
    else:
        render_history_tab()
