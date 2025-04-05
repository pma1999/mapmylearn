"""
PDF Generator utility for Learning Paths.
Converts learning path data structures into well-formatted PDF documents.
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import base64
import json
import logging
import markdown
import re
from markdown_it import MarkdownIt
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Configure logging
logger = logging.getLogger(__name__)

# Get the current directory to locate templates
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
CSS_DIR = os.path.join(TEMPLATE_DIR, "css")

# Create template directory if it doesn't exist
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(CSS_DIR, exist_ok=True)

# Create Jinja2 environment
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

# PDF base styling
BASE_CSS = """
@page {
    margin: 1cm;
    @top-center {
        content: "Learning Path";
        font-family: 'Helvetica', sans-serif;
        font-size: 9pt;
        color: #888;
    }
    @bottom-right {
        content: counter(page);
        font-family: 'Helvetica', sans-serif;
        font-size: 9pt;
    }
}

@page :first {
    margin: 0;
    @top-center { content: normal; }
    @bottom-right { content: normal; }
}

html {
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #333;
}

body {
    margin: 0;
    padding: 0;
}

.cover {
    height: 100vh;
    padding: 2cm;
    background-color: #f5f5f5;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.cover h1 {
    font-size: 28pt;
    color: #2c3e50;
    margin-bottom: 1cm;
    line-height: 1.2;
}

.cover .metadata {
    margin-top: 2cm;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-weight: bold;
    color: #2c3e50;
    margin-top: 1em;
    margin-bottom: 0.5em;
}

