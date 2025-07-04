from PIL import Image, ImageOps
import io

def process_image(
    data: bytes,
    width: int | None,
    format: str,
    quality: int = 80,
    height: int | None = None,
    fit: str = "contain"
) -> bytes:
    image = Image.open(io.BytesIO(data))

    # Normalize format
    format = format.lower()
    if format == "jpg":
        format = "jpeg"

    # Compute dimensions
    original_width, original_height = image.size

    if width is None and height is None:
        width, height = original_width, original_height
    elif width is None:
        width = int(original_width * (height / original_height))
    elif height is None:
        height = int(original_height * (width / original_width))

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Resize according to fit
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

    # Save image to bytes
    output = io.BytesIO()
    image.save(output, format=format.upper(), quality=quality)
    output.seek(0)
    return output.read()
