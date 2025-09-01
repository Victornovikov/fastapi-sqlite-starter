from jinja2_fragments.fastapi import Jinja2Blocks
from pathlib import Path

# Configure templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Blocks(directory=str(templates_dir))
