from PIL import Image
import io

def process_image(data: bytes, width: int, format: str, quality: int = 80) -> bytes:
    image = Image.open(io.BytesIO(data))
    new_height = int(image.height * width / image.width)
    resized = image.resize((width, new_height))

    output = io.BytesIO()
    resized.save(output, format=format.upper(), quality=quality)
    output.seek(0)
    return output.read()
