"""Text utilities for sizing and layout."""


def calculate_max_font_size(
    canvas, text: str, font_family: str, max_length: float, max_height: float,
    min_size: float = 6, max_size: float = 72, safe_margin: float = 0
) -> float:
    """
    Calculate the maximum font size that will fit text in available space.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to measure.
        font_family: Font family name.
        max_length: Maximum width for the text.
        max_height: Maximum height for the text.
        min_size: Minimum font size to consider (default: 6).
        max_size: Maximum font size to consider (default: 72).
        safe_margin: Additional margin to subtract from available space (default: 0).

    Returns:
        The largest font size that fits within constraints.
    """
    # Apply safe margin to constraints
    effective_max_length = max_length - (safe_margin * 2)
    effective_max_height = max_height - (safe_margin * 2)

    # Find the largest font size that fits
    best_size = min_size

    for size in range(int(max_size), int(min_size) - 1, -1):
        text_width = canvas.stringWidth(text, font_family, size)
        text_height = size  # Approximate text height as font size

        if text_width <= effective_max_length and text_height <= effective_max_height:
            best_size = size
            break

    return best_size


def calculate_optimal_char_spacing(
    canvas, text: str, font_family: str, font_size: float, max_width: float,
    min_spacing: float = -0.5, max_spacing: float = 0.5
) -> float:
    """
    Calculate optimal character spacing to fit text within max_width.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to measure.
        font_family: Font family name.
        font_size: Font size in points.
        max_width: Maximum width for the text.
        min_spacing: Minimum character spacing in points (negative = tighter, default: -0.5).
        max_spacing: Maximum character spacing in points (positive = looser, default: 0.5).

    Returns:
        Optimal character spacing in points. Returns 0 if text fits without adjustment.
    """
    # Check if text already fits with normal spacing
    normal_width = canvas.stringWidth(text, font_family, font_size)

    if normal_width <= max_width:
        return 0.0

    # Text is too wide - try tightening (negative spacing)
    # Binary search for optimal spacing
    left, right = min_spacing, 0.0
    best_spacing = min_spacing

    for _ in range(20):  # Binary search iterations
        mid = (left + right) / 2
        # Approximate width with character spacing
        # Each character adds `spacing` to the total width
        # Spaces get both charSpace AND wordSpace (3x compression)
        num_spaces = text.count(' ')
        word_spacing = mid * 3
        adjusted_width = normal_width + (len(text) - 1) * mid + num_spaces * word_spacing

        if adjusted_width <= max_width:
            best_spacing = mid
            right = mid
        else:
            left = mid

    return best_spacing
