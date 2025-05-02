import pandas as pd
from typing import List, Dict
from io import BytesIO
from fastapi import UploadFile
from app.utils.validators import is_valid_email, is_valid_phone

async def read_spreadsheet(files: List[UploadFile]) -> List[Dict]:
    all_data = []
    for file in files:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        elif file.filename.endswith((".xls", ".xlsx")):
            content = await file.read() 
            df = pd.read_excel(BytesIO(content), engine="openpyxl")  
        else:
            continue  # Skip unsupported files
        all_data.extend(df.fillna("").to_dict(orient="records"))
    return all_data


def validate_contacts(data: List[Dict]) -> List[Dict]:
    valid_contacts = []
    seen_students = set()

    for row in data:
        # Normalize the row, stripping spaces and converting to lowercase
        normalized_row = {k.strip().lower(): v for k, v in row.items()}

        # Get the email and phone, stripping spaces and ensuring phone is a string
        email = normalized_row.get("parent email", "").strip()
        phone = str(normalized_row.get("phone no", "")).strip()
        student_names = normalized_row.get("student name", "").strip()  # Student names field
        parent_name = normalized_row.get("parent name", "").strip()
        mode = normalized_row.get("mode", "").strip()

        # Skip if both phone and email are empty
        if not email and not phone:
            continue

        # Skip if any of the required fields are empty
        if not student_names or not mode:
            continue

        # Handle multiple student names if they are separated by a comma
        student_names_list = [name.strip() for name in student_names.split(",")] if "," in student_names else [student_names]

        # Skip duplicates based on student name
        for student_name in student_names_list:
            key = (student_name.lower(), email.lower(), phone)

            if key in seen_students:
                continue
            seen_students.add(key)  # Store the name in lowercase to avoid case-sensitive duplicates

            # Validate the email or phone
            if is_valid_email(email) or is_valid_phone(phone):
                valid_contacts.append({
                    "name": student_name,
                    "parent_name": parent_name,
                    "email": email,
                    "phone": phone,
                    "mode": mode
                })

    return valid_contacts



