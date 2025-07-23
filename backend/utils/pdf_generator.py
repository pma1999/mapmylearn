"""
PDF Generator utility for Courses.
Converts course data structures into well-formatted PDF documents.
"""

import os
import tempfile
import html
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import logging
import re
import markdown
from markdown_it import MarkdownIt
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Configure logging
logger = logging.getLogger(__name__)

class TemplateManager:
    """Manages templates for PDF generation."""
    
    # Base template directory
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
    CSS_DIR = os.path.join(TEMPLATE_DIR, "css")
    
    # Default template and CSS filenames
    TEMPLATE_FILENAME = "learning_path_template.html"
    CSS_FILENAME = "pdf_styles.css"
    
    # Base CSS content
    BASE_CSS = """
@page {
   margin: 1cm;
   @top-center {
       content: "Course";
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

/* Module intro styling */
.module-intro {
   min-height: 70vh;
   padding: 1cm 0;
   display: flex;
   flex-direction: column;
}

.module-intro h1 {
   margin-top: 0;
}

.module-page-break {
   page-break-after: always;
}

.module-toc {
   margin-top: auto;
   border-top: 1px solid #ddd;
   padding-top: 1cm;
}

.module-toc h3 {
   margin-top: 0;
   color: #3498db;
}

.module-toc ul {
   list-style-type: none;
   padding-left: 0;
}

.module-toc li {
   margin-bottom: 0.5cm;
   font-size: 12pt;
}

.module-toc a {
   text-decoration: none;
   color: #2c3e50;
}

.submodule {
   margin-bottom: 0.8cm;
   page-break-inside: avoid;
   page-break-before: auto;
}

.submodule h3 {
   page-break-after: avoid;
}

.submodule .content {
   margin-top: 0.5cm;
   margin-bottom: 0.5cm;
   line-height: 1.6;
   page-break-before: auto;
   page-break-after: auto;
   page-break-inside: avoid;
}

.submodule .resources {
   page-break-before: auto;
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
   page-break-before: auto;
   page-break-inside: avoid;
}

.resources h4 {
   margin-top: 0;
   color: #3498db;
}

.resources ul {
   margin-bottom: 0;
   padding-left: 0;
   list-style-type: none;
}

.resource-item {
   margin-bottom: 0.5cm;
   padding-bottom: 0.3cm;
   border-bottom: 1px solid #eee;
}

.resource-item:last-child {
   margin-bottom: 0;
   padding-bottom: 0;
   border-bottom: none;
}

.resource-title {
   font-weight: bold;
   font-size: 11pt;
   margin-bottom: 0.2cm;
}

.resource-description {
   font-size: 10pt;
   margin-bottom: 0.2cm;
   color: #666;
}

.resource-url {
   font-size: 9pt;
   margin-bottom: 0.2cm;
   color: #3498db;
   word-break: break-all;
}

.resource-url a {
   color: #3498db;
   text-decoration: underline;
}

.resource-type {
   font-size: 9pt;
   color: #888;
   font-style: italic;
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
    
    # Base HTML template
    BASE_HTML = """
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
               <li>
                   <div class="resource-item">
                       <div class="resource-title">{{ resource.title }}</div>
                       {% if resource.description %}
                       <div class="resource-description">{{ resource.description }}</div>
                       {% endif %}
                       {% if resource.url %}
                       <div class="resource-url"><a href="{{ resource.url }}">{{ resource.url }}</a></div>
                       {% endif %}
                       {% if resource.type %}
                       <div class="resource-type">Type: {{ resource.type }}</div>
                       {% endif %}
                   </div>
               </li>
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
                       <li>
                           <div class="resource-item">
                               <div class="resource-title">{{ resource.title }}</div>
                               {% if resource.description %}
                               <div class="resource-description">{{ resource.description }}</div>
                               {% endif %}
                               {% if resource.url %}
                               <div class="resource-url"><a href="{{ resource.url }}">{{ resource.url }}</a></div>
                               {% endif %}
                               {% if resource.type %}
                               <div class="resource-type">Type: {{ resource.type }}</div>
                               {% endif %}
                           </div>
                       </li>
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
    
    def __init__(self):
        """Initialize the template manager and ensure template files exist."""
        self._ensure_directories_exist()
        self._ensure_template_files_exist()
        self._initialize_jinja_env()
    
    def _ensure_directories_exist(self):
        """Ensure template directories exist."""
        os.makedirs(self.TEMPLATE_DIR, exist_ok=True)
        os.makedirs(self.CSS_DIR, exist_ok=True)
    
    def _ensure_template_files_exist(self):
        """Ensure template and CSS files exist."""
        # Create CSS file if it doesn't exist
        css_file_path = os.path.join(self.CSS_DIR, self.CSS_FILENAME)
        if not os.path.exists(css_file_path):
            with open(css_file_path, "w") as f:
                f.write(self.BASE_CSS)
        
        # Create HTML template if it doesn't exist
        template_file_path = os.path.join(self.TEMPLATE_DIR, self.TEMPLATE_FILENAME)
        if not os.path.exists(template_file_path):
            with open(template_file_path, "w") as f:
                f.write(self.BASE_HTML)
    
    def _initialize_jinja_env(self):
        """Initialize Jinja2 environment."""
        self.env = Environment(
            loader=FileSystemLoader(self.TEMPLATE_DIR),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def get_css_content(self) -> str:
        """Get CSS content from file."""
        try:
            css_file_path = os.path.join(self.CSS_DIR, self.CSS_FILENAME)
            with open(css_file_path, "r") as f:
                css_content = f.read()
            
            # Decode HTML entities
            css_content = html.unescape(css_content)
            return css_content
        except Exception as css_error:
            logger.error(f"Error loading CSS: {str(css_error)}")
            # Return minimal fallback CSS
            return """
            body { font-family: sans-serif; margin: 2cm; line-height: 1.5; }
            h1 { font-size: 18pt; margin-top: 1cm; }
            h2 { font-size: 14pt; }
            """
    
    def render_template(self, template_data: Dict[str, Any]) -> str:
        """Render HTML template with provided data."""
        try:
            template = self.env.get_template(self.TEMPLATE_FILENAME)
            return template.render(**template_data)
        except Exception as template_error:
            logger.error(f"Error rendering template: {str(template_error)}")
            raise


class MarkdownProcessor:
    """Processes markdown content for PDF rendering."""
    
    @staticmethod
    def preprocess_content(text: str) -> str:
        """
        Prepare markdown content for consistent rendering between UI and PDF.
        
        Args:
            text: The markdown text to preprocess
            
        Returns:
            Preprocessed markdown text
        """
        if not text:
            return text
        
        # Remove ```markdown only at the beginning of content
        if text.startswith("```markdown\n"):
            text = text.replace("```markdown\n", "", 1)
        
        # Ensure proper header formatting
        text = re.sub(r'(^|\n)(\#{1,6})([^\s#])', r'\1\2 \3', text)
        
        return text
    
    @staticmethod
    def convert_to_html(text: str) -> str:
        """
        Convert markdown text to HTML.
        
        Args:
            text: The markdown text to convert
            
        Returns:
            HTML representation of the markdown
        """
        if not text:
            return ""
        
        try:
            # Preprocess text for consistent handling
            text = MarkdownProcessor.preprocess_content(text)
            
            # Try with markdown-it-py for better rendering
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
        except Exception as e:
            logger.error(f"Error processing markdown: {str(e)}")
            # Return plain text as fallback
            return f"<p>{text}</p>"


class LearningPathExtractor:
    """Extracts and processes course content."""
    
    @staticmethod
    def format_date(date_obj: Union[str, datetime, None]) -> str:
        """
        Format a date object as a readable string.
        
        Args:
            date_obj: The date to format (string, datetime or None)
            
        Returns:
            Formatted date string
        """
        if not date_obj:
            return "N/A"
        
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.fromisoformat(date_obj.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                try:
                    date_obj = datetime.strptime(date_obj, "%Y-%m-%dT%H:%M:%S.%fZ")
                except (ValueError, TypeError):
                    return date_obj
        
        if isinstance(date_obj, datetime):
            return date_obj.strftime("%B %d, %Y")
        
        return str(date_obj)
    
    @staticmethod
    def extract_modules(path_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and process modules from course data.
        
        Args:
            path_data: The course data structure
            
        Returns:
            List of processed modules with their content
        """
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
            
            # Preprocess and process module description
            module_description = MarkdownProcessor.preprocess_content(module.get("description", ""))
            processed_description = MarkdownProcessor.convert_to_html(module_description)
            
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
                    
                    # Preprocess and process submodule description and content
                    sub_description = MarkdownProcessor.preprocess_content(sub.get("description", ""))
                    sub_content = MarkdownProcessor.preprocess_content(sub.get("content", ""))
                    
                    processed_sub_description = MarkdownProcessor.convert_to_html(sub_description)
                    processed_sub_content = MarkdownProcessor.convert_to_html(sub_content)
                    
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


class PDFGenerator:
    """Main class for generating PDFs from courses."""
    
    def __init__(self):
        """Initialize the PDF Generator with template manager."""
        self.template_manager = TemplateManager()
    
    def generate(self, learning_path: Dict[str, Any], user_name: Optional[str] = None) -> str:
        """
        Generate a PDF from a course.
        
        Args:
            learning_path: The course data
            user_name: Optional username to include in the PDF
            
        Returns:
            Path to the generated PDF file
        """
        try:
            logger.info(f"Generating PDF for course: {learning_path.get('topic', 'Untitled')}")
            
            # Extract important dates
            creation_date = LearningPathExtractor.format_date(learning_path.get("creation_date", datetime.now()))
            last_modified_date = LearningPathExtractor.format_date(learning_path.get("last_modified_date"))
            generation_date = LearningPathExtractor.format_date(datetime.now())
            
            # Extract and process modules
            modules = LearningPathExtractor.extract_modules(learning_path.get("path_data", {}))
            
            # Get CSS content
            css_content = self.template_manager.get_css_content()
            
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
            
            # Render HTML content
            html_content = self.template_manager.render_template(template_data)
            
            # Create temporary file for PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                try:
                    # Configure fonts
                    font_config = FontConfiguration()
                    
                    # Create HTML object and generate PDF
                    html_obj = HTML(string=html_content)
                    html_obj.write_pdf(
                        tmp.name,
                        font_config=font_config
                    )
                    
                    logger.info(f"PDF generated successfully: {tmp.name}")
                    return tmp.name
                except Exception as pdf_error:
                    logger.error(f"Error generating PDF with WeasyPrint: {str(pdf_error)}")
                    if hasattr(pdf_error, 'args') and pdf_error.args:
                        logger.error(f"Error details: {pdf_error.args}")
                    raise
        
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise


def create_filename(topic: str) -> str:
    """
    Create a sanitized filename from the topic.
    
    Args:
        topic: The course topic
        
    Returns:
        Sanitized filename with timestamp
    """
    # Remove characters that are problematic in filenames
    sanitized = "".join(c for c in topic if c.isalnum() or c in (' ', '_', '-')).strip()
    sanitized = sanitized.replace(' ', '_')
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"learning_path_{sanitized}_{timestamp}.pdf"


# Main function to generate PDF
def generate_pdf(learning_path: Dict[str, Any], user_name: Optional[str] = None) -> str:
    """
    Generate a PDF from a course.
    
    Args:
        learning_path: The course data
        user_name: Optional username to include in the PDF
        
    Returns:
        Path to the generated PDF file
    """
    pdf_generator = PDFGenerator()
    return pdf_generator.generate(learning_path, user_name) 