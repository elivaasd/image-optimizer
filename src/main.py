from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import unquote
import requests
from dotenv import load_dotenv

from image_utils import process_image
from s3_utils import (
    generate_s3_key,
    check_image_exists,
    download_image_from_s3,
    upload_image_to_s3,
)
from redis_utils import (
    get_from_cache,
    set_in_cache,
)
from memory_cache import (  # ✅ Import memory cache helpers
    get_from_memory_cache,
    set_in_memory_cache,
)

load_dotenv()

app = FastAPI(
    title="Image Optimization Service",
    description="Dynamically resize, convert, and transform images using flexible URL parameters.",
    version="1.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_dimension(value: str | None) -> int | None:
    """Convert string dimension to int, allow 'auto'."""
    if value is None or value.lower() == "auto":
        return None
    try:
        return int(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid dimension value: {value}")

@app.get(
    "/image/{options}/{image_url:path}",
    summary="Resize & Convert Images",
    description="""
    Dynamically optimize images via URL path parameters.

    **Example:**
    `/image/width=1200,h=800,format=webp,quality=80,fit=crop/https://example.com/image.jpg`

    **Options:**
    - `width`: int or 'auto'
    - `h`: int or 'auto'
    - `format`: webp, jpeg, png
    - `quality`: 1–100
    - `fit`: contain (default), cover, fill, crop
    """
)
def image_path_proxy(
    options: str = Path(..., example="width=auto,h=800,quality=80,format=webp,fit=contain"),
    image_url: str = Path(..., example="https://example.com/image.jpg")
):
    try:
        # Parse transformation options
        opt_map = dict(part.split('=') for part in options.split(',') if '=' in part)

        width = parse_dimension(opt_map.get("width", "auto"))
        height = parse_dimension(opt_map.get("h", "auto"))
        img_format = opt_map.get("format", "webp").lower()
        quality = int(opt_map.get("quality", 80))
        fit = opt_map.get("fit", "contain")

        # Unquote URL and generate cache key
        src_url = unquote(image_url)
        s3_key = generate_s3_key(src_url, options)

        # 🔁 1. In-memory LRU cache
        mem_cached = get_from_memory_cache(s3_key)
        if mem_cached:
            print(f"[CACHE HIT] Memory: {s3_key}")
            return Response(content=mem_cached, media_type=f"image/{img_format}")

        # 🧠 2. Redis
        redis_image = get_from_cache(s3_key)
        if redis_image:
            print(f"[CACHE HIT] Redis: {s3_key}")
            set_in_memory_cache(s3_key, redis_image)
            return Response(content=redis_image, media_type=f"image/{img_format}")

        # ☁️ 3. S3
        if check_image_exists(s3_key):
            print(f"[CACHE HIT] S3: {s3_key}")
            s3_image = download_image_from_s3(s3_key)
            set_in_cache(s3_key, s3_image)
            set_in_memory_cache(s3_key, s3_image)
            return Response(content=s3_image, media_type=f"image/{img_format}")

        # 🌍 4. Origin fetch
        print(f"[ORIGIN FETCH] {src_url}")
        response = requests.get(src_url, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found at source URL.")
        
        original_image = response.content

        # 🛠️ Process the image
        optimized = process_image(original_image, width, img_format, quality, height, fit)

        # 💾 Cache everywhere
        upload_image_to_s3(s3_key, optimized, content_type=f"image/{img_format}")
        set_in_cache(s3_key, optimized)
        set_in_memory_cache(s3_key, optimized)

        return Response(content=optimized, media_type=f"image/{img_format}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail="Image processing failed.")
