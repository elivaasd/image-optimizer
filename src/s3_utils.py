import os
import boto3
import hashlib
from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "ap-south-1")  # Adjust if needed
)

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")  # Add in .env

def generate_s3_key(image_url: str, options: str) -> str:
    hash_input = image_url + "|" + options
    key_hash = hashlib.md5(hash_input.encode()).hexdigest()
    ext = options.split("format=")[-1].split(",")[0]
    return f"optimized/{key_hash}.{ext}"

def check_image_exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=key)
        print(f"[CACHE HIT] Found in S3: {key}")
        return True
    except ClientError:
        print(f"[CACHE MISS] Not found in S3: {key}")
        return False

def download_image_from_s3(key: str) -> bytes:
    response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    return response['Body'].read()

def upload_image_to_s3(key: str, content: bytes, content_type: str):
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=content,
        ContentType=content_type,
        CacheControl="public, max-age=31536000"
    )
