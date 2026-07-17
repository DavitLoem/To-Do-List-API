from config.mongo import users_collection, otps_collection
from bson.objectid import ObjectId
import bcrypt
from datetime import datetime, timedelta
import random
import jwt
import os

from fastapi import Header, HTTPException


async def get_current_user(authorization: str = Header(...)):
    """Extracts and verifies JWT token from Authorization header, returns user_id"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ", 1)[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_id


async def insert_new_acc(fullname: str, email: str, password: str, profile_image: str = None):
    email_lower = email.strip().lower()
    existing_user = await users_collection.find_one({"email": email_lower})
    if existing_user:
        return None

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user_doc = {
        "fullname": fullname,
        "email": email_lower,
        "password": hashed_password,
        "profile_image": profile_image,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await users_collection.insert_one(user_doc)
    return result.inserted_id


async def find_by_id(user_id: str):
    return await users_collection.find_one({"_id": ObjectId(user_id)})


async def find_by_email(email: str):
    return await users_collection.find_one({"email": email.strip().lower()})


def verify_password(stored_hash, provided_password: str) -> bool:
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")
    return bcrypt.checkpw(provided_password.encode("utf-8"), stored_hash)


async def login(email: str, password: str):
    user = await find_by_email(email)
    if not user:
        return None
    if not verify_password(user["password"], password):
        return None
    return user


async def generate_and_save_otp(email: str) -> str:
    otp = str(random.randint(1000, 9999))
    email_lower = email.strip().lower()

    await otps_collection.delete_many({"email": email_lower})

    otp_doc = {
        "email": email_lower,
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=15)
    }
    await otps_collection.insert_one(otp_doc)
    return otp


async def verify_otp_code(email: str, otp: str) -> bool:
    email_lower = email.strip().lower()
    otp_str = str(otp).strip()

    otp_record = await otps_collection.find_one({"email": email_lower, "otp": otp_str})

    if not otp_record:
        return False

    if datetime.utcnow() > otp_record["expires_at"]:
        return False

    return True


async def update_user_password(email: str, new_password: str):
    """Hashes the new password and updates the user record."""
    email_lower = email.strip().lower()
    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

    await users_collection.update_one(
        {"email": email_lower},
        {"$set": {
            "password": hashed_password,
            "updated_at": datetime.utcnow()
        }}
    )
    # Clear the OTP so it can't be reused
    await otps_collection.delete_many({"email": email_lower})


async def change_user_password(user_id: str, old_password: str, new_password: str) -> bool:
    """Changes password for a logged-in user after verifying the old one."""
    user = await find_by_id(user_id)
    if not user:
        return False
    if not verify_password(user["password"], old_password):
        return False

    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}}
    )
    return True


async def update_user_profile(user_id: str, fullname: str = None):
    update_data = {"updated_at": datetime.utcnow()}
    if fullname:
        update_data["fullname"] = fullname

    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    return await find_by_id(user_id)


def verify_token(token: str) -> str:
    """Verify JWT token and return user_id, or None if invalid/expired."""
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY", "secret"),
            algorithms=[os.getenv("JWT_ALGORITHM", "HS256")]
        )
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None