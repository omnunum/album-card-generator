"""Image processing utilities using Pillow."""

from io import BytesIO
from typing import Literal

from PIL import Image

# Type alias for image alignment
ImageAlign = Literal["center", "left", "right"]


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


def resize_and_crop_cover_fullscale(
    image_data: bytes, target_size: tuple[int, int], align: ImageAlign = "center"
) -> Image.Image:
    """
    Resize and crop album cover to fill target height with horizontal alignment.

    Scales the image to match the target height, then crops horizontally based on alignment.

    Args:
        image_data: Raw image bytes.
        target_size: Target size as (width, height) in pixels.
        align: Horizontal alignment - "center", "left", or "right".

    Returns:
        Processed PIL Image.
    """
    img = load_image_from_bytes(image_data)

    # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
    if img.mode != "RGB":
        img = img.convert("RGB")

    target_width, target_height = target_size

    # Scale image to match target height (maintains aspect ratio)
    scale_factor = target_height / img.height
    new_height = target_height
    new_width = int(img.width * scale_factor)

    # Resize with high-quality resampling
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Crop horizontally based on alignment
    if new_width <= target_width:
        # Image is narrower than target, no crop needed (center it)
        left = 0
        right = new_width
    else:
        # Image is wider than target, crop based on alignment
        if align == "left":
            # Align left edge, crop from right
            left = 0
            right = target_width
        elif align == "right":
            # Align right edge, crop from left
            left = new_width - target_width
            right = new_width
        else:  # "center" (default)
            # Center crop
            left = (new_width - target_width) // 2
            right = left + target_width

    # Top and bottom are always aligned (full height)
    top = 0
    bottom = target_height

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
