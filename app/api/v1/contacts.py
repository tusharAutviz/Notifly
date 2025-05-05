from fastapi import APIRouter, Depends, status, UploadFile, File, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
from app.db.models.contact import Contact
from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.utils.file_handler import read_spreadsheet, validate_contacts
from app.utils.validators import create_response
from typing import List, Dict
from app.db.schemas.contact import Contacts
from fastapi.encoders import jsonable_encoder
from typing import Optional
from sqlalchemy import or_
import logging
import io
import xlsxwriter

router = APIRouter()

logger = logging.getLogger(__name__)

# --- UPLOAD CONTACTS ENDPOINT ---
@router.post("/upload", summary="Upload contacts from a file")
async def upload_contacts(files: List[UploadFile] = File(...), db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        raw_data = await read_spreadsheet(files)
        valid_contacts = validate_contacts(raw_data)
        if not valid_contacts:
            return create_response(status.HTTP_400_BAD_REQUEST, "No valid contacts found in the file.")
        inserted, updated = 0, 0

        # Step 2: Upsert to DB
        for contact in valid_contacts:
            existing = db.query(Contact).filter(Contact.student_name == contact["name"], Contact.user_id == current_user.id).first()
            if existing:
                # Update existing record
                existing.student_name = contact["name"]
                existing.parent_email = contact["email"]
                existing.parent_phone_no = contact["phone"]
                existing.parent_name = contact["parent_name"]
                existing.mode = contact["mode"]
                existing.user_id = current_user.id
                updated += 1
            else:
                # Insert new record
                db_contact = Contact(
                    student_name=contact["name"],
                    parent_email=contact["email"],
                    parent_phone_no=contact["phone"],
                    parent_name=contact["parent_name"],
                    mode=contact["mode"],
                    user_id=current_user.id
                )
                db.add(db_contact)  
                inserted += 1
        
        db.commit()
        return create_response(status.HTTP_200_OK, "Contacts uploaded successfully.", data={"inserted": inserted, "updated": updated})
    

    except Exception as err:
        logger.error(f"Error in upload contacts: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
    

# --- CREATE CONTACT ENDPOINT ---
@router.post("/create", summary="Create a new contact")
async def create_contact(request: Contacts, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        existing_contact = db.query(Contact).filter(Contact.student_name == request.student_name, Contact.user_id == current_user.id).first()
        if existing_contact:
            return create_response(status.HTTP_400_BAD_REQUEST, "Contact already exists.")
        
        new_contact = Contact(
            student_name=request.student_name,
            parent_email=request.parent_email,
            parent_phone_no=request.parent_phone_no,
            parent_name=request.parent_name,
            mode=request.mode,
            user_id=current_user.id
        )
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        return create_response(status.HTTP_201_CREATED, "Contact created successfully.", data={"contact_id": new_contact.id})

    except Exception as err:
        logger.error(f"Error in create contact: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
    

# --- UPDATE CONTACT ENDPOINT ---
@router.put("/update", summary="Update a contact")
async def update_contact(contact_id: int, request: Contacts, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        existing_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
        if not existing_contact:
            return create_response(status.HTTP_404_NOT_FOUND, "Contact not found.")
        
        existing_contact.student_name = request.student_name
        existing_contact.parent_email = request.parent_email
        existing_contact.parent_phone_no = request.parent_phone_no
        existing_contact.parent_name = request.parent_name
        existing_contact.mode = request.mode
        existing_contact.user_id = current_user.id
        db.commit()

        return create_response(status.HTTP_200_OK, "Contact updated successfully.")


    except Exception as err:
        logger.error(f"Error in update contact: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
    

# --- GET ALL CONTACTS ENDPOINT ---
@router.get("/get-all", summary="Get all contacts")
async def get_all_contacts(request: Request, 
    db=Depends(get_db), 
    current_user: User = Depends(get_current_user),
    name: Optional[str] = Query(None, description="Filter by student and parent name"),
    limit: int = Query(20, gt=0, le=100, description="Number of contacts to return per page (max 100)"),
    offset: int = Query(0, ge=0, description="Number of contacts to skip")):
    try:
        contacts_query = db.query(Contact).filter(Contact.user_id == current_user.id)

        # Apply name filter if provided
        if name:
            contacts_query = contacts_query.filter(
                or_(
                    Contact.student_name.ilike(f"%{name}%"),
                    Contact.parent_name.ilike(f"%{name}%")
                )
            )

        total_contacts = contacts_query.with_entities(Contact.id).count()
        contacts = contacts_query.offset(offset).limit(limit).all()

        if not contacts:
            return create_response(status.HTTP_404_NOT_FOUND, "No contacts found.")
        
        contacts_json = jsonable_encoder(contacts)

        base_url = str(request.url).split('?')[0]
        query_params = dict(request.query_params)

        # Calculate next offset
        next_offset = offset + limit
        prev_offset = max(offset - limit, 0)

        next_url = None
        if next_offset < total_contacts:
            query_params["offset"] = next_offset
            query_params["limit"] = limit
            next_url = f"{base_url}?{query_params}"

        previous_url = None
        if offset > 0:
            query_params["offset"] = prev_offset
            query_params["limit"] = limit
            previous_url = f"{base_url}?{query_params}"

        data = {
            "contacts": contacts_json,
            "pagination": {
                "total_contacts": total_contacts,
                "limit": limit,
                "offset": offset,
                "total_pages": (total_contacts + limit - 1) // limit,
                "next": next_url,
                "previous": previous_url
            }
        }
        return create_response(status.HTTP_200_OK, "Contacts retrieved successfully.", data=data)

    except Exception as err:
        logger.error(f"Error in get all contacts: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
            

# --- DELETE CONTACT ENDPOINT ---
@router.delete("/delete", summary="Delete a contact")
async def delete_contact(contact_id: int, db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
        if not contact:
            return create_response(status.HTTP_404_NOT_FOUND, "Contact not found.")

        db.delete(contact)
        db.commit()
        return create_response(status.HTTP_200_OK, "Contact deleted successfully.")
    
    except Exception as err:
        logger.error(f"Error in delete contact: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))



# --- DOWNLOAD CONTACTS ENDPOINT ---
@router.get("/download", summary="Download contacts as Excel")
async def download_contacts(db=Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()
        if not contacts:
            return create_response(status.HTTP_404_NOT_FOUND, "No contacts found.")
        
        # Convert to list of dicts
        contacts_data = [
            {
                "Student Name": c.student_name,
                "Parent Name": c.parent_name,
                "Parent Email": c.parent_email,
                "Phone No": c.parent_phone_no,
                "Mode": c.mode,
                "Created At": c.created_at.strftime("%Y-%m-%d %H:%M:%S")
            } for c in contacts
        ]

        # Convert to DataFrame
        df = pd.DataFrame(contacts_data)

        # Save to Excel in-memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Contacts')
        output.seek(0)

        headers = {
            "Content-Disposition": "attachment; filename=contacts.xlsx",
            "X-Response-Message": "Export successful",
            "X-Response-Code": "200"
        }

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )

    except Exception as err:
        logger.error(f"Error in download contacts: {str(err)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(err))
