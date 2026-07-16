import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from pathlib import Path

# Try to load .env from multiple possible locations
env_path = Path(__file__).parent.parent.parent / '.env'
print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")

load_dotenv(env_path)

# Configure Cloudinary directly
cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

print(f"Cloudinary configured - Cloud Name: {cloud_name}, API Key: {api_key}, Secret: {api_secret}")

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret
)

async def upload_image(file, folder="profile_images"):
    """
    Upload an image to Cloudinary and return the URL
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            contents,
            folder=folder,
            resource_type="image",
            allowed_formats=["jpg", "jpeg", "png", "gif", "webp"],
            max_file_size=2000000  # 2MB max
        )
        
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        raise Exception(f"Image upload failed: {str(e)}")

async def delete_image(public_id: str):
    """
    Delete an image from Cloudinary
    """
    try:
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        raise Exception(f"Image deletion failed: {str(e)}")
