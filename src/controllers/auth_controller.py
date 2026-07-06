from fastapi import APIRouter, Body, HTTPException, BackgroundTasks
from src.model.auth_model import RegisterRequest, LoginRequest, ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest
from src.services.auth_services import (
    insert_new_acc, find_by_id, login, generate_and_save_otp, 
    verify_otp_code, update_user_password, find_by_email
)
from src.services.email_sender import send_otp_email
import jwt
import os
import datetime

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/api/auth/login", summary="Login a user")
async def login_user(body: LoginRequest = Body(...)):
    user = await login(body.email, body.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = jwt.encode(
        {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        },
        os.getenv("JWT_SECRET_KEY", "secret"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256")
    )
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "fullname": user["fullname"],
            "email": user["email"]
        }
    }


@auth_router.post("/api/auth/register", summary="Register a new user")
async def register(body: RegisterRequest = Body(...)):
    if body.password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    try:
        oid = await insert_new_acc(body.fullname, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if not oid:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    user = await find_by_id(oid)
    token = jwt.encode(
        {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        },
        os.getenv("JWT_SECRET_KEY", "secret"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256")
    )
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "fullname": user["fullname"],
            "email": user["email"]
        }
    }


@auth_router.post("/api/auth/forgot-password", summary="Step 1: Request OTP")
async def forgot_password(
    body: ForgotPasswordRequest = Body(...), 
    background_tasks: BackgroundTasks = BackgroundTasks() # <-- FIXED: Added BackgroundTasks
):
    user = await find_by_email(body.email)
    
    # <-- FIXED: Make it throw an error so you know if you typed an unregistered email
    if not user:
        raise HTTPException(status_code=404, detail="User with this email does not exist. Please register first.")
    
    # Generate OTP
    otp = await generate_and_save_otp(body.email)
    
    # Send email in background
    background_tasks.add_task(send_otp_email, body.email, otp)
    print(f"🔥 BACKGROUND TASK STARTED - OTP FOR {body.email} IS: {otp} 🔥")
    
    return {"message": "OTP has been sent to your email."}


@auth_router.post("/api/auth/verify-otp", summary="Step 2: Verify 4-digit OTP")
async def verify_otp(body: VerifyOTPRequest = Body(...)):
    print(f"🔍 DEBUG - Received verify-otp request:")
    print(f"   Email: {body.email}")
    print(f"   OTP: {body.otp}")
    
    is_valid = await verify_otp_code(body.email, body.otp)
    print(f"🔍 DEBUG - OTP validation result: {is_valid}")
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    return {"message": "OTP verified successfully. Proceed to reset password."}


@auth_router.post("/api/auth/reset-password", summary="Step 3: Create New Password")
async def reset_password(body: ResetPasswordRequest = Body(...)):
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    is_valid = await verify_otp_code(body.email, body.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    await update_user_password(body.email, body.new_password)
    
    return {"message": "Password reset successfully. You can now log in."}