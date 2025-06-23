from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import requests
from PIL import Image
import io
from image_utils import process_image
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import unquote

app = FastAPI(
    title="Image Optimization Service",
    description="Resize and convert images dynamically via query or Cloudflare-style path parameters.",
    version="1.0.0"
)

# CORS for browser or CDN use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/image", summary="Resize and Convert Image via Query Parameters")
def image_proxy(
    src: str = Query(..., description="Source image URL (HTTPS only)"),
    width: int = Query(800, description="Resize width in pixels"),
    format: str = Query("webp", description="Output format: webp, jpeg, png"),
    quality: int = Query(80, description="Image quality (1–100)")
):
    """
    Fetches an image from a given URL, resizes it, converts to specified format, and returns it.
    """
    try:
        img_data = requests.get(src, timeout=5).content
        processed = process_image(img_data, width, format, quality)
        return Response(content=processed, media_type=f"image/{format}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/image/{options}/{image_url:path}", summary="Resize and Convert Image via Path Format")
def image_path_proxy(options: str, image_url: str):
    """
    Supports Cloudflare-style path formatting:
    /image/width=1200,h=800,quality=80,format=webp/{image_url}
    """
    try:
        # Parse path options into a dictionary
        opt_map = {}
        for part in options.split(','):
            if '=' in part:
                k, v = part.split('=', 1)
                opt_map[k.strip()] = v.strip()

        width = int(opt_map.get("width", 800))
        height = opt_map.get("h")
        format = opt_map.get("format", "webp")
        quality = int(opt_map.get("quality", 80))

        # Decode the image URL and fetch it
        src = unquote(image_url)
        img_data = requests.get(src, timeout=5).content

        # Call image processor with optional height
        processed = process_image(img_data, width, format, quality, height)
        return Response(content=processed, media_type=f"image/{format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
