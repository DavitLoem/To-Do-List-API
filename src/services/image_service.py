import cloudinary
import cloudinary.uploader
from config.cloudinary import cloudinary

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
