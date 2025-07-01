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

load_dotenv()

app = FastAPI(
    title="Image Optimization Service",
    description="Dynamically resize, convert, and transform images using Cloudflare-style URLs.",
    version="1.2.0"
)

# Enable CORS (for frontend apps, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/image/{options}/{image_url:path}",
    summary="Resize & Convert Images",
    description="""
    Dynamically optimize images via URL path parameters.

    **Example usage:**
    `/image/width=1200,h=800,format=webp,quality=80,fit=crop/https://example.com/image.jpg`

    **Supported options:**
    - `width` (required): Target width in pixels
    - `h` (optional): Target height in pixels
    - `format`: `webp`, `jpeg`, or `png`
    - `quality`: 1–100 (default: 80)
    - `fit`: `contain`, `cover`, `fill`, or `crop` (default: contain)
    """
)
def image_path_proxy(
    options: str = Path(..., example="width=1200,h=800,quality=80,format=webp,fit=crop"),
    image_url: str = Path(..., example="https://example.com/image.jpg")
):
    try:
        # ✅ Parse options into a dict
        opt_map = dict(part.split('=') for part in options.split(',') if '=' in part)

        width = int(opt_map.get("width", 800))
        height = int(opt_map["h"]) if "h" in opt_map else None
        img_format = opt_map.get("format", "webp").lower()
        quality = int(opt_map.get("quality", 80))
        fit = opt_map.get("fit", "contain")

        # ✅ Decode URL and create a cache key
        src_url = unquote(image_url)
        s3_key = generate_s3_key(src_url, options)

        # 🧠 First-level cache: Redis
        redis_image = get_from_cache(s3_key)
        if redis_image:
            print(f"[CACHE HIT] Redis: {s3_key}")
            return Response(content=redis_image, media_type=f"image/{img_format}")

        # ☁️ Second-level cache: S3
        if check_image_exists(s3_key):
            print(f"[CACHE HIT] S3: {s3_key}")
            s3_image = download_image_from_s3(s3_key)
            set_in_cache(s3_key, s3_image)
            return Response(content=s3_image, media_type=f"image/{img_format}")

        # 🌐 Fetch original image
        print(f"[ORIGIN FETCH] {src_url}")
        response = requests.get(src_url, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found at source URL.")
        
        original_image = response.content

        # 🛠️ Process the image
        optimized = process_image(original_image, width, img_format, quality, height, fit)

        # ⬆️ Cache in both Redis and S3
        upload_image_to_s3(s3_key, optimized, content_type=f"image/{img_format}")
        set_in_cache(s3_key, optimized)

        return Response(content=optimized, media_type=f"image/{img_format}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail="Image processing failed.")