h1 { font-size: 20pt; page-break-before: always; }
h2 { font-size: 16pt; color: #3498db; border-bottom: 1px solid #3498db; padding-bottom: 0.2cm; }
h3 { font-size: 14pt; color: #2980b9; }
h4 { font-size: 12pt; color: #1abc9c; }

p {
    margin-bottom: 0.5em;
}

ul, ol {
    margin-top: 0.2em;
    margin-bottom: 0.5em;
}

li {
    margin-bottom: 0.2em;
}

.toc {
    margin: 1cm 0;
    page-break-after: always;
}

.toc h2 {
    font-size: 16pt;
    margin-bottom: 1cm;
}

.toc ul {
    list-style-type: none;
    padding-left: 0;
}

.toc ul ul {
    padding-left: 1cm;
}

.toc a {
    text-decoration: none;
    color: #333;
}

.toc .toc-item-level-1 {
    font-weight: bold;
    margin-top: 0.5cm;
}

.toc .toc-item-level-2 {
    margin-top: 0.2cm;
}

.toc .toc-page-num {
    float: right;
}

.toc .toc-line {
    border-bottom: 1px dotted #ccc;
}

.tag {
    display: inline-block;
    background-color: #e1f5fe;
    color: #0288d1;
    border-radius: 4px;
    padding: 0.1cm 0.3cm;
    margin-right: 0.2cm;
    margin-bottom: 0.2cm;
    font-size: 9pt;
}

.module {
    margin-bottom: 1cm;
    page-break-inside: avoid;
}

.submodule {
    margin-bottom: 0.8cm;
    page-break-inside: avoid;
}

.submodule .content {
    margin-top: 0.5cm;
    margin-bottom: 0.5cm;
    line-height: 1.6;
}

.submodule .content p {
    margin-bottom: 0.8em;
}

.submodule .content ul, .submodule .content ol {
    margin-left: 0.5cm;
    margin-bottom: 0.8em;
}

.submodule .content code {
    font-family: 'Courier New', monospace;
    background-color: #f5f5f5;
    padding: 0.1cm 0.2cm;
    border-radius: 3px;
    font-size: 90%;
}

.submodule .content pre {
    background-color: #f5f5f5;
    padding: 0.5cm;
    border-radius: 5px;
    overflow-x: auto;
    font-family: 'Courier New', monospace;
    font-size: 90%;
    line-height: 1.4;
    margin: 0.5cm 0;
}

.resources {
    background-color: #f9f9f9;
    border-left: 4px solid #3498db;
    padding: 0.5cm;
    margin-top: 0.5cm;
    margin-bottom: 0.5cm;
}

.resources h4 {
    margin-top: 0;
    color: #3498db;
}

.resources ul {
    margin-bottom: 0;
}

.page-break {
    page-break-after: always;
}

.footer {
    margin-top: 1cm;
    font-size: 9pt;
    color: #888;
    text-align: center;
}
"""

# Create the CSS file if it doesn't exist
css_file_path = os.path.join(CSS_DIR, "pdf_styles.css")
if not os.path.exists(css_file_path):
    with open(css_file_path, "w") as f:
        f.write(BASE_CSS)

# Create the HTML template for the PDF
TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ learning_path.topic }}</title>
    <style>
        {{ css }}
    </style>
</head>
<body>
    <!-- Cover Page -->
    <div class="cover">
        <h1>{{ learning_path.topic }}</h1>
        <div class="metadata">
            <p><strong>Creation Date:</strong> {{ creation_date }}</p>
            {% if last_modified_date %}
            <p><strong>Last Modified:</strong> {{ last_modified_date }}</p>
            {% endif %}
            {% if learning_path.tags %}
            <p><strong>Tags:</strong> 
                {% for tag in learning_path.tags %}
                <span class="tag">{{ tag }}</span>
                {% endfor %}
            </p>
            {% endif %}
            <p><strong>Source:</strong> {{ learning_path.source }}</p>
        </div>
    </div>

    <!-- Table of Contents -->
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
            {% for module in modules %}
            <li class="toc-item-level-1">
                <span class="toc-line">
                    <a href="#module-{{ loop.index }}">{{ module.title }}</a>
                    <span class="toc-page-num"><!-- Page number --></span>
                </span>
                {% if module.sub_modules %}
                {% set module_index = loop.index %}
                <ul>
                    {% for sub_module in module.sub_modules %}
                    <li class="toc-item-level-2">
                        <span class="toc-line">
                            <a href="#submodule-{{ module_index }}-{{ loop.index }}">{{ sub_module.title }}</a>
                            <span class="toc-page-num"><!-- Page number --></span>
                        </span>
                    </li>
                    {% endfor %}
                </ul>
                {% endif %}
            </li>
            {% endfor %}
        </ul>
    </div>

    <!-- Content -->
    {% for module in modules %}
    <div class="module">
        <h1 id="module-{{ loop.index }}">{{ module.title }}</h1>
        {{ module.description|safe }}
        
        {% if module.resources %}
        <div class="resources">
            <h4>Resources</h4>
            <ul>
                {% for resource in module.resources %}
                <li>{{ resource }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        {% if module.sub_modules %}
            {% set module_index = loop.index %}
            {% for sub_module in module.sub_modules %}
            <div class="submodule">
                <h3 id="submodule-{{ module_index }}-{{ loop.index }}">{{ sub_module.title }}</h3>
                {{ sub_module.description|safe }}
                
                {% if sub_module.content %}
                <div class="content">
                    {{ sub_module.content|safe }}
                </div>
                {% endif %}
                
                {% if sub_module.resources %}
                <div class="resources">
                    <h4>Resources</h4>
                    <ul>
                        {% for resource in sub_module.resources %}
                        <li>{{ resource }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        {% endif %}
    </div>
    {% endfor %}

    <!-- Footer with generation info -->
    <div class="footer">
        <p>Generated on {{ generation_date }}</p>
    </div>
</body>
</html>
"""

# Create the template file if it doesn't exist
template_file_path = os.path.join(TEMPLATE_DIR, "learning_path_template.html")
if not os.path.exists(template_file_path):
    with open(template_file_path, "w") as f:
        f.write(TEMPLATE_HTML)

def _format_date(date_obj):
    """Format a datetime object into a readable string."""
    if not date_obj:
        return None
    return date_obj.strftime("%B %d, %Y")

def _process_markdown(text):
    """Process markdown text to HTML."""
    if not text:
        return ""
    
    # Process any markdown headers (# headers) that might not be properly formatted
    # Add a space after the # if there isn't one
    text = re.sub(r'(^|\n)(\#{1,6})([^\s#])', r'\1\2 \3', text)
    
    # First try with markdown-it-py for better rendering
    try:
        md = MarkdownIt("commonmark", {"html": True})
        return md.render(text)
    except Exception as e:
        logger.warning(f"Error with markdown-it-py: {str(e)}. Falling back to python-markdown.")
        # Fall back to python-markdown with extensions
        return markdown.markdown(text, extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'nl2br',
            'sane_lists'
        ])

def _extract_modules(path_data):
    """Extract modules from learning path data."""
    modules = []
    
    # Handle different potential structures
    if "modules" in path_data:
        raw_modules = path_data["modules"]
    elif "content" in path_data and "modules" in path_data["content"]:
        raw_modules = path_data["content"]["modules"]
    else:
        # Try to find modules in the structure
        raw_modules = []
        for key, value in path_data.items():
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                raw_modules = value
                break
    
    # Process each module
    for i, module in enumerate(raw_modules):
        module_title = module.get("title", f"Module {i+1}")
        
        # Process module description with markdown
        module_description = module.get("description", "")
        processed_description = _process_markdown(module_description)
        
        # Extract resources
        resources = module.get("resources", [])
        
        # Process submodules
        sub_modules = []
        
        # Check various submodule keys
        submodules_data = None
        for key in ["sub_modules", "subModules", "subjects", "topics", "subtopics", "lessons", "submodules"]:
            if key in module and isinstance(module[key], list):
                submodules_data = module[key]
                break
        
        if submodules_data:
            for j, sub in enumerate(submodules_data):
                sub_title = sub.get("title", f"Subtopic {j+1}")
                
                # Process submodule description with markdown
                sub_description = sub.get("description", "")
                processed_sub_description = _process_markdown(sub_description)
                
                # Extract and process submodule content (main body text)
                sub_content = sub.get("content", "")
                processed_sub_content = _process_markdown(sub_content)
                
                # Extract resources
                sub_resources = sub.get("resources", [])
                
                sub_modules.append({
                    "title": sub_title,
                    "description": processed_sub_description,
                    "content": processed_sub_content,
                    "resources": sub_resources
                })
        
        modules.append({
            "title": module_title,
            "description": processed_description,
            "resources": resources,
            "sub_modules": sub_modules
        })
    
    return modules

def generate_pdf(learning_path: Dict[str, Any], user_name: Optional[str] = None) -> str:
    """
    Generate a PDF from a learning path.
    
    Args:
        learning_path: The learning path data
        user_name: Optional username to include in the PDF
        
    Returns:
        Path to the generated PDF file
    """
    try:
        logger.info(f"Generating PDF for learning path: {learning_path.get('topic', 'Untitled')}")
        
        # Extract important dates
        creation_date = _format_date(learning_path.get("creation_date", datetime.now()))
        last_modified_date = _format_date(learning_path.get("last_modified_date"))
        generation_date = _format_date(datetime.now())
        
        # Extract and process modules
        modules = _extract_modules(learning_path.get("path_data", {}))
        
        # Read CSS
        with open(css_file_path, "r") as f:
            css_content = f.read()
        
        # Prepare template data
        template_data = {
            "learning_path": learning_path,
            "creation_date": creation_date,
            "last_modified_date": last_modified_date,
            "generation_date": generation_date,
            "modules": modules,
            "css": css_content,
            "user_name": user_name
        }
        
        # Load template
        template = env.get_template("learning_path_template.html")
        html_content = template.render(**template_data)
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            # Configure fonts
            font_config = FontConfiguration()
            
            # Create HTML object
            html = HTML(string=html_content)
            
            # Generate PDF
            html.write_pdf(
                tmp.name,
                font_config=font_config
            )
            
            logger.info(f"PDF generated successfully: {tmp.name}")
            return tmp.name
    
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise

def create_filename(topic):
    """Create a sanitized filename from the topic."""
    # Remove characters that are problematic in filenames
    sanitized = "".join(c for c in topic if c.isalnum() or c in (' ', '_', '-')).strip()
    sanitized = sanitized.replace(' ', '_')
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"learning_path_{sanitized}_{timestamp}.pdf" 