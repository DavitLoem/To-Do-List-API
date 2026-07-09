from fastapi import APIRouter, Body, HTTPException, BackgroundTasks, Depends
from src.model.auth_model import (
    RegisterRequest, LoginRequest, ForgotPasswordRequest, VerifyOTPRequest,
    ResetPasswordRequest, ChangePasswordRequest, UpdateProfileRequest
)
from src.services.auth_services import (
    insert_new_acc, find_by_id, login, generate_and_save_otp,
    verify_otp_code, update_user_password, find_by_email,
    get_current_user, change_user_password, update_user_profile
)
from src.services.email_sender import send_otp_email
import jwt
import os
import datetime

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _serialize_user(user):
    return {
        "id": str(user["_id"]),
        "fullname": user["fullname"],
        "email": user["email"]
    }


@auth_router.post("/register", summary="Register a new user")
async def register(body: RegisterRequest = Body(...)):
    if body.password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    oid = await insert_new_acc(body.fullname, body.email, body.password)
    if not oid:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user = await find_by_id(oid)
    return {"message": "User registered successfully", "user": _serialize_user(user)}


@auth_router.post("/login", summary="Login a user")
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
    return {"message": "Login successful", "token": token, "user": _serialize_user(user)}


@auth_router.post("/logout", summary="Logout the current user")
async def logout_user(user_id: str = Depends(get_current_user)):
    # JWTs are stateless, so logout is handled client-side by discarding the token.
    # If you need server-side invalidation, add a token blacklist collection here.
    return {"message": "Logged out successfully"}


@auth_router.get("/me", summary="Get the logged-in user's profile")
async def get_profile(user_id: str = Depends(get_current_user)):
    user = await find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": _serialize_user(user)}


@auth_router.put("/me", summary="Update the logged-in user's profile")
async def update_profile(body: UpdateProfileRequest = Body(...), user_id: str = Depends(get_current_user)):
    user = await update_user_profile(user_id, fullname=body.fullname)
    return {"message": "Profile updated", "user": _serialize_user(user)}


@auth_router.post("/change-password", summary="Change password while logged in")
async def change_password(body: ChangePasswordRequest = Body(...), user_id: str = Depends(get_current_user)):
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    success = await change_user_password(user_id, body.old_password, body.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    return {"message": "Password changed successfully"}


@auth_router.post("/forgot-password", summary="Step 1: Request OTP")
async def forgot_password(
    body: ForgotPasswordRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    user = await find_by_email(body.email)
    if not user:
        raise HTTPException(status_code=404, detail="User with this email does not exist. Please register first.")

    otp = await generate_and_save_otp(body.email)
    background_tasks.add_task(send_otp_email, body.email, otp)

    return {"message": "OTP has been sent to your email."}


@auth_router.post("/verify-otp", summary="Step 2: Verify 4-digit OTP")
async def verify_otp(body: VerifyOTPRequest = Body(...)):
    is_valid = await verify_otp_code(body.email, body.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    return {"message": "OTP verified successfully. Proceed to reset password."}


@auth_router.post("/reset-password", summary="Step 3: Create New Password")
async def reset_password(body: ResetPasswordRequest = Body(...)):
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    is_valid = await verify_otp_code(body.email, body.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    await update_user_password(body.email, body.new_password)

    return {"message": "Password reset successfully. You can now log in."}