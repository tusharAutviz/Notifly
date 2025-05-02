from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from app.db.models.user import User
from app.db.models.template import Template
from app.db.models.message_log import MessageLog
from app.db.models.school import School
from app.utils.email_utils import send_email_background, extract_template_variables, generate_dynamic_html_email
from app.dependencies import get_db, get_current_user
from app.db.schemas.email import EmailRequest
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/send-email/", summary="Send email to recipients")
async def send_email(request: EmailRequest, background_tasks: BackgroundTasks, db = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        success_count = 0
        failed_recipients = []
        school = db.query(School).filter(School.id == current_user.school_id).first()
        for group in request.groups:
            template = db.query(Template).filter(
                Template.id == group.template_id,
                Template.type == "email",
                Template.user_id == current_user.id
            ).first()

            if not template:
                return JSONResponse(
                    content={
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Template not found."
                    },
                    status_code=status.HTTP_404_NOT_FOUND
                )

            placeholders = extract_template_variables(template.content)

            for recipient_info in group.recipient_data:
                recipient_email = recipient_info.email
                recipient_vars = recipient_info.variables

                recipient_identifier = recipient_vars.get("parent_name") or str(recipient_vars)
                if not recipient_email:
                    failed_recipients.append(f"Missing email for recipient: {recipient_identifier}")
                    continue

                # Add system variables
                recipient_vars["teacher_name"] = current_user.name
                recipient_vars["school_name"] = getattr(school, "school_name", "Your School")

                missing = set(placeholders) - set(recipient_vars.keys())
                if missing:
                    return JSONResponse(
                        content={
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": f"Missing required variables for {recipient_email}: {', '.join(missing)}"
                        },
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                email_body = generate_dynamic_html_email(template.content, recipient_vars)

                try:
                    send_email_background(
                        background_tasks=background_tasks,
                        subject=group.subject,
                        email_to=recipient_email,
                        body=email_body["html_template"]
                    )

                    db.add(MessageLog(
                        user_id=current_user.id,
                        message_type="email",
                        recipient=recipient_email,
                        recipient_name= recipient_vars["parent_name"],
                        subject=group.subject,
                        content=email_body["filled_content"],
                        status=True,
                    ))

                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
                    db.add(MessageLog(
                        user_id=current_user.id,
                        message_type="email",
                        recipient=recipient_email,
                        recipient_name= recipient_vars["parent_name"],
                        subject=group.subject,
                        content=email_body["filled_content"],
                        status=False,
                    ))
                    failed_recipients.append(recipient_email)

        db.commit()

        if failed_recipients:
            return JSONResponse(
                content={
                    "status": status.HTTP_207_MULTI_STATUS,
                    "message": f"Email sent to {success_count} recipients, failed for {len(failed_recipients)}",
                    "data": {
                        "failed_recipients": failed_recipients,
                    }
                },
                status_code=status.HTTP_207_MULTI_STATUS
            )
        return JSONResponse(
            content={
                "status": status.HTTP_200_OK,
                "message": f"Email sent to {success_count} recipients",
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"Error in send email: {str(e)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(e),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )