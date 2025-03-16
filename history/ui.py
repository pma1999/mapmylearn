import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import io
import history.history_service as hs

def format_date(date_str: str) -> str:
    """Formatea una fecha ISO a un formato legible."""
    try:
        date = datetime.fromisoformat(date_str)
        return date.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str

def render_history_tab():
    """Renderiza la pestaña del historial de learning paths."""
    st.header("Historial de Rutas de Aprendizaje")
    
    # Carga inicial del historial
    preview_data = hs.get_history_preview()
    
    # Opciones de filtrado
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        # Filtro por tema
        search_term = st.text_input("Buscar por tema:", key="history_search")
    with col2:
        # Ordenar por
        sort_options = {
            "creation_date": "Fecha de creación",
            "last_modified_date": "Última modificación",
            "topic": "Tema",
            "favorite": "Favoritos primero"
        }
        sort_by = st.selectbox("Ordenar por:", options=list(sort_options.keys()),
                              format_func=lambda x: sort_options[x],
                              key="history_sort")
    with col3:
        # Filtro por origen
        source_options = ["Todos", "Generados", "Importados"]
        source_filter = st.selectbox("Origen:", options=source_options, key="history_source")
    
    # Acciones de importación/exportación
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        # Importar JSON
        uploaded_file = st.file_uploader("Importar JSON:", type=["json"], key="import_json")
        if uploaded_file is not None:
            # Procesar el archivo subido
            try:
                string_data = uploaded_file.getvalue().decode("utf-8")
                success, message = hs.import_learning_path(string_data)
                if success:
                    st.success(message)
                    # Recargar datos
                    preview_data = hs.get_history_preview()
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error al importar: {str(e)}")
    with col2:
        # Exportar todo el historial
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
        # Limpiar historial
        if st.button("Limpiar historial"):
            if st.session_state.get("confirm_clear", False):
                success = hs.clear_history()
                if success:
                    st.success("Historial eliminado correctamente")
                    preview_data = []  # Vaciar la vista previa
                    st.session_state["confirm_clear"] = False
                else:
                    st.error("Error al eliminar el historial")
            else:
                st.session_state["confirm_clear"] = True
                st.warning("¿Estás seguro? Esta acción no se puede deshacer. Haz clic de nuevo para confirmar.")
    
    # Filtrar resultados según criterios
    filtered_data = preview_data
    if search_term:
        filtered_data = [entry for entry in filtered_data 
                        if search_term.lower() in entry["topic"].lower()]
    
    if source_filter == "Generados":
        filtered_data = [entry for entry in filtered_data if entry["source"] == "generated"]
    elif source_filter == "Importados":
        filtered_data = [entry for entry in filtered_data if entry["source"] == "imported"]
    
    # Mostrar mensaje si no hay resultados
    if not filtered_data:
        st.info("No hay rutas de aprendizaje en el historial. Genera o importa una ruta para comenzar.")
        return
    
    # Mostrar cada entrada como una tarjeta
    for i, entry in enumerate(filtered_data):
        with st.expander(f"📚 {entry['topic']} ({format_date(entry['creation_date'])})", expanded=i==0 and len(filtered_data)==1):
            # Metadatos básicos
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Creado:** {format_date(entry['creation_date'])}")
                if entry['last_modified_date']:
                    st.write(f"**Modificado:** {format_date(entry['last_modified_date'])}")
                st.write(f"**Módulos:** {entry['modules_count']}")
            with col2:
                st.write(f"**Origen:** {'Generado' if entry['source'] == 'generated' else 'Importado'}")
                
                # Tags (etiquetas)
                tags = entry.get('tags', [])
                if tags:
                    st.write("**Etiquetas:** " + ", ".join(tags))
                
                # Editar etiquetas
                new_tag = st.text_input("Nueva etiqueta:", key=f"tag_input_{entry['id']}")
                if new_tag:
                    if st.button("Añadir etiqueta", key=f"add_tag_{entry['id']}"):
                        updated_tags = tags + [new_tag]
                        if hs.update_learning_path_metadata(entry['id'], tags=updated_tags):
                            st.success(f"Etiqueta '{new_tag}' añadida")
                            st.rerun()
            
            with col3:
                # Botón de favorito
                is_favorite = entry.get('favorite', False)
                if st.button(
                    "★ Favorito" if is_favorite else "☆ Marcar favorito", 
                    key=f"fav_{entry['id']}"
                ):
                    if hs.update_learning_path_metadata(entry['id'], favorite=not is_favorite):
                        st.rerun()
                
                # Botón de eliminar
                if st.button("🗑️ Eliminar", key=f"del_{entry['id']}"):
                    if st.session_state.get(f"confirm_delete_{entry['id']}", False):
                        if hs.delete_learning_path(entry['id']):
                            st.success("Ruta eliminada correctamente")
                            st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{entry['id']}"] = True
                        st.warning("¿Confirmar eliminación?")
            
            # Separación
            st.markdown("---")
            
            # Acciones principales
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Ver ruta completa", key=f"view_{entry['id']}"):
                    # Obtener datos completos
                    complete_data = hs.get_learning_path(entry['id'])
                    if complete_data:
                        st.session_state["selected_learning_path"] = complete_data
                        st.session_state["selected_learning_path_id"] = entry['id']
                        st.rerun()
            
            with col2:
                # Descargar esta ruta específica
                learning_path = hs.get_learning_path(entry['id'])
                if learning_path:
                    json_result = json.dumps(learning_path, ensure_ascii=False, indent=4)
                    st.download_button(
                        "⬇️ Descargar JSON", 
                        json_result, 
                        file_name=f"learning_path_{entry['topic'].replace(' ', '_')}.json",
                        key=f"download_{entry['id']}"
                    )

