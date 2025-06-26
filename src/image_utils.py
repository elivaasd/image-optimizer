from PIL import Image, ImageOps
import io

def process_image(data: bytes, width: int, format: str, quality: int = 80, height: int = None, fit: str = "contain") -> bytes:
    image = Image.open(io.BytesIO(data))

    # Normalize format string
    format = format.lower()
    if format == "jpg":
        format = "jpeg"

    # Auto-calculate height if not provided
    if height is None:
        height = int(image.height * width / image.width)

    if image.mode != "RGB":
        image = image.convert("RGB")

    # Apply fit modes
    if fit == "contain":
        image = ImageOps.contain(image, (width, height))
    elif fit == "cover":
        image = ImageOps.fit(image, (width, height), method=Image.LANCZOS)
    elif fit == "fill":
        image = image.resize((width, height), Image.LANCZOS)
    elif fit == "crop":
        left = (image.width - width) / 2
        top = (image.height - height) / 2
        right = (image.width + width) / 2
        bottom = (image.height + height) / 2
        image = image.crop((left, top, right, bottom))
    else:
        raise ValueError(f"Invalid fit mode: {fit}")

    output = io.BytesIO()
    image.save(output, format=format.upper(), quality=quality)
    output.seek(0)
    return output.read()
