"""Image processing utilities using Pillow."""

from io import BytesIO

from PIL import Image


def load_image_from_bytes(image_data: bytes) -> Image.Image:
    """
    Load image from raw bytes.

    Args:
        image_data: Raw image bytes (JPEG, PNG, etc.).

    Returns:
        PIL Image object.
    """
    return Image.open(BytesIO(image_data))


def resize_and_crop_cover(image_data: bytes, target_size: tuple[int, int]) -> Image.Image:
    """
    Resize and crop album cover to fit target size while maintaining aspect ratio.

    Uses center crop to ensure the most important part of the image is visible.

    Args:
        image_data: Raw image bytes.
        target_size: Target size as (width, height) in pixels.

    Returns:
        Processed PIL Image.
    """
    img = load_image_from_bytes(image_data)

    # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Calculate aspect ratios
    target_width, target_height = target_size
    target_ratio = target_width / target_height
    img_ratio = img.width / img.height

    # Determine resize dimensions to cover target area
    if img_ratio > target_ratio:
        # Image is wider, scale by height
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        # Image is taller, scale by width
        new_width = target_width
        new_height = int(target_width / img_ratio)

    # Resize with high-quality resampling
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Center crop to target size
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return img.crop((left, top, right, bottom))


def save_image_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
    """
    Save PIL Image to bytes.

    Args:
        img: PIL Image object.
        format: Image format (PNG, JPEG, etc.).

    Returns:
        Image as bytes.
    """
    buffer = BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


def get_image_dimensions(image_data: bytes) -> tuple[int, int]:
    """
    Get dimensions of image without fully loading it.

    Args:
        image_data: Raw image bytes.

    Returns:
        Tuple of (width, height) in pixels.
    """
    img = load_image_from_bytes(image_data)
    return (img.width, img.height)
