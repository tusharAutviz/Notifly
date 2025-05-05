from fastapi import APIRouter, Depends, status, Request, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder 
from app.db.models.template import Template
from app.db.schemas.template import TemplateCreate
from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.utils.validators import create_response
from typing import Optional
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

# --- CREATE TEMPLATE ENDPOINT ---
@router.post("/create", summary="Create a new template")
def create_template(request: TemplateCreate, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:

        new_template = Template(
            name=request.name,
            content=request.content,
            type=request.type.lower(),
            user_id=current_user.id,
            subject=request.template_subject
        )
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        return create_response(status.HTTP_201_CREATED, "Template created successfully.", data={"template_id": new_template.id})  

    except Exception as err:
        logger.error(f"Error in template creation: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))


# --- GET SPECIFIC TEMPLATE ENDPOINT ---
@router.get("/get-specific", summary="Get a specific template")
def get_template(template_id: int, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        template = db.query(Template).filter(Template.id == template_id, Template.user_id == current_user.id).first()
        if not template:
            return create_response(status.HTTP_404_NOT_FOUND, "No Template Found")
        
        template_json = jsonable_encoder(template)
        return create_response(status.HTTP_200_OK, "Template fetched successfully", data={"result": template_json})
                                                                                                                                                                            
    except Exception as err:
        logger.error(f"Error in get specific template: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))


# --- UPDATE TEMPLATE ENDPOINT ---
@router.put("/update", summary="Update a specific template")
def update_template(template_id: int, request: TemplateCreate, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        template = db.query(Template).filter(Template.id == template_id, Template.user_id == current_user.id).first()
        if not template:
            return create_response(status.HTTP_404_NOT_FOUND, "No Template Found")
        
        template.name = request.name
        template.content = request.content
        template.type = request.type.lower()
        template.subject = request.template_subject
        template.user_id = current_user.id
        db.commit()

        return create_response(status.HTTP_200_OK, "Template updated successfully.")

    except Exception as err:
        logger.error(f"Error in update template: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
    

# --- DELETE TEMPLATE ENDPOINT ---
@router.delete("/delete", summary="Delete a specific template")
def delete_template(template_id: int, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        template = db.query(Template).filter(Template.id == template_id, Template.user_id == current_user.id).first()
        if not template:
            return create_response(status.HTTP_404_NOT_FOUND, "No Template Found")
        
        db.delete(template)
        db.commit()

        return create_response(status.HTTP_200_OK, "Template deleted successfully.")
    
    except Exception as err:
        logger.error(f"Error in delete template: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))


# --- GET ALL TEMPLATES ENDPOINT ---
@router.get("/get-all", summary="Get all the templates")
async def get_all_templates(request: Request, 
    db=Depends(get_db), 
    current_user: User = Depends(get_current_user),
    name: Optional[str] = Query(None, description="Filter by template name"),
    limit: int = Query(20, gt=0, le=100, description="Number of templates to return per page (max 100)"),
    offset: int = Query(0, ge=0, description="Number of templates to skip")):
    try:
        templates_query = db.query(Template).filter(Template.user_id == current_user.id)
        if name:
            templates_query = templates_query.filter(Template.name.ilike(f"%{name}%"))

        total_template = templates_query.with_entities(Template.id).count()
        templates = templates_query.offset(offset).limit(limit).all()
        if not templates:
            return create_response(status.HTTP_404_NOT_FOUND, "No Template Found")
        
        template_json = jsonable_encoder(templates)
        base_url = str(request.url).split('?')[0]
        query_params = dict(request.query_params)

        # Calculate next offset
        next_offset = offset + limit
        prev_offset = max(offset - limit, 0)

        next_url = None
        if next_offset < total_template:
            query_params["offset"] = next_offset
            query_params["limit"] = limit
            next_url = f"{base_url}?{query_params}"

        previous_url = None
        if offset > 0:
            query_params["offset"] = prev_offset
            query_params["limit"] = limit
            previous_url = f"{base_url}?{query_params}"

        data = {
            "result": template_json,
            "pagination": {
                "total_template": total_template,
                "limit": limit,
                "offset": offset,
                "total_pages": (total_template + limit - 1) // limit,
                "next": next_url,
                "previous": previous_url
            }
        }
        return create_response(status.HTTP_200_OK, "Template fetched succesfully", data=data)
       
    except Exception as err:
        logger.error(f"Error in get all template: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))