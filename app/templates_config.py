from jinja2_fragments.fastapi import Jinja2Blocks
from pathlib import Path
from datetime import datetime

# Configure templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Blocks(directory=str(templates_dir))

# Add global template functions
def get_current_year():
    """Return the current year for use in templates"""
    return datetime.now().year

# Register global functions
templates.env.globals['now'] = lambda format_str: datetime.now().strftime(format_str)
templates.env.globals['current_year'] = get_current_year  # Function, not result
