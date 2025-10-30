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
        font_family: Font family name for this line (e.g., "Helvetica", "Helvetica-Bold", "Courier").
        prefix: Text before main content (track numbers, tree characters, etc.). Defaults to monospace font.
        suffix: Text after main content (durations, etc.). Defaults to monospace font.
        prefix_font: Font family for prefix. None means use default monospace from context.
        suffix_font: Font family for suffix. None means use default monospace from context.
    """
    text: str
    point_size: float = 16.0
    leading_ratio: float = 1.0
    horizontal_scale: float = 1.0
    fixed_size: bool = False
    track: Track | None = None
    font_family: str = "Helvetica"
    prefix: str = ""
    suffix: str = ""
    prefix_font: str | None = None
    suffix_font: str | None = None


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
    canvas: Canvas, lines: List[Line], context: RendererContext, max_width: float,
    min_horizontal_scale: float, split_max: int
) -> List[Line]:
    """
    Process all lines at their current point sizes to fit within max_width.

    This function:
    1. Calculates needed horizontal_scale for each line independently
    2. Splits lines if compression would be too extreme
    3. For split lines from the same input, uses the worse compression for consistency
    4. Accounts for prefix/suffix width when calculating effective width for text

    Args:
        canvas: ReportLab canvas for measuring text.
        lines: Input lines with point_size, leading_ratio, and font_family set.
        context: Rendering context with font configuration.
        max_width: Maximum width constraint (total available width).
        min_horizontal_scale: Minimum allowed horizontal scale (e.g., 0.7 = 70%).
        split_max: Maximum times a line can be split.

    Returns:
        Processed lines with updated text, horizontal_scale, and potentially more lines from splits.
    """
    processed_lines = []

    # Process each line independently
    for line in lines:
        # Calculate effective width for text content (accounting for prefix/suffix)
        prefix_font = line.prefix_font or context.theme.effective_monospace_family
        suffix_font = line.suffix_font or context.theme.effective_monospace_family

        prefix_width = canvas.stringWidth(line.prefix, prefix_font, line.point_size) if line.prefix else 0
        suffix_width = canvas.stringWidth(line.suffix, suffix_font, line.point_size) if line.suffix else 0
        effective_width = max_width - prefix_width - suffix_width

        base_width = canvas.stringWidth(line.text, line.font_family, line.point_size)

        if base_width <= effective_width:
            # Line fits without compression
            processed_lines.append(Line(
                text=line.text,
                point_size=line.point_size,
                leading_ratio=line.leading_ratio,
                horizontal_scale=1.0,
                fixed_size=line.fixed_size,
                track=line.track,
                font_family=line.font_family,
                prefix=line.prefix,
                suffix=line.suffix,
                prefix_font=line.prefix_font,
                suffix_font=line.suffix_font
            ))
        else:
            # Calculate needed compression
            needed_scale = effective_width / base_width

            if needed_scale >= min_horizontal_scale:
                # Compression is acceptable
                processed_lines.append(Line(
                    text=line.text,
                    point_size=line.point_size,
                    leading_ratio=line.leading_ratio,
                    horizontal_scale=needed_scale,
                    fixed_size=line.fixed_size,
                    track=line.track,
                    font_family=line.font_family,
                    prefix=line.prefix,
                    suffix=line.suffix,
                    prefix_font=line.prefix_font,
                    suffix_font=line.suffix_font
                ))
            else:
                # Compression too extreme - try splitting
                split_lines = _split_line_at_word_boundary(
                    canvas, line.text, effective_width, line.font_family, line.point_size,
                    min_horizontal_scale, split_max
                )

                # Calculate scale needed for each split line
                split_parts = []
                for i, split_text in enumerate(split_lines):
                    split_width = canvas.stringWidth(split_text, line.font_family, line.point_size)
                    split_scale = effective_width / split_width if split_width > effective_width else 1.0

                    # If last line and scale still too extreme, truncate
                    if i == len(split_lines) - 1 and split_scale < min_horizontal_scale:
                        split_text = _truncate_at_word_boundary(
                            canvas, split_text, effective_width, line.font_family, line.point_size,
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
                        track=line.track,  # All split parts reference the same track
                        font_family=line.font_family,
                        prefix=line.prefix,
                        suffix=line.suffix,
                        prefix_font=line.prefix_font,
                        suffix_font=line.suffix_font
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
        lines: List of Line objects with text, point_size, leading_ratio, and font_family.
        context: Rendering context with font configuration.
        max_width: Maximum width constraint (post-margin).
        max_height: Maximum height constraint (post-margin).
        min_horizontal_scale: Minimum allowed horizontal scale (default: 0.7 = 70%).
        split_max: Maximum times a line can be split (default: 1 = max 2 lines per input line).
        size_reduction_ratio: Multiplicative factor for reducing font size each iteration (default: 0.984375).
        min_point_size: Minimum point size allowed (default: 6.0).

    Returns:
        List of fitted Line objects with final text, point_size, leading_ratio, font_family, and horizontal_scale.
    """
    # Make copies of input lines to avoid mutating originals
    current_lines = [copy.copy(line) for line in lines]

    while True:
        # Process lines at current sizes
        processed_lines = _process_lines_at_current_size(
            canvas, current_lines, context, max_width,
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
        size_changed = False
        for line in current_lines:
            if not line.fixed_size:
                line.point_size *= size_reduction_ratio
                size_changed = True

        # If all lines are fixed_size, we can't reduce further
        if not size_changed:
            return processed_lines
