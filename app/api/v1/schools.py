from fastapi import APIRouter, Depends, status, Request, Query
from fastapi.responses import JSONResponse
from app.db.models.school import School
from app.db.schemas.school import CreateSchool,PartialSchoolUpdate
from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.utils.validators import create_response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import asc
from typing import Optional
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


# --- CREATE SCHOOL ENDPOINT ---
@router.post("/create", summary="Create a new school")
async def create_school(request: CreateSchool, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if current_user.is_admin:
            existing_school = db.query(School).filter(School.school_name == request.school_name.title()).first()
            if existing_school:
                return create_response(status.HTTP_400_BAD_REQUEST, "School already exists.")
            
            new_school = School(
                school_name=request.school_name.title(),
                address=request.address,
                city=request.city,
                state=request.state,
                country=request.country,
                pincode=request.pincode,
                phone_no=request.phone_no,
                email=request.email,
                website=request.website,
                is_active=request.is_active
            )
            db.add(new_school)
            db.commit()
            db.refresh(new_school)
            return create_response(status.HTTP_201_CREATED, "School created successfully.", data={"school_id": new_school.id})

        return create_response(status.HTTP_401_UNAUTHORIZED, "You are not authorized.")

    except Exception as err:
        logger.error(f"Error in create school: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
    

# --- UPDATE SCHOOL ENDPOINT ---
@router.patch("/update", summary="Update a specific school")
async def update_school(school_id: int, request: PartialSchoolUpdate, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if current_user.is_admin:
            school = db.query(School).filter(School.id == school_id).first()
            if not school:
                return create_response(status.HTTP_404_NOT_FOUND, "School not found.")
            
            update_data = request.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if value not in [None, ""]:
                    setattr(school, field, value.title() if field == "school_name" and value else value)

            db.commit()
            return create_response(status.HTTP_200_OK, "School updated successfully.")

        return create_response(status.HTTP_401_UNAUTHORIZED, "You are not authorized.")

    except Exception as err:
        logger.error(f"Error in update school: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))


# --- GET ALL SCHOOLS ENDPOINT ---
@router.get("/get-all", summary="Get all schools")
async def get_all_schools(request: Request, 
    db=Depends(get_db),
    name: Optional[str] = Query(None, description="Filter schools by name"), 
    limit: int = Query(20, gt=0, le=100, description="Number of schools to return per page (max 100)"),
    offset: int = Query(0, ge=0, description="Number of schools to skip")):
    try:
        schools_query = db.query(School)
        if name:
            schools_query = schools_query.filter(School.name.ilike(f"%{name}%"))

        schools_query = schools_query.order_by(asc(School.is_active))
        schools = schools_query.offset(offset).limit(limit).all()
        
        if not schools:
            return create_response(status.HTTP_404_NOT_FOUND, "No schools found.")
        
        schools_json = jsonable_encoder(schools)
        total_schools = schools_query.with_entities(School.id).count()
        
        base_url = str(request.url).split('?')[0]
        query_params = dict(request.query_params)

        # Calculate next offset
        next_offset = offset + limit
        prev_offset = max(offset - limit, 0)

        next_url = None
        if next_offset < total_schools:
            query_params["offset"] = next_offset
            query_params["limit"] = limit
            next_url = f"{base_url}?{query_params}"

        previous_url = None
        if offset > 0:
            query_params["offset"] = prev_offset
            query_params["limit"] = limit
            previous_url = f"{base_url}?{query_params}"

        data = {
            "result": schools_json,
            "pagination": {
                "total_schools": total_schools,
                "limit": limit,
                "offset": offset,
                "total_pages": (total_schools + limit - 1) // limit,
                "next": next_url,
                "previous": previous_url
            }
        }

        return create_response(status.HTTP_200_OK, "Schools retrieved successfully.", data=data)

    except Exception as err:
        logger.error(f"Error in get all schools: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))


# --- DELETE SCHOOL ENDPOINT ---
@router.delete("/delete", summary="Delete a specific school")
async def delete_school(school_id: int, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if current_user.is_admin:
            school = db.query(School).filter(School.id == school_id).first()
            if not school:
                return create_response(status.HTTP_404_NOT_FOUND, "School not found.")
            
            db.delete(school)
            db.commit()
            return create_response(status.HTTP_200_OK, "School deleted successfully.")
        
        return create_response(status.HTTP_401_UNAUTHORIZED, "You are not authorized.")


    except Exception as err:
        logger.error(f"Error in delete school: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))