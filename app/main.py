# Import the passlib patch first to ensure it's applied before any other imports
from app.utils.passlib_patch import patch_result
# Log warning if patch failed
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.db.base import Base
from app.api.v1 import auth, template, contacts, email, schools, logs, sms

if not patch_result:
    logging.warning("Failed to apply passlib patch. Password hashing may not work correctly.")


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Messaging Platform API", version="1.0.0", description="Email/SMS platform with templating, contact uploads, and status tracking.",)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["https://your-frontend.com"] in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schools, prefix="/api/v1/schools", tags=["schools"])
app.include_router(auth, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(template, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(contacts, prefix="/api/v1/contacts", tags=["Contacts"])
app.include_router(email, prefix="/api/v1/email", tags=["email"])
app.include_router(logs, prefix="/api/v1/logs", tags=["logs"])
app.include_router(sms, prefix="/api/v1/sms", tags=["sms"])


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Messaging Platform API 🚀"}