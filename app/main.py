# Import the passlib patch first to ensure it's applied before any other imports
from app.utils.passlib_patch import patch_result
# Log warning if patch failed
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.core.config import Settings
from app.db.base import Base
from app.api.v1 import auth, template, contacts, email, schools, logs, sms

if not patch_result:
    logging.warning("Failed to apply passlib patch. Password hashing may not work correctly.")


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Messaging Platform API", version="1.0.0", description="Email/SMS platform with templating, contact uploads, and status tracking.", docs_url="/docs", redoc_url="/redoc",)
settings = Settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["https://your-frontend.com"] in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Include routers
    app.include_router(auth, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
    app.include_router(template, prefix=f"{settings.API_V1_STR}/templates", tags=["Templates"])
    app.include_router(contacts, prefix=f"{settings.API_V1_STR}/contacts", tags=["Contacts"])
    app.include_router(email, prefix=f"{settings.API_V1_STR}/email", tags=["Email"])
    app.include_router(schools, prefix=f"{settings.API_V1_STR}/schools", tags=["Schools"])
    app.include_router(logs, prefix=f"{settings.API_V1_STR}/logs", tags=["Logs"])
    app.include_router(sms, prefix=f"{settings.API_V1_STR}/sms", tags=["SMS"])
except AttributeError:
    # If your router modules export router as an attribute:
    try:
        app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
        app.include_router(template.router, prefix=f"{settings.API_V1_STR}/templates", tags=["Templates"])
        app.include_router(contacts.router, prefix=f"{settings.API_V1_STR}/contacts", tags=["Contacts"])
        app.include_router(email.router, prefix=f"{settings.API_V1_STR}/email", tags=["Email"])
        app.include_router(schools.router, prefix=f"{settings.API_V1_STR}/schools", tags=["Schools"])
        app.include_router(logs.router, prefix=f"{settings.API_V1_STR}/logs", tags=["Logs"])
        app.include_router(sms.router, prefix=f"{settings.API_V1_STR}/sms", tags=["SMS"])
    except Exception as e:
        logging.error(f"Error including routers: {e}")
        raise


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Messaging Platform API 🚀"}

