import os
from twilio.rest import Client
from dotenv import load_dotenv
from app.core.config import Settings

load_dotenv()
settings = Settings()

# Fetch credentials from environment variables
TWILIO_ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER = settings.TWILIO_PHONE_NUMBER

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    raise ValueError("Missing Twilio configuration in environment variables.")

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms(to_number: str, message: str) -> dict:
    """
    Sends an SMS using Twilio.
    :param to_number: Recipient's phone number (e.g., '+15555555555')
    :param message: The message content
    :return: Twilio API response dictionary
    """
    try:
        response = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number,
            status_callback="https://3c7d-112-196-96-42.ngrok-free.app/api/v1/webhook/twilio/sms/status"
        )
        return {
            "sid": response.sid,
            "status": response.status,
            "to": response.to,
            "from": response.from_,
            "error_message": response.error_message
        }
    except Exception as e:
        raise RuntimeError(f"Failed to send SMS: {str(e)}")
