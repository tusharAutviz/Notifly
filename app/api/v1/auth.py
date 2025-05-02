# Import the passlib patch first to ensure it's applied before any other imports
from app.utils.passlib_patch import patch_result

from fastapi import APIRouter, Depends, status, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse
from app.db.models.user import User, RefreshToken
from app.db.models.school import School
from fastapi.security import OAuth2PasswordRequestForm
from app.dependencies import get_current_user, get_db
from app.db.schemas.user import CreateUser, VerifyOTP, ResendOtp, RegenerateAccessToken, ForgotPassword, ResetPassword, NewPassword, UpdateUser
from app.utils.validators import is_valid_email, is_valid_phone
from app.utils.otp_utils import generate_otp, save_otp_to_user, verify_otp
from app.utils.email_utils import send_email_background, get_email_template_otp
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from app.core.security import create_token, create_refresh_token, verify_token
from app.core.config import settings
from sqlalchemy import asc, or_
from fastapi.encoders import jsonable_encoder
from typing import Optional
import logging


logger = logging.getLogger(__name__)

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


# ---- USER LOGIN ENDPOINT ----
@router.post("/login/")
async def user_login(request: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    try:
        get_user = db.query(User).filter(User.email == request.username).first()
        if not get_user:
            return JSONResponse(
                content={
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found. Try to Login"
                }, 
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not get_user.is_admin:
            school = db.query(School).filter(School.id == get_user.school_id).first()
            if not school.is_active:
                return JSONResponse(
                    content={
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "School is not active."
                    }, 
                    status_code=status.HTTP_403_FORBIDDEN
                )

        # Check if user is verified
        if not get_user.otp_verified:
            return JSONResponse(
                content={
                    "status": status.HTTP_401_UNAUTHORIZED,
                    "message": "User is not verified. Please verify your email."
                }, 
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        if not get_user.is_active:
            return JSONResponse(
                content={
                    "status": status.HTTP_401_UNAUTHORIZED,
                    "message": "User is not active."
                }, 
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if not verify_password(request.password, get_user.password):
            return JSONResponse(
                content={
                    "status": status.HTTP_401_UNAUTHORIZED,
                    "message": "Incorrect password."
                }, 
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # ✅ Generate tokens
        access_token = create_token(
            data={"sub": request.username},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        refresh_token = create_refresh_token(
            data={"sub": request.username},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        store_refresh_token = RefreshToken(
            user_email=request.username,
            token=refresh_token
        )
        db.add(store_refresh_token)
        db.commit()

        return  {
                    "status": status.HTTP_200_OK,
                    "message": "Login successfully.",
                    "access_token": access_token,
                    "token_type": "bearer",
                    "data": {
                        "name": get_user.name,
                        "email": get_user.email,
                        "is_admin": get_user.is_admin,
                    }
                }

    except Exception as err:
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- USER REGISTER ENDPOINT ---
@router.post("/signup/")
async def register_user(request: CreateUser, background_tasks: BackgroundTasks, db=Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            return JSONResponse(
                content={
                    "status": status.HTTP_200_OK,
                    "message": "User is already exist please try to login."
                }, 
                status_code=status.HTTP_200_OK
            )

        hash_password = get_password_hash(request.password)

        if is_valid_email(request.email) and is_valid_phone(request.mobile_no):
            # Create user with verification pending
            create_user = User(
                name=request.name,
                email=request.email,
                password=hash_password,
                mobile_no=request.mobile_no,
                otp_verified=False,
                school_id= request.school_id,
            )
            db.add(create_user)
            db.commit()
            db.refresh(create_user)

            # Generate OTP
            otp = generate_otp()
            save_otp_to_user(db, request.email, otp)

            # Send OTP email
            email_body = get_email_template_otp(request.name, otp)
            send_email_background(
                background_tasks,
                "Email Verification",
                request.email,
                email_body
            )

            return JSONResponse(
                content={
                    "status": status.HTTP_200_OK,
                    "message": "User registered successfully. Please check your email for verification code.",
                    "data": {
                        "email": request.email
                    }
                },
                status_code=status.HTTP_200_OK
            )

        else:
            return JSONResponse(
                content={
                    "status": status.HTTP_429_TOO_MANY_REQUESTS,
                    "message": "Please enter valid email or mobile no."
                },
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )


    except Exception as err:
        logger.error(f"Error in signup: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

# --- ADMIN REGISTER ENDPOINT ---
# @router.post("/admin-signup/")
# async def register_user(request: CreateUser, background_tasks: BackgroundTasks, db=Depends(get_db)):
#     try:
#         existing_user = db.query(User).filter(User.email == request.email).first()

#         if existing_user:
#             raise HTTPException(status_code=200, detail="User is already exist please try to login.")

#         hash_password = get_password_hash(request.password)

#         if is_valid_email(request.email) and is_valid_phone(request.mobile_no):
#             # Create user with verification pending
#             create_user = User(
#                 name=request.name,
#                 email=request.email,
#                 password=hash_password,
#                 mobile_no=request.mobile_no,
#                 otp_verified=True,
#                 is_admin=True
#             )
#             db.add(create_user)
#             db.commit()
#             db.refresh(create_user)

#             # # Generate OTP
#             # otp = generate_otp()
#             # save_otp_to_user(db, request.email, otp)

#             # # Send OTP email
#             # email_body = get_email_template_otp(request.name, otp)
#             # send_email_background(
#             #     background_tasks,
#             #     "Email Verification",
#             #     request.email,
#             #     email_body
#             # )

#             return JSONResponse(
#                 content={
#                     "result": "User registered successfully. Please check your email for verification code.",
#                     "email": request.email
#                 },
#                 status_code=200
#             )

#         else:
#             raise HTTPException(status_code=429, detail="Please enter valid email or mobile no.")

#     except HTTPException as httpExcp:
#         raise httpExcp

#     except Exception as err:
#         logger.error(f"Error in signup: {str(err)}")
#         raise HTTPException(status_code=500, detail=str(err))


# --- VERIFY OTP ENDPOINT ---
@router.post("/verify-otp/")
async def verify_user_otp(request: VerifyOTP, db=Depends(get_db)):
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return JSONResponse(
                content={
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found.",
                },
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Verify OTP
        is_valid = verify_otp(db, request.email, request.otp, settings.OTP_EXPIRY_MINUTES)

        if not is_valid:
            return JSONResponse(
                content={
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid OTP or OTP has expired.",
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Checking type for reset token for reset password
        if type(is_valid) == str:
            return JSONResponse(
                content={
                    "status": status.HTTP_200_OK,
                    "message": "Otp verified sucessfully. Now you can reset your password.", 
                }, 
                status_code = status.HTTP_200_OK
            )
        
        return JSONResponse(
            content={
                "status": status.HTTP_200_OK,
                "message": "Otp verified sucessfully."
            }, 
            status_code=status.HTTP_200_OK
        )
   
    except Exception as err:
        logger.error(f"Error in OTP verification: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- FORGOT PASSWORD ENDPOINT ---
@router.post("/forgot-password/")
async def forgot_password(request: ForgotPassword, background_tasks: BackgroundTasks, db=Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return JSONResponse(
                content={
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found.",
                },
                status_code=status.HTTP_404_NOT_FOUND
            )

        otp = generate_otp()
        save_otp_to_user(db, request.email, otp)

        email_body = get_email_template_otp(user.name, otp)
        send_email_background(
            background_tasks,
            "Password Reset",
            request.email,
            email_body
        )

        return JSONResponse(
            content={
                "status": status.HTTP_200_OK,
                "message": "Password reset OTP sent to your email."
            }, 
            status_code=status.HTTP_200_OK
        )

    except Exception as err:
        logger.error(f"Error in forgot password: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- NEW PASSWORD ENDPOINT ---
@router.post("/new-password/")
async def new_password(request: NewPassword, db=Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return JSONResponse(
                content={
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found.",
                },
                status_code=status.HTTP_404_NOT_FOUND
            )

        if user.otp != request.reset_token:
            return JSONResponse(
                content={
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid reset token.",
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        expiry_time = user.otp_created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        expiry_time_timezone = expiry_time.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expiry_time_timezone:
            return JSONResponse(
                content={
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Reset token has expired.",
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Update the user's password
        hash_password = get_password_hash(request.password)
        user.password = hash_password

        # Clear the OTP after successful password reset
        user.otp = None
        user.otp_created_at = None

        # Invalidate all refresh tokens for this user for security
        refresh_tokens = db.query(RefreshToken).filter(RefreshToken.user_email == user.email).all()
        for token in refresh_tokens:
            token.blacklisted = True

        db.commit()

        return JSONResponse(
            content={
                "status": status.HTTP_200_OK,
                "message": "Password has been reset successfully. Please login with your new password."
            },
            status_code = status.HTTP_200_OK
        )

    except Exception as err:
        logger.error(f"Error in new password: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- CHANGE PASSWORD ENDPOINT ---


# --- RESEND OTP ENDPOINT ---
@router.post("/resend-otp/")
async def resend_otp(request: ResendOtp, background_tasks: BackgroundTasks, db=Depends(get_db)):
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return JSONResponse(
                content={
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found.",
                    "data": {
                        "email": request.email
                    }
                },
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if user is already verified
        if user.otp_verified:
            return JSONResponse(
                content={
                    "status": status.HTTP_200_OK,
                    "message": "User is already verified."
                },
                status_code=status.HTTP_200_OK
            )

        # Generate new OTP
        otp = generate_otp()
        save_otp_to_user(db, request.email, otp)

        # Send OTP email
        email_body = get_email_template_otp(user.name, otp)
        send_email_background(
            background_tasks,
            "Email Verification",
            request.email,
            email_body
        )

        return JSONResponse(
            content={
                "status": status.HTTP_200_OK,
                "message": "Verification code resent. Please check your email.",
                "data": {
                    "email": request.email
                }
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as err:
        logger.error(f"Error in resending OTP: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- RE-GENERATE ACCESS TOKEN FROM REFRESH TOKEN ENDPOINT ---
@router.post("/refresh-token/")
async def refresh_token(request: RegenerateAccessToken,db = Depends(get_db)):
    try:
        payload = verify_token(request.refresh_token)
        if not payload:
            return JSONResponse(
                content={
                    "status": status.HTTP_401_UNAUTHORIZED,
                    "message": "Invalid refresh token."
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        refresh = db.query(RefreshToken).filter(RefreshToken.token == request.refresh_token, RefreshToken.blacklisted == False).first()

        if not refresh:
            return JSONResponse(
                content={
                    "status": status.HTTP_401_UNAUTHORIZED,
                    "message": "Invalid refresh token."
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        new_access_token = create_token(
            data={"sub": payload.get("sub")},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh.blacklisted = True
        db.flush()

        new_refresh_token = create_refresh_token(
            data={"sub": payload.get("sub")},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        token_db = RefreshToken(
            user_email=payload.get("sub"),
            token=new_refresh_token
        )
        db.add(token_db)
        db.commit()
        return JSONResponse(
            content={
                "status": status.HTTP_200_OK,
                "message": "Token refreshed successfully.",
                "data": {
                    "access_token": new_access_token,
                    "token_type": "bearer",
                    "refresh_token": new_refresh_token
                }
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as err:
        logger.error(f"Error in refreshing token: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- RESET PASSWORD ENDPOINT ---
@router.patch("/reset-password/")
async def reset_password(request: ResetPassword, db=Depends(get_db), current_user: get_current_user = Depends()):
    try:
        # Verify current password
        if not verify_password(request.password, current_user.password):
            return JSONResponse(
                content={
                    "status": status.HTTP_401_UNAUTHORIZED,
                    "message": "Incorrect password.",
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Update to new password
        hash_password = get_password_hash(request.new_password)
        db.query(User).filter(User.id == current_user.id).update({"password": hash_password})
        db.commit()

        # Invalidate all refresh tokens for this user for security
        refresh_tokens = db.query(RefreshToken).filter(RefreshToken.user_email == current_user.email).all()
        for token in refresh_tokens:
            token.blacklisted = True
        db.commit()

        return JSONResponse(
            content={
                "status": status.HTTP_200_OK,
                "message": "Password has been changed successfully. Please login with your new password."
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as err:
        logger.error(f"Error in reset password: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# --- UPDATE USER DATA BY ADMIN ENDPOINT ---
@router.patch("/update-user/", summary="update user status by admin")
async def update_user(request: UpdateUser, db=Depends(get_db), current_user: get_current_user = Depends()):
    try:
        if current_user.is_admin:
            user = db.query(User).filter(User.id == request.user_id).first()
            if not user:
                return JSONResponse(
                    content={
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "User not found."
                    }, 
                    status_code=status.HTTP_404_NOT_FOUND
                )
                
            user.is_active = request.is_active

            if request.is_active == False:
                db.query(RefreshToken).filter(RefreshToken.user_email == user.id).update({"blacklisted":True})

            db.commit()
            return JSONResponse(content={
                    "status": status.HTTP_200_OK,
                    "message": "User status is updated successfully."
                }, 
                status_code=status.HTTP_200_OK
            )

        return JSONResponse(
            content={
                "status": status.HTTP_401_UNAUTHORIZED,
                "message": "You are not authorized."
            }, 
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    except Exception as err:
        logger.error(f"Error in update user: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




# --- SHOW USERS FOR ADMIN ENDPOINT ---
@router.get("/get-all/", summary="get user to show admin pannel")
async def get_all(request: Request, 
    db=Depends(get_db),
    username: Optional[str] = Query(None, description="Filter users by name and email"), 
    current_user: get_current_user = Depends(), 
    limit: int = Query(20, gt=0, le=100, description="Number of users per page (max 100)"),
    offset: int = Query(0, ge=0, description="Number of users to skip (pagination offset)")):
    try:
        if current_user.is_admin:
            user_query = db.query(User)
            if username:
                user_query = user_query.filter(
                    or_(
                        User.name.ilike(f"%{username}%"),
                        User.email.ilike(f"%{username}%")
                    )
                )

            users_query = user_query.order_by(asc(User.is_active))
            total_users = users_query.with_entities(User.id).count()
            users = users_query.offset(offset).limit(limit).all()
            if not users:
                return JSONResponse(
                    content={
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "No users found."
                    }, 
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            json_user = jsonable_encoder(users)
            
            
            base_url = str(request.url).split('?')[0]
            query_params = dict(request.query_params)

            # Calculate next offset
            next_offset = offset + limit
            prev_offset = max(offset - limit, 0)

            next_url = None
            if next_offset < total_users:
                query_params["offset"] = next_offset
                query_params["limit"] = limit
                next_url = f"{base_url}?{query_params}"

            previous_url = None
            if offset > 0:
                query_params["offset"] = prev_offset
                query_params["limit"] = limit
                previous_url = f"{base_url}?{query_params}"

            return JSONResponse(
                content={
                    "status": status.HTTP_200_OK,
                    "message": "Users retrieved successfully.",
                    "data": {
                        "result": json_user,
                        "pagination": {
                            "total_users": total_users,
                            "limit": limit,
                            "offset": offset,
                            "total_pages": (total_users + limit - 1) // limit,
                            "next": next_url,
                            "previous": previous_url
                        }
                    }
                },
                status_code=status.HTTP_200_OK
            )
        
        return JSONResponse(
            content={
                "status": status.HTTP_401_UNAUTHORIZED,
                "message": "You are not authorized."
            }, 
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    except Exception as err:
        logger.error(f"Error in get all users: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- LOGOUT API ENDPOINT ---
@router.post("/logout/", summary="Logout api")
async def logout(db=Depends(get_db), current_user: get_current_user = Depends()):
    try:
        db.query(RefreshToken).filter(RefreshToken.user_email == current_user.email).update({"blacklisted":True})
        db.commit()
        return JSONResponse(content={
                "status": status.HTTP_200_OK,
                "message": "logout successfully."
            }, 
            status_code=status.HTTP_200_OK
        )
    
    except Exception as err:
        logger.error(f"Error in logout: {str(err)}")
        return JSONResponse(
            content={
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "detail": str(err),
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# @router.delete("/delete/", summary="Delete a specific user")
# async def delete_user(id: int, db=Depends(get_db)):
#     try:
        
#         user = db.query(User).filter(User.id == id).first()
#         if not user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
#         db.delete(user)
#         db.commit()
#         return JSONResponse(content={"result": "User deleted successfully."}, status_code=status.HTTP_200_OK)

    
#     except HTTPException as httpExcp:
#         raise httpExcp
    
#     except Exception as err:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))