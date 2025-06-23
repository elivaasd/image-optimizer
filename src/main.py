from fastapi import FastAPI, Query, HTTPException, Path
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
from PIL import Image
import io
from urllib.parse import unquote
from image_utils import process_image


app = FastAPI(
    title="Image Optimization Service",
    description="Dynamically resize and convert images via query or Cloudflare-style path parameters.",
    version="1.0.0"
)


# Allow all CORS (for browser or CDN use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/image", summary="Resize & Convert via Query Parameters")
def image_proxy(
    src: str = Query(..., description="Source image URL (HTTPS only)"),
    width: int = Query(800, description="Resize width in pixels"),
    format: str = Query("webp", description="Output format: webp, jpeg, png"),
    quality: int = Query(80, description="Image quality (1–100)")
):
    """Accepts image URL as a query parameter and returns resized and reformatted image."""
    try:
        img_data = requests.get(src, timeout=5).content
        processed = process_image(img_data, width, format, quality)
        return Response(content=processed, media_type=f"image/{format}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/image/{options}/{image_url:path}",
    summary="Resize & Convert (Cloudflare-style Path)",
    description="""
    ⚠️ Swagger UI cannot test this route due to URL encoding issues.  
    Use it manually like this:
    /image/width=1200,h=800,quality=80,format=webp/https://d4b28jbnqso5g.cloudfront.net/your-image.jpg

    - All options are comma-separated.
    - Keys: `width`, `h` (height), `quality`, `format`.
    """
)
def image_path_proxy(
    options: str = Path(..., example="width=1200,h=800,quality=80,format=webp"),
    image_url: str = Path(..., example="https://d4b28jbnqso5g.cloudfront.net/your-image.jpg")
):
    """Accepts Cloudflare-style path and returns optimized image."""
    try:
        # Parse options string
        opt_map = dict(part.split('=') for part in options.split(',') if '=' in part)
        width = int(opt_map.get("width", 800))
        height = opt_map.get("h")  # optional
        format = opt_map.get("format", "webp")
        quality = int(opt_map.get("quality", 80))

        # Decode image URL and fetch it
        src = unquote(image_url)
        img_data = requests.get(src, timeout=5).content

        # Resize/convert
        processed = process_image(img_data, width, format, quality, height)
        return Response(content=processed, media_type=f"image/{format}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
