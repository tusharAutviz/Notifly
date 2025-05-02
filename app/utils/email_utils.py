import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks
from app.core.config import settings
import logging
import string


logger = logging.getLogger(__name__)

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: str):
    """Add email sending task to background tasks"""
    background_tasks.add_task(_send_email, subject=subject,email_to=email_to, body=body)

async def _send_email(subject: str, email_to: str, body: str):
    """Send email using SMTP"""
    try:
        message = MIMEMultipart()
        message["From"] = settings.EMAIL_FROM
        message["To"] = email_to
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "html"))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.sendmail(settings.EMAIL_FROM, email_to, message.as_string())
            
        logger.info(f"Email sent successfully to {email_to}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {str(e)}")
        return False

def get_email_template_otp(user_name: str, otp: str) -> str:
    """Generate HTML email template for OTP verification"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h2 style="color: #4a6ee0;">Email Verification</h2>
            <p>Hello {user_name},</p>
            <p>Thank you for registering with our service. To complete your registration, please use the following OTP code:</p>
            <div style="background-color: #4a6ee0; color: white; font-size: 24px; padding: 10px; text-align: center; margin: 20px 0; border-radius: 5px;">
                <strong>{otp}</strong>
            </div>
            <p>This code will expire in 10 minutes.</p>
            <p>If you did not request this verification, please ignore this email.</p>
            <p>Best regards,<br>The Team</p>
        </div>
    </body>
    </html>
    """

# def generate_dynamic_html_email(content_template: str, variables: dict):
#     """
#     Replaces placeholders like {student_name}, {parent_name} dynamically
#     and returns final HTML email template.
#     """
#     filled_content = content_template.format(**variables)
#      # Replace newlines with <br> tags for HTML rendering
#     filled_content = filled_content.replace("\n", "<br>")
#     html_template = f"""
#     <!DOCTYPE html>
#     <html>
#     <head>
#       <style>
#         body {{
#           font-family: Arial, sans-serif;
#           background-color: #f4f4f4;
#           margin: 0;
#           padding: 0;
#         }}
#         .email-container {{
#           background-color: #ffffff;
#           margin: 40px auto;
#           padding: 20px;
#           max-width: 600px;
#           border-radius: 8px;
#           box-shadow: 0 2px 8px rgba(0,0,0,0.1);
#         }}
#         .content {{
#           font-size: 16px;
#           color: #333;
#           line-height: 1.6;
#         }}
#         .footer {{
#           margin-top: 30px;
#           font-size: 14px;
#           color: #777;
#           text-align: left;
#         }}
#       </style>
#     </head>
#     <body>
#       <div class="email-container">
#         <div class="content">
#           {filled_content}
#         </div>
#       </div>
#     </body>
#     </html>
#     """
#     return html_template


def generate_dynamic_html_email(content_template: str, variables: dict):
    """
    Replaces placeholders like {student_name}, {parent_name} dynamically
    and returns final HTML email template.
    """
    filled_content = content_template.format(**variables)
     # Replace newlines with <br> tags for HTML rendering
    filled_content_br = filled_content.replace("\n", "<br>")
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{
          font-family: Arial, sans-serif;
          background-color: #f4f4f4;
          margin: 0;
          padding: 0;
        }}
        .email-container {{
          background-color: #ffffff;
          margin: 40px auto;
          padding: 20px;
          max-width: 600px;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
          text-align: center;
          padding-bottom: 20px;
        }}
        .header h1 {{
          color: #5f82ff;
          margin: 0;
          font-size: 24px;
        }}
        .content {{
          font-size: 16px;
          color: #333;
          line-height: 1.6;
        }}
        .footer {{
          margin-top: 30px;
          font-size: 14px;
          color: #777;
          text-align: left;
        }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <div class="header">
          <h1>Notify</h1>
        </div>
        <div class="content">
            {filled_content_br}
        </div>
      </div>
    </body>
    </html>
    """
    return {"html_template": html_template, "filled_content": filled_content}



def extract_template_variables(template: str):
    formatter = string.Formatter()
    variables = set()

    for literal_text, field_name, format_spec, conversion in formatter.parse(template):
        if field_name is not None:
            variables.add(field_name)
    return list(variables)