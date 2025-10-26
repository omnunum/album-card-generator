"""Text utilities for sizing and layout."""

from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, List
from reportlab.pdfgen.canvas import Canvas

if TYPE_CHECKING:
    from cardgen.api.models import Track
    from cardgen.design.base import RendererContext



def calculate_max_font_size(
    canvas: Canvas, text: str, font_family: str, max_length: float, max_height: float,
    min_size: float = 6, max_size: float = 72, safe_margin: float = 0, step: float = 0.25
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
        step: Step size for font size increments (default: 1.0, use 0.25 for finer granularity).

    Returns:
        The largest font size that fits within constraints.
    """
    # Apply safe margin to constraints
    effective_max_length = max_length - (safe_margin * 2)
    effective_max_height = max_height - (safe_margin * 2)

    # Find the largest font size that fits
    best_size = min_size

    # Generate range with custom step size
    current_size = max_size
    while current_size >= min_size:
        text_width = canvas.stringWidth(text, font_family, current_size)
        text_height = current_size  # Approximate text height as font size

        if text_width <= effective_max_length and text_height <= effective_max_height:
            best_size = current_size
            break

        current_size -= step

    return best_size


def calculate_optimal_char_spacing(
    canvas: Canvas, text: str, font_family: str, font_size: float, max_width: float,
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


def calculate_text_width(
    canvas: Canvas, text: str, font_family: str, font_size: float,
    char_spacing: float = 0.0, word_spacing: float = 0.0
) -> float:
    """
    Calculate text width accounting for character and word spacing.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to measure.
        font_family: Font family name.
        font_size: Font size in points.
        char_spacing: Character spacing in points (default: 0.0).
        word_spacing: Word spacing in points (default: 0.0).

    Returns:
        Total text width in points.
    """
    base_width = canvas.stringWidth(text, font_family, font_size)
    width_with_spacing = base_width + (len(text) * char_spacing) + (text.count(' ') * word_spacing)
    return width_with_spacing


def wrap_text_to_width(
    canvas: Canvas, text: str, max_width: float, font_family: str, font_size: float,
    char_spacing: float = 0.0, word_spacing: float = 0.0,
    mode: str = "multi_line"
) -> list[str] | tuple[str, str]:
    """
    Wrap text at word boundaries to fit within max_width.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to wrap.
        max_width: Maximum width in points.
        font_family: Font family name.
        font_size: Font size in points.
        char_spacing: Character spacing in points (default: 0.0).
        word_spacing: Word spacing in points (default: 0.0).
        mode: "multi_line" returns list of all lines, "two_part" returns (first_line, remainder).

    Returns:
        List of wrapped lines (multi_line mode) or tuple of (first_line, remainder) (two_part mode).
    """
    words = text.split()

    if mode == "two_part":
        # Two-part mode: return (first_line, remainder)
        first_line = ""
        remainder = text

        for i, word in enumerate(words):
            test_line = " ".join(words[:i+1])
            width = calculate_text_width(canvas, test_line, font_family, font_size, char_spacing, word_spacing)

            if width <= max_width:
                first_line = test_line
                remainder = " ".join(words[i+1:])
            else:
                break

        # If no words fit, split at character boundary
        if not first_line:
            for i in range(len(text), 0, -1):
                test_text = text[:i]
                width = calculate_text_width(canvas, test_text, font_family, font_size, char_spacing, word_spacing)
                if width <= max_width:
                    first_line = test_text
                    remainder = text[i:]
                    break

        return first_line, remainder

    else:
        # Multi-line mode: return list of all wrapped lines
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            width = calculate_text_width(canvas, test_line, font_family, font_size, char_spacing, word_spacing)

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines


def truncate_text_with_ellipsis(
    canvas: Canvas, text: str, max_width: float, font_family: str, font_size: float,
    char_spacing: float = 0.0, word_spacing: float = 0.0,
    ellipsis: str = "…"
) -> str:
    """
    Truncate text with ellipsis to fit within max_width using binary search.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to truncate.
        max_width: Maximum width in points.
        font_family: Font family name.
        font_size: Font size in points.
        char_spacing: Character spacing in points (default: 0.0).
        word_spacing: Word spacing in points (default: 0.0).
        ellipsis: Ellipsis character(s) to append (default: "…").

    Returns:
        Truncated text with ellipsis if needed, or original text if it fits.
    """
    # Check if text already fits
    text_width = calculate_text_width(canvas, text, font_family, font_size, char_spacing, word_spacing)
    if text_width <= max_width:
        return text

    # Calculate ellipsis width
    ellipsis_width = calculate_text_width(canvas, ellipsis, font_family, font_size, char_spacing, 0)
    available_text_width = max_width - ellipsis_width

    # Binary search for the right length
    left, right = 0, len(text)
    best_length = 0

    while left <= right:
        mid = (left + right) // 2
        truncated_text = text[:mid]
        width = calculate_text_width(canvas, truncated_text, font_family, font_size, char_spacing, word_spacing)

        if width <= available_text_width:
            best_length = mid
            left = mid + 1
        else:
            right = mid - 1

    return text[:best_length] + ellipsis


def fit_text_adaptive(
    canvas: Canvas, text: str, max_width: float, font_family: str, font_size: float,
    word_spacing: float = 0.0, min_char_spacing: float = -1.0,
    allow_wrap: bool = False, max_width_line2: float | None = None
) -> dict:
    """
    Adaptively fit text with fallback strategies: compress → wrap → truncate.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to fit.
        max_width: Maximum width for the text (or first line if wrapping).
        font_family: Font family name.
        font_size: Font size in points.
        word_spacing: Word spacing in points (default: 0.0).
        min_char_spacing: Minimum character spacing threshold (default: -1.0).
        allow_wrap: Allow wrapping to multiple lines (default: False).
        max_width_line2: Maximum width for second line if wrapping (defaults to max_width).

    Returns:
        {
            'text': str or list[str],  # Single string or list if wrapped
            'char_spacing': float or list[float],  # Single value or list if wrapped
            'truncated': bool
        }
    """
    # Step 1: Try normal spacing
    text_width = calculate_text_width(canvas, text, font_family, font_size, 0.0, word_spacing)

    if text_width <= max_width:
        return {'text': text, 'char_spacing': 0.0, 'truncated': False}

    # Step 2: Calculate compression needed
    if len(text) > 0:
        char_spacing = (max_width - text_width) / len(text)
    else:
        char_spacing = 0.0

    if char_spacing >= min_char_spacing:
        # Compression is acceptable
        return {'text': text, 'char_spacing': char_spacing, 'truncated': False}

    # Step 3: Try wrapping if allowed
    if allow_wrap:
        max_width_line2 = max_width_line2 or max_width
        first_line, remainder = wrap_text_to_width(
            canvas, text, max_width, font_family, font_size, 0.0, word_spacing, mode="two_part"
        )

        if remainder:
            # Calculate widths for both lines
            line1_width = calculate_text_width(canvas, first_line, font_family, font_size, 0.0, word_spacing)
            line2_width = calculate_text_width(canvas, remainder, font_family, font_size, 0.0, word_spacing)

            # Check if both lines fit with normal spacing
            if line1_width <= max_width and line2_width <= max_width_line2:
                return {'text': [first_line, remainder], 'char_spacing': [0.0, 0.0], 'truncated': False}

            # Calculate compression for each line
            line1_char_spacing = (max_width - line1_width) / len(first_line) if len(first_line) > 0 else 0.0
            line2_char_spacing = (max_width_line2 - line2_width) / len(remainder) if len(remainder) > 0 else 0.0

            # Use unified compression from the worst case
            unified_char_spacing = min(line1_char_spacing, line2_char_spacing)

            if unified_char_spacing >= min_char_spacing:
                # Both lines can fit with compression
                return {
                    'text': [first_line, remainder],
                    'char_spacing': [unified_char_spacing, unified_char_spacing],
                    'truncated': False
                }

            # Truncate line 2 with min compression
            truncated_line2 = truncate_text_with_ellipsis(
                canvas, remainder, max_width_line2, font_family, font_size,
                min_char_spacing, word_spacing
            )

            return {
                'text': [first_line, truncated_line2],
                'char_spacing': [min_char_spacing, min_char_spacing],
                'truncated': True
            }

    # Step 4: Last resort - truncate with min compression
    truncated_text = truncate_text_with_ellipsis(
        canvas, text, max_width, font_family, font_size,
        min_char_spacing, word_spacing
    )

    return {'text': truncated_text, 'char_spacing': min_char_spacing, 'truncated': True}


def fit_text_two_lines(
    canvas: Canvas, text: str,
    line1_max_width: float, line2_max_width: float,
    font_family: str, font_size: float,
    word_spacing: float = 0.0, min_char_spacing: float = -1.0
) -> dict:
    """
    Fit text across two lines with different max widths.

    Optimized for tracklist use case where line 1 has less space (track number + duration)
    and line 2 has more space (indent only).

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to fit.
        line1_max_width: Maximum width for first line.
        line2_max_width: Maximum width for second line.
        font_family: Font family name.
        font_size: Font size in points.
        word_spacing: Word spacing in points (default: 0.0).
        min_char_spacing: Minimum character spacing threshold (default: -1.0).

    Returns:
        {
            'line1': str,
            'line2': str,
            'line1_char_spacing': float,
            'line2_char_spacing': float,
            'truncated': bool
        }
    """
    # Try single line first
    text_width = calculate_text_width(canvas, text, font_family, font_size, 0.0, word_spacing)

    if text_width <= line1_max_width:
        return {
            'line1': text,
            'line2': '',
            'line1_char_spacing': 0.0,
            'line2_char_spacing': 0.0,
            'truncated': False
        }

    # Calculate compression needed for single line
    char_spacing = (line1_max_width - text_width) / len(text) if len(text) > 0 else 0.0

    if char_spacing >= min_char_spacing:
        # Single line with compression
        return {
            'line1': text,
            'line2': '',
            'line1_char_spacing': char_spacing,
            'line2_char_spacing': 0.0,
            'truncated': False
        }

    # Wrap to two lines
    first_line, remainder = wrap_text_to_width(
        canvas, text, line1_max_width, font_family, font_size, 0.0, word_spacing, mode="two_part"
    )

    if not remainder:
        # Entire text fits on line 1 after split
        return {
            'line1': first_line,
            'line2': '',
            'line1_char_spacing': 0.0,
            'line2_char_spacing': 0.0,
            'truncated': False
        }

    # Calculate widths for both lines
    line1_width = calculate_text_width(canvas, first_line, font_family, font_size, 0.0, word_spacing)
    line2_width = calculate_text_width(canvas, remainder, font_family, font_size, 0.0, word_spacing)

    # Check if both lines fit with normal spacing
    if line1_width <= line1_max_width and line2_width <= line2_max_width:
        return {
            'line1': first_line,
            'line2': remainder,
            'line1_char_spacing': 0.0,
            'line2_char_spacing': 0.0,
            'truncated': False
        }

    # Calculate compression factors for both lines
    line1_char_spacing = (line1_max_width - line1_width) / len(first_line) if len(first_line) > 0 else 0.0
    line2_char_spacing = (line2_max_width - line2_width) / len(remainder) if len(remainder) > 0 else 0.0

    # Use unified compression from the worst case for consistency
    unified_char_spacing = min(line1_char_spacing, line2_char_spacing)

    if unified_char_spacing >= min_char_spacing:
        # Both lines can fit with compression
        return {
            'line1': first_line,
            'line2': remainder,
            'line1_char_spacing': unified_char_spacing,
            'line2_char_spacing': unified_char_spacing,
            'truncated': False
        }

    # Last resort - use min compression and truncate line 2
    truncated_line2 = truncate_text_with_ellipsis(
        canvas, remainder, line2_max_width, font_family, font_size,
        min_char_spacing, word_spacing
    )

    return {
        'line1': first_line,
        'line2': truncated_line2,
        'line1_char_spacing': min_char_spacing,
        'line2_char_spacing': min_char_spacing,
        'truncated': True
    }


# ============================================================================
# Advanced Text Block Fitting with Arbitrary Line Sizes
# ============================================================================

@dataclass
class Line:
    """
    Represents a line of text with typographical properties.

    Attributes:
        text: The text content.
        point_size: Font size in points.
        leading_ratio: Multiplier for leading (vertical space between baselines) relative to point_size.
        horizontal_scale: Character width scale (1.0 = 100%, 0.8 = 80% condensed).
        fixed_size: If True, point_size is never reduced during fitting iterations (for fixed-height elements).
        track: Reference to the original Track object (if this line represents a track).
    """
    text: str
    point_size: float = 16.0
    leading_ratio: float = 1.0
    horizontal_scale: float = 1.0
    fixed_size: bool = False
    track: Track | None = None


def _measure_line_width(
    canvas: Canvas, text: str, font_family: str, point_size: float, horizontal_scale: float
) -> float:
    """
    Measure the width of text with horizontal scaling applied.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to measure.
        font_family: Font family name.
        point_size: Font size in points.
        horizontal_scale: Character width scale (1.0 = normal, <1.0 = condensed).

    Returns:
        Width in points.
    """
    base_width = canvas.stringWidth(text, font_family, point_size)
    return base_width * horizontal_scale


def _split_line_at_word_boundary(
    canvas: Canvas, text: str, max_width: float, font_family: str, point_size: float,
    horizontal_scale: float, split_max: int
) -> List[str]:
    """
    Split text at word boundaries to fit within max_width, up to split_max times.

    Uses greedy algorithm to fill each line as much as possible.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to split.
        max_width: Maximum width per line.
        font_family: Font family name.
        point_size: Font size in points.
        horizontal_scale: Character width scale.
        split_max: Maximum number of splits (e.g., 1 = max 2 lines).

    Returns:
        List of text segments (up to split_max + 1 lines).
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        width = _measure_line_width(canvas, test_line, font_family, point_size, horizontal_scale)

        if width <= max_width:
            current_line = test_line
        else:
            # Current line is full, start new line
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Single word doesn't fit, force it on its own line
                lines.append(word)
                current_line = ""

            # Check if we've reached split limit
            if len(lines) > split_max:
                # Combine remaining into last line
                remaining_words = words[words.index(word):]
                current_line = " ".join(remaining_words)
                break

    if current_line:
        lines.append(current_line)

    return lines


def _truncate_at_word_boundary(
    canvas: Canvas, text: str, max_width: float, font_family: str, point_size: float,
    horizontal_scale: float
) -> str:
    """
    Truncate text at word boundary with ellipsis to fit within max_width.

    Args:
        canvas: ReportLab canvas for measuring text.
        text: Text to truncate.
        max_width: Maximum width.
        font_family: Font family name.
        point_size: Font size in points.
        horizontal_scale: Character width scale.

    Returns:
        Truncated text with ellipsis (e.g., "Some text…").
    """
    ellipsis = "…"
    ellipsis_width = _measure_line_width(canvas, ellipsis, font_family, point_size, horizontal_scale)
    available_width = max_width - ellipsis_width

    words = text.split()
    truncated = ""

    for i, word in enumerate(words):
        test_line = " ".join(words[:i+1])
        width = _measure_line_width(canvas, test_line, font_family, point_size, horizontal_scale)

        if width <= available_width:
            truncated = test_line
        else:
            break

    return truncated + ellipsis if truncated else ellipsis


def _process_lines_at_current_size(
    canvas: Canvas, lines: List[Line], font_family: str, max_width: float,
    min_horizontal_scale: float, split_max: int
) -> List[Line]:
    """
    Process all lines at their current point sizes to fit within max_width.

    This function:
    1. Calculates needed horizontal_scale for each line independently
    2. Splits lines if compression would be too extreme
    3. For split lines from the same input, uses the worse compression for consistency

    Args:
        canvas: ReportLab canvas for measuring text.
        lines: Input lines with point_size and leading_ratio set.
        font_family: Font family name.
        max_width: Maximum width constraint.
        min_horizontal_scale: Minimum allowed horizontal scale (e.g., 0.7 = 70%).
        split_max: Maximum times a line can be split.

    Returns:
        Processed lines with updated text, horizontal_scale, and potentially more lines from splits.
    """
    processed_lines = []

    # Process each line independently
    for line in lines:
        base_width = canvas.stringWidth(line.text, font_family, line.point_size)

        if base_width <= max_width:
            # Line fits without compression
            processed_lines.append(Line(
                text=line.text,
                point_size=line.point_size,
                leading_ratio=line.leading_ratio,
                horizontal_scale=1.0,
                fixed_size=line.fixed_size,
                track=line.track
            ))
        else:
            # Calculate needed compression
            needed_scale = max_width / base_width

            if needed_scale >= min_horizontal_scale:
                # Compression is acceptable
                processed_lines.append(Line(
                    text=line.text,
                    point_size=line.point_size,
                    leading_ratio=line.leading_ratio,
                    horizontal_scale=needed_scale,
                    fixed_size=line.fixed_size,
                    track=line.track
                ))
            else:
                # Compression too extreme - try splitting
                split_lines = _split_line_at_word_boundary(
                    canvas, line.text, max_width, font_family, line.point_size,
                    min_horizontal_scale, split_max
                )

                # Calculate scale needed for each split line
                split_parts = []
                for i, split_text in enumerate(split_lines):
                    split_width = canvas.stringWidth(split_text, font_family, line.point_size)
                    split_scale = max_width / split_width if split_width > max_width else 1.0

                    # If last line and scale still too extreme, truncate
                    if i == len(split_lines) - 1 and split_scale < min_horizontal_scale:
                        split_text = _truncate_at_word_boundary(
                            canvas, split_text, max_width, font_family, line.point_size,
                            min_horizontal_scale
                        )
                        split_scale = min_horizontal_scale

                    split_parts.append((split_text, split_scale))

                # Find worst (minimum) scale among split parts from THIS line only
                unified_scale = min(scale for _, scale in split_parts)

                # Apply unified scale to all parts of this split line
                for split_text, _ in split_parts:
                    processed_lines.append(Line(
                        text=split_text,
                        point_size=line.point_size,
                        leading_ratio=line.leading_ratio,
                        horizontal_scale=unified_scale,
                        fixed_size=line.fixed_size,
                        track=line.track  # All split parts reference the same track
                    ))

    return processed_lines


def _calculate_total_height(lines: List[Line]) -> float:
    """
    Calculate total vertical height of all lines including leading.

    Args:
        lines: List of Line objects.

    Returns:
        Total height in points.
    """
    total = sum(line.point_size for line in lines)
    total += sum(line.point_size * line.leading_ratio for line in lines)
    return total


def fit_text_block(
    canvas: Canvas, lines: List[Line], context: RendererContext,
    max_width: float,
    max_height: float,
    min_horizontal_scale: float = 0.7,
    split_max: int = 1,
    size_reduction_ratio: float = 0.984375,  # ~0.25pt reduction on 16pt font
    min_point_size: float = 6.0
) -> List[Line]:
    """
    Fit a block of text lines within width and height constraints.

    This algorithm:
    1. Attempts to fit all lines at their current point sizes by:
       - Applying horizontal scaling (condensing) if needed
       - Splitting lines if compression would be too extreme
       - Truncating with ellipsis as last resort
    2. Ensures all lines use the same horizontal_scale for visual consistency
    3. If total height exceeds max_height, reduces all point sizes proportionally and retries

    Args:
        canvas: ReportLab canvas for measuring text.
        lines: List of Line objects with text, point_size, and leading_ratio.
        font_family: Font family name to use for all text.
        max_width: Maximum width constraint (post-margin).
        max_height: Maximum height constraint (post-margin).
        min_horizontal_scale: Minimum allowed horizontal scale (default: 0.7 = 70%).
        split_max: Maximum times a line can be split (default: 1 = max 2 lines per input line).
        size_reduction_ratio: Multiplicative factor for reducing font size each iteration (default: 0.984375).
        min_point_size: Minimum point size allowed (default: 6.0).

    Returns:
        List of fitted Line objects with final text, point_size, leading_ratio, and horizontal_scale.
    """
    # Make copies of input lines to avoid mutating originals
    current_lines = [copy.copy(line) for line in lines]
    track_size = context.font_config.track_size 
    while True:
        # Estimate widths at 12pt (will scale proportionally)
        track_num_width = canvas.stringWidth(f"{00:2d}.", context.font_config.monospace_family, track_size)
        helvetica_space_width = canvas.stringWidth(" ", context.font_config.family, track_size)
        duration_width = canvas.stringWidth("00:00", context.font_config.monospace_family, track_size)
        gap_before_duration = 3

        # Available width for track title text (first line - most restrictive)
        title_width = max_width - track_num_width - helvetica_space_width - duration_width - gap_before_duration

        # Process lines at current sizes
        processed_lines = _process_lines_at_current_size(
            canvas, current_lines, context.font_config.family, title_width,
            min_horizontal_scale, split_max
        )

        # Calculate total height
        total_height = _calculate_total_height(processed_lines)

        # Check if we fit within vertical constraints
        if total_height <= max_height:
            return processed_lines

        # Check if we've hit minimum size
        min_size = min(line.point_size for line in current_lines)
        if min_size <= min_point_size:
            # Can't reduce further, return best effort
            return processed_lines

        # Reduce font sizes proportionally (skip fixed_size lines)
        for line in current_lines:
            if not line.fixed_size:
                line.point_size *= size_reduction_ratio
        track_size *= size_reduction_ratio
