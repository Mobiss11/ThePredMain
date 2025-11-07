import boto3
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# S3 configuration
S3_ENDPOINT = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
S3_BUCKET = os.getenv('S3_BUCKET', 'thepred-events')

# Initialize S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

# Icons to upload
icons_dir = Path('webapp/static/icons')
ai_icons = [
    'ai-data-analysis.svg',
    'ai-recommendations.svg',
    'ai-insights.svg',
    'ai-notifications.svg',
    'ai-telegram-learning.svg'
]

print(f"Uploading AI icons to S3 bucket: {S3_BUCKET}")
print(f"S3 endpoint: {S3_ENDPOINT}")

for icon_name in ai_icons:
    icon_path = icons_dir / icon_name

    if not icon_path.exists():
        print(f"❌ Icon not found: {icon_path}")
        continue

    # Upload to ai-icons/ folder in S3
    s3_key = f'ai-icons/{icon_name}'

    try:
        s3_client.upload_file(
            str(icon_path),
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ContentType': 'image/svg+xml',
                'ACL': 'public-read'
            }
        )
        print(f"✅ Uploaded: {icon_name} -> s3://{S3_BUCKET}/{s3_key}")
    except Exception as e:
        print(f"❌ Failed to upload {icon_name}: {e}")

print("\n✨ Done! Icons are now available at:")
print(f"https://thepred.store/{S3_BUCKET}/ai-icons/[icon-name].svg")
