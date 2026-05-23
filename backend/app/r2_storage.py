import os
import uuid
import mimetypes
import io
import boto3
from botocore.config import Config
from PIL import Image
from flask import request

# Configuration variables loaded from environment
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "red-social")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_LOCAL_FALLBACK = os.getenv("R2_LOCAL_FALLBACK", "true").lower() in ("true", "1", "yes")

# S3 Client initialization
s3_client = None
if R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_ENDPOINT:
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto"
        )
    except Exception as e:
        print(f"Error initializing R2 boto3 client: {e}")

def get_local_url(filename: str) -> str:
    """Generates the absolute local URL for the uploaded file inside the Flask app context."""
    try:
        # Dynamically build using host from current request (e.g. http://localhost:8800/)
        return f"{request.host_url}static/uploads/{filename}"
    except Exception:
        # Fallback to local hardcoded port if request context is not available
        return f"http://localhost:8800/static/uploads/{filename}"

def save_locally(file_data: bytes, filename: str) -> None:
    """Saves the file data to the static/uploads/ directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    file_path = os.path.join(uploads_dir, filename)
    with open(file_path, "wb") as f:
        f.write(file_data)

def compress_image(file_stream, mime_type: str, target_width: int = 1080, quality: int = 75) -> tuple[bytes, str]:
    """
    Compresses and resizes image using PIL for mobile optimization.
    Returns compressed image bytes and output mime type.
    """
    try:
        img = Image.open(file_stream)
        
        # Preserve animated GIFs
        if mime_type == "image/gif":
            file_stream.seek(0)
            return file_stream.read(), mime_type
            
        # Resize if width exceeds target_width
        width, height = img.size
        if width > target_width:
            new_height = int((target_width / width) * height)
            img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
            
        # Convert transparent modes if saving as JPEG
        out_mime = mime_type
        save_format = "JPEG"
        if mime_type in ("image/jpeg", "image/jpg"):
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            out_mime = "image/jpeg"
            save_format = "JPEG"
        elif mime_type == "image/png":
            # Keep as PNG but save optimized
            save_format = "PNG"
        elif mime_type == "image/webp":
            save_format = "WEBP"
        else:
            # Fallback to JPEG
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            out_mime = "image/jpeg"
            save_format = "JPEG"
            
        out_io = io.BytesIO()
        img.save(out_io, format=save_format, quality=quality, optimize=True)
        return out_io.getvalue(), out_mime
    except Exception as e:
        print(f"Error compressing image: {e}")
        file_stream.seek(0)
        return file_stream.read(), mime_type

def upload_file_to_r2(file_stream, mime_type: str, folder: str, limit_mb: float) -> str:
    """
    Validates limits and formats, compresses image if applicable, 
    and uploads to Cloudflare R2 with automatic local fallback.
    """
    # 1. Size Validation
    file_stream.seek(0, 2)
    size_bytes = file_stream.tell()
    file_stream.seek(0)
    
    limit_bytes = limit_mb * 1024 * 1024
    if size_bytes > limit_bytes:
        raise ValueError(f"El archivo excede el límite permitido de {limit_mb}MB.")
        
    # 2. MIME Validation
    allowed_images = ("image/jpeg", "image/png", "image/webp", "image/gif")
    allowed_videos = ("video/mp4", "video/quicktime", "video/webm")
    
    if mime_type not in allowed_images and mime_type not in allowed_videos:
        raise ValueError(f"Tipo de archivo '{mime_type}' no permitido.")
        
    # 3. Generate UUID filename and preserve extension
    ext = mimetypes.guess_extension(mime_type)
    if mime_type == "image/jpeg":
        ext = ".jpg"
    elif mime_type == "video/quicktime":
        ext = ".mov"
    elif not ext:
        ext = ".bin"
        
    filename = f"{uuid.uuid4()}{ext}"
    key = f"{folder}/{filename}"
    
    # 4. Processing & Compression
    file_bytes = None
    final_mime = mime_type
    
    if mime_type in allowed_images:
        target_width = 400 if folder == "avatars" else 1080
        file_bytes, final_mime = compress_image(file_stream, mime_type, target_width=target_width)
    else:
        file_bytes = file_stream.read()
        
    # 5. Uploading
    # If S3 is configured and fallback is not forced, try uploading to Cloudflare R2
    if s3_client:
        try:
            s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=key,
                Body=file_bytes,
                ContentType=final_mime
            )
            
            # If a public serving domain is configured in the environment, use it
            r2_public_url = os.getenv("R2_PUBLIC_URL")
            if r2_public_url:
                public_clean = r2_public_url.rstrip("/")
                url = f"{public_clean}/{key}"
            else:
                # If no public URL is provided, generate a presigned GET URL valid for 7 days (maximum allowed by S3v4)
                try:
                    url = s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": R2_BUCKET_NAME, "Key": key},
                        ExpiresIn=604800  # 7 days
                    )
                except Exception as ex:
                    print(f"Error generating presigned URL: {ex}")
                    # Fallback to direct URL if presigned fails
                    endpoint_clean = R2_ENDPOINT.rstrip("/")
                    url = f"{endpoint_clean}/{R2_BUCKET_NAME}/{key}"
            return url
        except Exception as e:
            print(f"R2 upload failed: {e}. Attempting local fallback...")
            if R2_LOCAL_FALLBACK:
                save_locally(file_bytes, filename)
                return get_local_url(filename)
            else:
                raise ValueError(f"R2 upload failed and local fallback is disabled: {str(e)}")
    else:
        # Save locally as fallback
        if R2_LOCAL_FALLBACK:
            save_locally(file_bytes, filename)
            return get_local_url(filename)
        else:
            raise ValueError("R2 no está configurado y el fallback local está desactivado.")

# Obligatory API functions

def upload_avatar(file) -> str:
    """Uploads avatar file to avatars/ (5MB limit)."""
    return upload_file_to_r2(file.stream, file.content_type, "avatars", 5.0)

def upload_post_media(file) -> str:
    """Uploads post media to posts/ (15MB limit)."""
    return upload_file_to_r2(file.stream, file.content_type, "posts", 15.0)

def upload_reel(file) -> str:
    """Uploads reel to reels/ (100MB limit)."""
    return upload_file_to_r2(file.stream, file.content_type, "reels", 100.0)

def upload_story(file) -> str:
    """Uploads story to stories/ (50MB limit)."""
    return upload_file_to_r2(file.stream, file.content_type, "stories", 50.0)

def upload_chat_media(file) -> str:
    """Uploads chat media to chats/ (15MB limit)."""
    return upload_file_to_r2(file.stream, file.content_type, "chats", 15.0)
