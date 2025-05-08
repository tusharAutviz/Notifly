from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from app.db.models.user import User
from app.db.models.template import Template
from app.db.models.message_log import MessageLog
from app.db.models.school import School
from app.utils.email_utils import send_email_background, extract_template_variables, generate_dynamic_html_email
from app.dependencies import get_db, get_current_user
from app.db.schemas.sms import SMSRequest
from app.utils.validators import create_response
from app.core.sms_client import send_sms
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/send-sms", summary="Send email to recipients")
async def send_email(request: SMSRequest, background_tasks: BackgroundTasks, db = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        success_count = 0
        failed_recipients = []
        school = db.query(School).filter(School.id == current_user.school_id).first()
        for group in request.groups:
            template = db.query(Template).filter(
                Template.id == group.template_id,
                Template.type == "parent",
                Template.user_id == current_user.id
            ).first()

            if not template:
                return create_response(status.HTTP_404_NOT_FOUND, "Template not found.")

            placeholders = extract_template_variables(template.content)

            for recipient_info in group.recipient_data:
                recipient_mobile = recipient_info.mobile_no
                recipient_vars = recipient_info.variables

                recipient_identifier = recipient_vars.get("parent_name") or str(recipient_vars)
                if not recipient_mobile:
                    failed_recipients.append(f"Missing email for recipient: {recipient_identifier}")
                    continue

                # Add system variables
                recipient_vars["teacher_name"] = current_user.name
                recipient_vars["school_name"] = getattr(school, "school_name", "Your School")

                missing = set(placeholders) - set(recipient_vars.keys())
                if missing:
                    return create_response(status.HTTP_400_BAD_REQUEST, f"Missing required variables for {recipient_mobile}: {', '.join(missing)}")

                try:
                    sms_response = send_sms(recipient_mobile, template.content.format(**recipient_vars))

                    db.add(MessageLog(
                        user_id=current_user.id,
                        message_type="sms",
                        recipient=recipient_mobile,
                        recipient_name= recipient_vars["parent_name"],
                        content=template.content.format(**recipient_vars),
                        status=True,
                        sid=sms_response["sid"]
                    ))

                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send sms to {recipient_mobile}: {str(e)}")
                    print(e)
                    db.add(MessageLog(
                        user_id=current_user.id,
                        message_type="sms",
                        recipient=recipient_mobile,
                        recipient_name= recipient_vars["parent_name"],
                        content=template.content.format(**recipient_vars),
                        status=False
                    ))
                    failed_recipients.append(recipient_mobile)

        db.commit()

        if failed_recipients:
            return create_response(status.HTTP_207_MULTI_STATUS, f"SMS sent to {success_count} recipients, failed for {len(failed_recipients)}", data={"failed_recipients": failed_recipients})

        return create_response(status.HTTP_200_OK, f"SMS sent to {success_count} recipients")

    except Exception as e:
        logger.error(f"Error in send sms: {str(e)}")
        return create_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", detail=str(e))


# @router.post("/send")
# async def send_sms_route(payload: SMSRequest, db = Depends(get_db), current_user: get_current_user = Depends()):
#     try:
#         # Send SMS using core SMS client
#         response = send_sms(payload.phone_number, payload.message)
#         print(response)
#         # Log the SMS in the database
#         if response["status"]:
#             log = MessageLog(
#                 message_type="sms",
#                 recipient=payload.phone_number,
#                 recipient_name=payload.recipient_name,
#                 subject=None,
#                 content=payload.message,
#                 user_id=current_user.id
#             )
#             db.add(log)
#             db.commit()

#             return JSONResponse(
#                 content={
#                     "status": status.HTTP_200_OK,
#                     "message": "SMS sent successfully"
#                 },
#                 status_code=status.HTTP_200_OK
#             )
#         else:
#             log = MessageLog(
#                 message_type="sms",
#                 recipient=payload.phone_number,
#                 recipient_name=payload.recipient_name,
#                 subject=None,
#                 content=payload.message,
#                 user_id=current_user.id,
#                 status=False
#             )
#             db.add(log)
#             db.commit()
#             return JSONResponse(
#                 content={
#                     "status": status.HTTP_400_BAD_REQUEST,
#                     "message": "Failed to send SMS"
#                 },
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#     except Exception as e:
#         logger.error(f"Error in send SMS: {str(e)}")
#         return JSONResponse(
#             content={
#                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 "message": "Internal Server Error",
#                 "detail": str(e),
#             },
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

