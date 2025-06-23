from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import requests
from PIL import Image
import io
from image_utils import process_image
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Image Optimization Service",
    description="Resize and convert images dynamically via URL parameters.",
    version="1.0.0"
)

# CORS for future UI or browser-based use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/image", summary="Resize and Convert Image")
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
