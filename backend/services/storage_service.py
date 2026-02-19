import boto3
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
