from aioboto3 import Session
from app.core.config import settings
import uuid
from typing import BinaryIO, Optional
import logging

logger = logging.getLogger(__name__)


class S3Client:
    """S3/MinIO client for file uploads"""

    def __init__(self):
        self.session = Session()
        self.endpoint = settings.S3_ENDPOINT
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket = settings.S3_BUCKET
        self.public_url = settings.S3_PUBLIC_URL

    async def init_bucket(self):
        """Initialize S3 bucket if it doesn't exist"""
        try:
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3:
                # Check if bucket exists
                try:
                    await s3.head_bucket(Bucket=self.bucket)
                    logger.info(f"Bucket {self.bucket} already exists")
                except:
                    # Create bucket if it doesn't exist
                    await s3.create_bucket(Bucket=self.bucket)
                    logger.info(f"Created bucket {self.bucket}")

                    # Set bucket policy to public read
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "*"},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{self.bucket}/*"]
                            }
                        ]
                    }
                    import json
                    await s3.put_bucket_policy(
                        Bucket=self.bucket,
                        Policy=json.dumps(policy)
                    )
                    logger.info(f"Set public read policy for bucket {self.bucket}")
        except Exception as e:
            logger.error(f"Error initializing bucket: {e}")

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """
        Upload file to S3
        Returns: Public URL of uploaded file
        """
        try:
            # Generate unique filename
            ext = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{ext}"

            async with self.session.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3:
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=unique_filename,
                    Body=file_content,
                    ContentType=content_type,
                    ACL='public-read'
                )

            # Return public URL
            public_url = f"{self.public_url}/{self.bucket}/{unique_filename}"
            logger.info(f"Uploaded file to {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from S3 by URL"""
        try:
            # Extract key from URL
            key = file_url.split(f"{self.bucket}/")[-1]

            async with self.session.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3:
                await s3.delete_object(Bucket=self.bucket, Key=key)

            logger.info(f"Deleted file {key} from S3")
            return True

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False


# Singleton instance
s3_client = S3Client()
