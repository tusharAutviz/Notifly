from pydantic import BaseModel, EmailStr, model_validator, ValidationError
from typing import List, Dict, Any


class RecipientData(BaseModel):
    email: EmailStr
    variables: Dict[str, Any]

    @model_validator(mode="after")
    def check_parent_name_in_variables(self):
        if "parent_name" not in self.variables or not self.variables["parent_name"]:
            raise ValueError("Missing required variable: 'parent_name'")
        return self

class RecipientGroup(BaseModel):
    template_id: int
    subject: str
    recipient_data: List[RecipientData]


class EmailRequest(BaseModel):
    groups: List[RecipientGroup]