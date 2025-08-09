import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def _format_date(date_obj: Union[str, datetime, None]) -> str:
    if not date_obj:
        return "N/A"
    if isinstance(date_obj, str):
        try:
            # Support common ISO variants
            if date_obj.endswith("Z"):
                # Remove Z and parse
                date_obj = datetime.fromisoformat(date_obj.replace("Z", "+00:00"))
            else:
                date_obj = datetime.fromisoformat(date_obj)
        except Exception:
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%dT%H:%M:%S.%fZ")
            except Exception:
                return str(date_obj)
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%B %d, %Y")
    return str(date_obj)


def _preprocess_markdown(text: str) -> str:
    if not text:
        return ""
    processed = text
    # Remove ```markdown only if at the very beginning
    if processed.startswith("```markdown\n"):
        processed = processed.replace("```markdown\n", "", 1)
    # Ensure space after # in headers
    processed = re.sub(r'(^|\n)(\#{1,6})([^\s#])', r'\1\2 \3', processed)
    return processed


def _extract_modules(path_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    modules: List[Dict[str, Any]] = []
    raw_modules: List[Dict[str, Any]] = []

    if isinstance(path_data, dict):
        if "modules" in path_data and isinstance(path_data["modules"], list):
            raw_modules = path_data["modules"]
        elif "content" in path_data and isinstance(path_data["content"], dict) and isinstance(path_data["content"].get("modules"), list):
            raw_modules = path_data["content"]["modules"]
        else:
            # Best-effort: first list of dicts we find
            for value in path_data.values():
                if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                    raw_modules = value
                    break

    for idx, module in enumerate(raw_modules):
        title = module.get("title", f"Module {idx+1}")
        description_md = _preprocess_markdown(module.get("description", ""))
        resources = module.get("resources", [])

        # Locate submodules under known keys
        submods_data = None
        for key in ["submodules", "sub_modules", "subModules", "subjects", "topics", "subtopics", "lessons"]:
            if key in module and isinstance(module[key], list):
                submods_data = module[key]
                break

        submodules: List[Dict[str, Any]] = []
        if submods_data:
            for j, sub in enumerate(submods_data):
                s_title = sub.get("title", f"Subtopic {j+1}")
                s_desc = _preprocess_markdown(sub.get("description", ""))
                s_content = _preprocess_markdown(sub.get("content", ""))
                s_resources = sub.get("resources", [])
                submodules.append({
                    "title": s_title,
                    "description": s_desc,
                    "content": s_content,
                    "resources": s_resources,
                })

        modules.append({
            "title": title,
            "description": description_md,
            "resources": resources,
            "submodules": submodules,
        })

    return modules


def _compose_resources_md(resources: List[Dict[str, Any]]) -> str:
    if not resources:
        return ""
    lines: List[str] = []
    lines.append("### Resources")
    for res in resources:
        title = res.get("title") or "Untitled"
        url = res.get("url")
        rtype = res.get("type")
        desc = res.get("description")
        bullet = f"- {title}"
        if url:
            bullet = f"- [{title}]({url})"
        meta_parts: List[str] = []
        if rtype:
            meta_parts.append(rtype)
        if desc:
            meta_parts.append(desc)
        if meta_parts:
            bullet += f" — {' | '.join(meta_parts)}"
        lines.append(bullet)
    lines.append("")
    return "\n".join(lines)


def _compose_markdown_document(learning_path: Dict[str, Any], modules: List[Dict[str, Any]], user_name: Optional[str]) -> str:
    topic = learning_path.get("topic", "Untitled Course")
    creation_date = _format_date(learning_path.get("creation_date"))
    last_modified_date = _format_date(learning_path.get("last_modified_date"))
    tags = learning_path.get("tags") or []
    source = learning_path.get("source") or "generated"

    lines: List[str] = []

    # Cover / Title
    lines.append(f"# {topic}")
    lines.append("")
    lines.append(f"- Created: {creation_date}")
    if last_modified_date and last_modified_date != "N/A":
        lines.append(f"- Last Modified: {last_modified_date}")
    if tags:
        lines.append(f"- Tags: {', '.join(tags)}")
    lines.append(f"- Source: {source}")
    if user_name:
        lines.append(f"- Exported for: {user_name}")
    lines.append("")

    # Table of Contents
    if modules:
        lines.append("## Table of Contents")
        for i, mod in enumerate(modules, start=1):
            lines.append(f"- {i}. {mod['title']}")
            if mod.get("submodules"):
                for j, sub in enumerate(mod["submodules"], start=1):
                    lines.append(f"  - {i}.{j} {sub['title']}")
        lines.append("")

    # Modules detail
    for i, mod in enumerate(modules, start=1):
        lines.append(f"## {mod['title']}")
        lines.append("")
        if mod.get("description"):
            lines.append(mod["description"].rstrip())
            lines.append("")
        # Module resources
        resources_md = _compose_resources_md(mod.get("resources", []))
        if resources_md:
            lines.append(resources_md.rstrip())
            lines.append("")
        # Submodules
        for sub in mod.get("submodules", []):
            lines.append(f"### {sub['title']}")
            lines.append("")
            if sub.get("description"):
                lines.append(sub["description"].rstrip())
                lines.append("")
            if sub.get("content"):
                lines.append(sub["content"].rstrip())
                lines.append("")
            s_resources_md = _compose_resources_md(sub.get("resources", []))
            if s_resources_md:
                lines.append(s_resources_md.rstrip())
                lines.append("")

    # Footer
    lines.append(f"\n---\nGenerated on {datetime.now().strftime('%B %d, %Y')}")

    return "\n".join(lines).strip() + "\n"


def create_md_filename(topic: str) -> str:
    sanitized = "".join(c for c in topic if c.isalnum() or c in (' ', '_', '-')).strip()
    sanitized = sanitized.replace(' ', '_') or "course"
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"course_{sanitized}_{timestamp}.md"


def generate_markdown(learning_path: Dict[str, Any], user_name: Optional[str] = None) -> str:
    """
    Generate a Markdown document for the given learning path.
    The input accepts the DB LearningPath.__dict__ shape or the response object
    with fields: topic, path_data, creation_date, last_modified_date, tags, source.
    """
    # Accept both full DB row dicts and response payloads
    path_data = learning_path.get("path_data") or {}
    modules = _extract_modules(path_data if isinstance(path_data, dict) else {})
    return _compose_markdown_document(learning_path, modules, user_name)
