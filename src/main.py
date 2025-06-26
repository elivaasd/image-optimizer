from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
from urllib.parse import unquote
from dotenv import load_dotenv

from image_utils import process_image
from s3_utils import (
    generate_s3_key,
    check_image_exists,
    download_image_from_s3,
    upload_image_to_s3,
)

load_dotenv()

app = FastAPI(
    title="Image Optimization Service",
    description="Dynamically resize, convert, and transform images using Cloudflare-style URLs.",
    version="1.1.0"
)

# CORS config (open for any domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/image/{options}/{image_url:path}",
    summary="Resize & Convert (Cloudflare-style Path)",
    description="""
Manually try:

`/image/width=1200,h=800,format=webp,quality=80,fit=crop/https://your-image-url.com/image.jpg`

**Options supported:**
- `width`: Resize width (required)
- `h`: Resize height (optional)
- `format`: `webp`, `jpeg`, `png`
- `quality`: 1–100
- `fit`: `contain` (default), `cover`, `fill`, `crop`
"""
)
def image_path_proxy(
    options: str = Path(..., example="width=1200,h=800,quality=80,format=webp,fit=crop"),
    image_url: str = Path(..., example="https://your-image-url.com/image.jpg")
):
    try:
        # ✅ Parse options string safely
        opt_map = dict(part.split('=') for part in options.split(',') if '=' in part)

        width = int(opt_map.get("width", 800))
        height_str = opt_map.get("h")
        height = int(height_str) if height_str else None
        format = opt_map.get("format", "webp").lower()
        quality = int(opt_map.get("quality", 80))
        fit = opt_map.get("fit", "contain")

        # ✅ Unquote URL and build cache key
        src = unquote(image_url)
        s3_key = generate_s3_key(src, options)

        # ⚡️ Try cache first
        if check_image_exists(s3_key):
            print(f"[SERVED FROM S3] Key: {s3_key}")
            cached = download_image_from_s3(s3_key)
            return Response(content=cached, media_type=f"image/{format}")

        # 📥 Download original image
        img_data = requests.get(src, timeout=5).content

        # 🛠️ Process the image
        processed = process_image(img_data, width, format, quality, height, fit)

        # 📤 Upload to S3 for caching
        upload_image_to_s3(s3_key, processed, content_type=f"image/{format}")

        return Response(content=processed, media_type=f"image/{format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
