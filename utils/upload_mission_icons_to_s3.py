#!/usr/bin/env python3
"""
Upload mission icons to S3/MinIO
"""
import asyncio
import os
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.core.s3 import s3_client
from app.core.config import settings

ICONS_DIR = Path(__file__).parent / 'webapp' / 'static' / 'icons' / 'missions'

ICON_FILES = [
    # Original 7
    'first_bet.svg',
    'beginner.svg',
    'first_win.svg',
    'win_streak.svg',
    'active_trader.svg',
    'crypto_lover.svg',
    'referral.svg',

    # New icons
    'daily_bet.svg',
    'daily_win.svg',
    'daily_login.svg',
    'weekly_marathon.svg',
    'weekly_master.svg',
    'fire_streak.svg',
    'veteran.svg',
    'legend.svg',
    'sports_fan.svg',
    'politics_expert.svg',
    'collector.svg',
    'unstoppable.svg',
    'subscription.svg'
]


async def upload_icons():
    """Upload mission icons to S3"""
    print("="*60)
    print("MISSION ICONS UPLOAD TO S3")
    print("="*60)
    print(f"S3 Endpoint: {settings.S3_ENDPOINT}")
    print(f"S3 Bucket: {settings.S3_BUCKET}")
    print(f"S3 Public URL: {settings.S3_PUBLIC_URL}")
    print(f"Access Key: {settings.S3_ACCESS_KEY}")
    print("="*60)
    print()

    # Initialize bucket
    print("Initializing S3 bucket...")
    await s3_client.init_bucket()
    print("✓ Bucket initialized\n")

    uploaded_urls = {}

    for icon_file in ICON_FILES:
        icon_path = ICONS_DIR / icon_file

        if not icon_path.exists():
            print(f"✗ File not found: {icon_path}")
            continue

        print(f"Uploading {icon_file}...")

        with open(icon_path, 'rb') as f:
            file_content = f.read()

        # Upload with specific key name in missions/ folder
        icon_name = icon_file.replace('.svg', '')
        key = f"missions/{icon_file}"

        try:
            async with s3_client.session.client(
                's3',
                endpoint_url=s3_client.endpoint,
                aws_access_key_id=s3_client.access_key,
                aws_secret_access_key=s3_client.secret_key,
            ) as s3:
                await s3.put_object(
                    Bucket=s3_client.bucket,
                    Key=key,
                    Body=file_content,
                    ContentType='image/svg+xml',
                    ACL='public-read'
                )

            # Construct public URL
            public_url = f"{s3_client.public_url}/{s3_client.bucket}/{key}"
            uploaded_urls[icon_name] = public_url
            print(f"✓ Uploaded: {public_url}")

        except Exception as e:
            print(f"✗ Error uploading {icon_file}: {e}")

    print("\n" + "="*60)
    print("UPLOAD COMPLETE")
    print("="*60)
    print("\nUploaded URLs:")
    for name, url in uploaded_urls.items():
        print(f"  {name}: {url}")

    print("\nTo use these icons, update your mission records with these URLs")
    print("or use the icon name (e.g., 'first_bet') and the app will construct the URL")


if __name__ == '__main__':
    asyncio.run(upload_icons())
