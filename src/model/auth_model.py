from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    fullname: str = Field(..., min_length=1, max_length=100, description="Full name", examples=["John Doe"])
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Email", examples=["john@example.com"])
    password: str = Field(..., min_length=8, max_length=50, description="Password", examples=["password123"])
    confirm_password: str = Field(..., min_length=8, max_length=50, description="Confirm password", examples=["password123"])


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Email", examples=["john@example.com"])
    password: str = Field(..., min_length=8, max_length=50, description="Password", examples=["password123"])


# Add these below your existing models in auth_model.py

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Email", examples=["john@example.com"])

class VerifyOTPRequest(BaseModel):
    email: str = Field(..., description="Email", examples=["john@example.com"])
    otp: str = Field(..., description="OTP code", examples=["1234"])

class ResetPasswordRequest(BaseModel):
    email: str = Field(..., description="Email", examples=["john@example.com"])
    otp: str = Field(..., description="OTP code", examples=["1234"])
    new_password: str = Field(..., description="New Password", examples=["newpassword123"])
    confirm_password: str = Field(..., description="Confirm Password", examples=["newpassword123"])


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=50, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=50, description="New password")
    confirm_password: str = Field(..., min_length=8, max_length=50, description="Confirm new password")


class UpdateProfileRequest(BaseModel):
    fullname: str = Field(..., min_length=1, max_length=100, description="Full name", examples=["John Doe"])


class TokenResponse(BaseModel):
    id: str
    fullname: str
    email: str
