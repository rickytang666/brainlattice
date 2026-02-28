import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

class PromptService:
    """
    manages and renders jinja2 prompt templates for llms
    """
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            # default to /backend/prompts
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            templates_dir = os.path.join(base_dir, "prompts")
            
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render(self, template_name: str, **kwargs) -> str:
        """renders a prompt template with provided variables"""
        template = self.env.get_template(template_name)
        return template.render(**kwargs)

# singleton instance
_prompt_service = None

def get_prompt_service() -> PromptService:
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service
