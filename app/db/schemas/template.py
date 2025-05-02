from pydantic import BaseModel

class TemplateCreate(BaseModel):
    name: str
    content: str
    type: str
    template_subject: str
    