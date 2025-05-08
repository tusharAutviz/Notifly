from pydantic import BaseModel
from typing import Optional

class TemplateCreate(BaseModel):
    name: str
    content: str
    type: str
    template_subject: Optional[str] = None
    