def render_learning_path_viewer(learning_path: Dict[str, Any], entry_id: str):
    """Renderiza la vista detallada de un learning path seleccionado."""
    # Botón para volver al historial
    if st.button("← Volver al historial"):
        st.session_state.pop("selected_learning_path", None)
        st.session_state.pop("selected_learning_path_id", None)
        st.rerun()
    
    st.header(f"Ruta de Aprendizaje: {learning_path.get('topic', 'Sin título')}")
    
    # Mostrar pasos de ejecución si están disponibles
    if learning_path.get("execution_steps"):
        with st.expander("Pasos de ejecución"):
            for step in learning_path["execution_steps"]:
                st.write(step)
    
    # Mostrar módulos
    modules = learning_path.get("modules", [])
    if modules:
        for module in modules:
            with st.expander(f"Módulo: {module.get('title', 'Sin título')}"):
                st.write(module.get("description", "Sin descripción"))
                
                # Mostrar submódulos si existen
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
                    # Contenido directo del módulo
                    content = module.get("content", "")
                    if content:
                        st.write(content)
                    else:
                        st.warning("No se encontraron submódulos ni contenido para este módulo.")
    else:
        st.error("No se encontraron módulos en esta ruta de aprendizaje.")
    
    # Botón para descargar JSON
    json_result = json.dumps(learning_path, ensure_ascii=False, indent=4)
    st.download_button(
        "Descargar Ruta de Aprendizaje (JSON)", 
        json_result, 
        file_name=f"learning_path_{learning_path.get('topic', 'learning_path').replace(' ', '_')}.json",
        key=f"download_detail_{entry_id}"
    )

def save_generated_learning_path(learning_path: Dict[str, Any]) -> None:
    """Guarda un learning path recién generado en el historial."""
    if hs.add_learning_path(learning_path):
        st.sidebar.success("Ruta de aprendizaje guardada en el historial")
    else:
        st.sidebar.error("Error al guardar en el historial")

def manage_history_ui():
    """Gestiona la UI del historial, mostrando el historial o un learning path específico."""
    # Comprobar si hay un learning path seleccionado para ver en detalle
    if "selected_learning_path" in st.session_state and "selected_learning_path_id" in st.session_state:
        render_learning_path_viewer(
            st.session_state["selected_learning_path"],
            st.session_state["selected_learning_path_id"]
        )
    else:
        # Si no hay ninguno seleccionado, mostrar el historial completo
        render_history_tab() 