from fastapi import APIRouter, Request, Depends
from starlette.responses import JSONResponse
from app.dependencies import get_db
from app.db.models.message_log import MessageLog
from app.utils.validators import create_response

router = APIRouter()

@router.post("/twilio/sms/status")
async def sms_status_webhook(request: Request, db=Depends(get_db)):
    form = await request.form()
    message_sid = form.get("MessageSid")
    message_status = form.get("MessageStatus")
    to = form.get("To")
    error_message = form.get("ErrorMessage")

    # Update your MessageLog status here based on SID
    if message_status == "failed" and message_status == "undelivered":
        db.query(MessageLog).filter(MessageLog.sid == message_sid).update({"status": False})

    if message_status == "delivered" and message_status == "sent":
        db.query(MessageLog).filter(MessageLog.sid == message_sid).update({"status": True})

    return create_response(200, "Webhook received successfully.")