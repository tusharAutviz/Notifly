from fastapi import APIRouter, Depends, status, Request, Query
from fastapi.responses import JSONResponse
from app.db.models.school import School
from app.db.schemas.school import CreateSchool,PartialSchoolUpdate
from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from fastapi.encoders import jsonable_encoder
from sqlalchemy import asc
from typing import Optional
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


# --- CREATE SCHOOL ENDPOINT ---
@router.post("/create/", summary="Create a new school")
async def create_school(request: CreateSchool, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if current_user.is_admin:
            existing_school = db.query(School).filter(School.school_name == request.school_name.title()).first()
            if existing_school:
                return JSONResponse(
                    content={
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "School already exists."
                    }, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
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
            return JSONResponse(
                content={
                    "status": status.HTTP_201_CREATED,
                    "message": "School created successfully.",
                    "data": {
                        "school_id": new_school.id
                    } 
                }, 
                status_code=status.HTTP_201_CREATED
            )

        return JSONResponse(
            content={
                "status": status.HTTP_401_UNAUTHORIZED,
                "message": "You are not authorized."
            }, 
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    except Exception as err:
        logger.error(f"Error in create school: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

# --- UPDATE SCHOOL ENDPOINT ---
@router.patch("/update/", summary="Update a specific school")
async def update_school(school_id: int, request: PartialSchoolUpdate, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if current_user.is_admin:
            school = db.query(School).filter(School.id == school_id).first()
            if not school:
                return JSONResponse(
                    content={
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "School not found."
                    }, 
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            update_data = request.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if value not in [None, ""]:
                    setattr(school, field, value.title() if field == "school_name" and value else value)

            db.commit()
            return JSONResponse(
                content={
                    "status": status.HTTP_200_OK,
                    "message": "School updated successfully."
                }, 
                status_code=status.HTTP_200_OK
            )

        return JSONResponse(
            content={
                "status": status.HTTP_401_UNAUTHORIZED,
                "message": "You are not authorized."
            }, 
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    except Exception as err:
        logger.error(f"Error in update school: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- GET ALL SCHOOLS ENDPOINT ---
@router.get("/get-all/", summary="Get all schools")
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
            return JSONResponse(
                content={
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "No schools found."
                }, 
                status_code=status.HTTP_404_NOT_FOUND
            )
        
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

        return JSONResponse(
            content={
                "status": status.HTTP_200_OK,
                "message": "Schools retrieved successfully.",
                "data": {
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
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as err:
        logger.error(f"Error in get all schools: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- DELETE SCHOOL ENDPOINT ---
@router.delete("/delete/", summary="Delete a specific school")
async def delete_school(school_id: int, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if current_user.is_admin:
            school = db.query(School).filter(School.id == school_id).first()
            if not school:
                return JSONResponse(
                    content={
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "School not found."
                    }, 
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            db.delete(school)
            db.commit()
            return JSONResponse(
                content={
                    "status": status.HTTP_200_OK,
                    "message": "School deleted successfully."
                }, 
                status_code=200
            )
        
        return JSONResponse(
            content={
                "status": status.HTTP_401_UNAUTHORIZED,
                "message": "You are not authorized."
            }, 
            status_code=status.HTTP_401_UNAUTHORIZED
        )   


    except Exception as err:
        logger.error(f"Error in delete school: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )