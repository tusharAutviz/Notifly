from fastapi import status, APIRouter, Depends, UploadFile, File, Form
from app.db.models.user import Subject, RefreshToken
from app.utils.validators import create_response, is_valid_email, is_valid_phone
from app.db.schemas.user import UpdateUserProfile, UpdateSubject
from app.dependencies import get_current_user, get_db
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from typing import Optional
import logging
import shutil
import os

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads/profile_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- GET PARTICULAR USER ---
@router.get("/", summary="get particular user")
async def get_user(db = Depends(get_db), current_user: get_current_user = Depends()):
    try:    
        user = jsonable_encoder(current_user)
        return create_response(status.HTTP_200_OK, "Getting user info successfully.", data={"result":user})
    
    except Exception as err:
        logging.log(f"Error in getting user details: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()  # read file content (optional)
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content)
    }

# --- UPDATE USER INFO ---
@router.patch("/", summary="Update user profile info")
async def update_user_info(
    name: Optional[str] = Form(None),
    mobile_no: Optional[str] = Form(None),
    about: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user: get_current_user = Depends()
):
    try:
        # Dynamically update fields
        if name is not None:
            current_user.name = name
        if mobile_no is not None:
            current_user.mobile_no = mobile_no
        if about is not None:
            current_user.about = about

        # Handle optional file upload
        if file:
            file_ext = file.filename.split(".")[-1]
            unique_name = f"{current_user.email}.{file_ext}"
            file_path = UPLOAD_DIR / unique_name

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            current_user.profile_img_url = str(file_path)

        db.commit()
        return create_response(status.HTTP_200_OK, "User info updated successfully.")
    except Exception as err:
        logger.error(f"Error in updating user info: {str(err)}")
        return create_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err)
        )

# --- DELETE USER PROFILE ---    
@router.delete("/delete/", summary="Delete a specific user")
async def delete_user(id: int, db=Depends(get_db), current_user: get_current_user = Depends()):
    try:
        db.query(RefreshToken).filter(RefreshToken.user_email == current_user.email).update({"blacklisted":True})
        db.delete(current_user)
        db.commit()
        return create_response(status.HTTP_200_OK, "User deleted successfully.")
    
    except Exception as err:
        logging.log(f"Error in delete user: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))


# --- CREATE SUBJECTS INFO ---
@router.post("/subjects", summary="create subjects for user")
async def create_subjects(request: UpdateSubject, db = Depends(get_db), current_user: get_current_user = Depends()):
    try:
        existing_subjects = []
        new_subjects = []
        for subject in request.subjects:
            existing_subject = db.query(Subject).filter(Subject.name == subject, Subject.user_id == current_user.id).first()
            if existing_subject:
                existing_subjects.append(subject)
                continue
            
            new_subject = Subject(
                name=subject,
                user_id=current_user.id
            )
            new_subjects.append(new_subject)
        
        db.commit()
        data = {
            "new_subjects": new_subjects,
            "existing_subjects": existing_subjects
        }
        return create_response(status.HTTP_201_OK, "Subjects created successfully.", data=data)

    except Exception as err:
        logging.log(f"Error in creating subjects: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
    

# --- GET ALL SUBJECTS ---
@router.get("/subjects", summary="get all subjects")
async def get_all_subjects(db = Depends(get_db), current_user: get_current_user = Depends()):
    try:
        subjects = db.query(Subject).filter(Subject.user_id == current_user.id).all()
        if not subjects:
            return create_response(status.HTTP_200_OK, "No subjects found.")
        
        json_result = jsonable_encoder(subjects)
        return create_response(status.HTTP_200_OK, "Subjects retrieved successfully.", data={"result": json_result})

    except Exception as err:
        logging.log(f"Error in getting subjects: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
    

# --- DELETE PARTICULAR SUBJECT ---
@router.delete("/subjects", summary="delete particular subject")
async def delete_subject(subject_id: int, db = Depends(get_db), current_user: get_current_user = Depends()):
    try:
        subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
        if not subject:
            return create_response(status.HTTP_200_OK, "Subject not found.")
        
        db.delete(subject)
        db.commit()
        return create_response(status.HTTP_200_OK, "Subject deleted successfully.")
    
    except Exception as err:
        logging.log(f"Error in delete subject: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
