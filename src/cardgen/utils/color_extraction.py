"""Color extraction utilities for album art."""

from io import BytesIO
from typing import Tuple
from collections import Counter

from PIL import Image


def extract_dominant_colors(
    image_bytes: bytes, n_colors: int = 2
) -> list[Tuple[float, float, float]]:
    """
    Extract dominant colors from an image using PIL's quantization.

    Args:
        image_bytes: Raw image data.
        n_colors: Number of dominant colors to extract (default: 2).

    Returns:
        List of RGB tuples in 0-1 range, ordered by dominance.
    """
    # Load image
    img = Image.open(BytesIO(image_bytes))

    # Convert to RGB if necessary
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize to reasonable size for processing (faster)
    img.thumbnail((200, 200))

    # Quantize to reduce colors and find most common
    # Convert to palette mode with n_colors
    img_quant = img.quantize(colors=n_colors)

    # Get palette colors
    palette = img_quant.getpalette()

    # Count pixel frequencies
    pixel_counts = Counter(img_quant.getdata())

    # Get the most common colors in order
    most_common = pixel_counts.most_common(n_colors)

    # Extract RGB values from palette
    dominant_colors = []
    for color_index, count in most_common:
        # Each color in palette is 3 bytes (R, G, B)
        r = palette[color_index * 3] / 255.0
        g = palette[color_index * 3 + 1] / 255.0
        b = palette[color_index * 3 + 2] / 255.0
        dominant_colors.append((r, g, b))

    return dominant_colors


def get_gradient_colors(image_bytes: bytes) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """
    Get two colors for gradient background from album art.

    If the image has two distinct dominant colors, use those.
    If mostly one color, generate a lighter and darker shade.

    Args:
        image_bytes: Raw image data.

    Returns:
        Tuple of (start_color, end_color) as RGB tuples in 0-1 range.
    """
    # Extract 2 dominant colors
    colors = extract_dominant_colors(image_bytes, n_colors=2)

    if len(colors) < 2:
        # Fallback: use black to dark gray
        return ((0.1, 0.1, 0.1), (0.3, 0.3, 0.3))

    color1, color2 = colors[0], colors[1]

    # Check if colors are too similar (mostly one color)
    # Calculate Euclidean distance in RGB space
    color_distance = (
        (color1[0] - color2[0]) ** 2 +
        (color1[1] - color2[1]) ** 2 +
        (color1[2] - color2[2]) ** 2
    ) ** 0.5

    # If colors are very similar (distance < 0.2), create lighter/darker shades
    if color_distance < 0.2:
        # Use the dominant color and create variations
        base_r, base_g, base_b = color1

        # Convert to HSV to adjust lightness while preserving hue
        hsv = rgb_to_hsv(base_r, base_g, base_b)
        h, s, v = hsv

        # Create darker shade (reduce value by 20%)
        darker_v = max(0.0, v - 0.2)
        darker_color = hsv_to_rgb(h, s, darker_v)

        # Create lighter shade (increase value by 20%)
        lighter_v = min(1.0, v + 0.2)
        lighter_color = hsv_to_rgb(h, s, lighter_v)

        return (darker_color, lighter_color)

    # Colors are distinct enough, use them as-is
    return (color1, color2)


def rgb_to_hsv(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """
    Convert RGB color to HSV.

    Args:
        r, g, b: RGB values in 0-1 range.

    Returns:
        Tuple of (h, s, v) in 0-1 range.
    """
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c

    # Value
    v = max_c

    # Saturation
    if max_c == 0:
        s = 0
    else:
        s = diff / max_c

    # Hue
    if diff == 0:
        h = 0
    elif max_c == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif max_c == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:
        h = (60 * ((r - g) / diff) + 240) % 360

    return (h / 360.0, s, v)


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[float, float, float]:
    """
    Convert HSV color to RGB.

    Args:
        h, s, v: HSV values in 0-1 range.

    Returns:
        Tuple of (r, g, b) in 0-1 range.
    """
    h = h * 360  # Convert to degrees

    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return (r + m, g + m, b + m)
