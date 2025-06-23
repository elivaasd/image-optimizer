from PIL import Image
import io

def process_image(data: bytes, width: int, format: str, quality: int = 80, height: int = None) -> bytes:
    image = Image.open(io.BytesIO(data))

    if height is None:
        height = int(image.height * width / image.width)
    else:
        height = int(height)

    resized = image.resize((width, height))

    output = io.BytesIO()
    resized.save(output, format=format.upper(), quality=quality)
    output.seek(0)
    return output.read()

