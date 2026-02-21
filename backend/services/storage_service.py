import boto3
import os
import pathlib
from botocore.config import Config
from core.config import get_settings
import io

settings = get_settings()

class S3StorageService:
    """s3-compatible storage service for cloudflare r2"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.R2_S3_API_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name='auto'  # r2 uses 'auto' or specific region
        )
        self.bucket = settings.R2_BUCKET

    def upload_file(self, content: bytes, filename: str) -> str:
        """upload bytes to r2 and return the key"""
        try:
            self.s3_client.upload_fileobj(
                io.BytesIO(content),
                self.bucket,
                filename
            )
            return filename
        except Exception as e:
            raise Exception(f"failed to upload to r2: {str(e)}")

    def download_file(self, filename: str) -> bytes:
        """download bytes from r2"""
        try:
            buffer = io.BytesIO()
            self.s3_client.download_fileobj(self.bucket, filename, buffer)
            return buffer.getvalue()
        except Exception as e:
            raise Exception(f"failed to download from r2: {str(e)}")

    def delete_file(self, filename: str):
        """delete file from r2"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=filename)
        except Exception as e:
            raise Exception(f"failed to delete from r2: {str(e)}")

class LocalStorageService:
    """local disk fallback storage service when r2 keys are omitted"""
    
    def __init__(self):
        self.base_dir = pathlib.Path("data")
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, content: bytes, filename: str) -> str:
        """write bytes to local disk"""
        try:
            file_path = self.base_dir / filename
            # ensure parent directories exist (like 'uploads/')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(content)
            return filename
        except Exception as e:
            raise Exception(f"failed to write to local storage: {str(e)}")
            
    def download_file(self, filename: str) -> bytes:
        """read bytes from local disk"""
        try:
            file_path = self.base_dir / filename
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise Exception(f"failed to read from local storage: {str(e)}")
            
    def delete_file(self, filename: str):
        """delete file from local disk"""
        try:
            file_path = self.base_dir / filename
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            raise Exception(f"failed to delete from local storage: {str(e)}")

def get_storage_service():
    """returns s3 storage if mapped, else falls back to local storage"""
    if all([settings.R2_S3_API_URL, settings.R2_ACCESS_KEY_ID, settings.R2_SECRET_ACCESS_KEY]):
        import logging
        logging.getLogger(__name__).info("initializing s3 storage service")
        return S3StorageService()
    else:
        import logging
        logging.getLogger(__name__).info("r2 credentials missing, falling back to local storage service")
        return LocalStorageService()
