"""Tracklist section implementation."""

from dataclasses import dataclass
from typing import Optional

from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen.canvas import Canvas

from cardgen.api.models import Track
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions
from cardgen.utils.tape import TapeSide
from cardgen.utils.text import calculate_text_width, fit_text_two_lines, fit_text_block, Line


@dataclass
class MinimapSegment:
    """A segment in the minimap (track or empty space)."""
    duration: float  # Duration in seconds
    track_number: Optional[int] = None  # None for empty space
    is_hatched: bool = False  # True for empty/unused space


class TracklistSection(CardSection):
    """Tracklist section with Side A/B and duration minimap."""

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        tracks: list[Track],
        side_capacity: int,
        title: str = "Tracklist",
        track_title_overflow: str = "truncate",
        min_char_spacing: float = -1.0,
    ) -> None:
        """
        Initialize tracklist section.

        Args:
            name: Section name.
            dimensions: Section dimensions.
            tracks: List of tracks with .side attribute assigned ("A" or "B").
            side_capacity: Maximum duration per side in seconds.
            title: Section title.
            track_title_overflow: How to handle long track titles ("truncate" or "wrap").
            min_char_spacing: Minimum character spacing for track titles (negative = compressed).
        """
        super().__init__(name, dimensions)
        self.tracks = tracks
        self.side_capacity = side_capacity
        self.title = title
        self.track_title_overflow = track_title_overflow
        self.min_char_spacing = min_char_spacing

    def render(self, context: RendererContext) -> None:
        """Render track listing with Side A/B and duration minimap."""
        c = context.canvas

        c.setFillColor(Color(*context.color_scheme.text))

        # Title
        c.setFont(
            f"{context.font_config.family}-Bold", context.font_config.title_size
        )
        title_y = (
            context.y # location of the bottom of the card within the page
            + context.height # start at the top of the card
            - context.padding # go down the size of the padding
            - context.font_config.title_size # go down the size of the title text
        )
        # text will draw "above" where our text_y line is
        c.drawString(context.x + context.padding, title_y, self.title)

        # Calculate available space left for the rest of the text
        available_height = title_y - context.y - context.padding
        text_width = context.width - (context.padding * 2)

        # Build Line objects for all content
        lines = self._build_text_lines(context)

        # Fit all text within constraints
        fitted_lines = fit_text_block(
            c, lines, context,
            max_width=text_width,
            max_height=available_height,
            min_horizontal_scale=0.7,
            split_max=1,
            min_point_size=4.0
        )

        # Render fitted lines
        text_y = (
            title_y # start at the bottom of the title
            - (context.font_config.title_size * 0.2) # go down portion of the title text for a text-to-text buffer
            - fitted_lines[0].point_size # go down the size of our first line
        )

        # Calculate Side A unused space for Side B offset
        side_a_tracks = [t for t in self.tracks if t.side == "A"]
        total_side_a_duration = sum(t.duration for t in side_a_tracks)
        side_a_unused_duration = self.side_capacity - total_side_a_duration

        text_y = self._render_fitted_lines(
            context, fitted_lines, text_y, text_width,
            side_a_unused_duration
        )

    def _build_text_lines(self, context: RendererContext) -> list[Line]:
        """
        Build Line objects for all tracklist content.

        Args:
            context: Rendering context with font configuration.

        Returns:
            List of Line objects representing all text that needs to be fitted.
        """
        lines: list[Line] = []

        # Side A header (fixed)
        if any(t.side == "A" for t in self.tracks):
            lines.append(Line(
                text="Side A",
                point_size=context.font_config.subtitle_size,
                leading_ratio=(1/16),  # Spacing after header
                fixed_size=True  # Never reduce this during iterations
            ))

            # Side A tracks (normal text that can be reduced)
            for track in [t for t in self.tracks if t.side == "A"]:
                lines.append(Line(
                    text=track.title,
                    point_size=context.font_config.track_size,
                    leading_ratio=(1/8),  # Spacing between tracks
                    track=track  # Reference to original track
                ))

        # Side B header (fixed)
        if any(t.side == "B" for t in self.tracks):
            lines.append(Line(
                text="Side B",
                point_size=context.font_config.subtitle_size,
                leading_ratio=(1/16),  # Spacing after header
                fixed_size=True  # Never reduce this during iterations
            ))

            # Side B tracks (normal text that can be reduced)
            for track in [t for t in self.tracks if t.side == "B"]:
                lines.append(Line(
                    text=track.title,
                    point_size=context.font_config.track_size,
                    leading_ratio=(1/8),  # Spacing between tracks
                    track=track  # Reference to original track
                ))

        return lines

    def _render_fitted_lines(
        self,
        context: RendererContext,
        fitted_lines: list[Line],
        start_y: float,
        text_width: float,
        side_a_unused_duration: float
    ) -> float:
        """
        Render fitted text lines with track numbers, durations, and minimaps.

        Args:
            context: Rendering context.
            fitted_lines: Fitted Line objects from fit_text_block.
            start_y: Starting y position.
            text_width: Available text width.
            side_a_unused_duration: Unused duration on Side A for tape flip logic.

        Returns:
            Final y position after rendering.
        """
        c = context.canvas
        text_y = start_y

        # Track which track numbers we've rendered the first line for
        track_numbers_first_line_rendered: set[int] = set()

        for i, fitted_line in enumerate(fitted_lines):
            # Determine line type
            is_header = fitted_line.text in ["Side A", "Side B"]
            is_first_line_of_track = fitted_line.track is not None and fitted_line.track.track_number not in track_numbers_first_line_rendered
            is_continuation_line = fitted_line.track is not None and fitted_line.track.track_number in track_numbers_first_line_rendered

            if is_header:
                 # The text bounding box extends higher than the normal text in order to fig ligatures and accents
                #   which leaves empty space.  Since we don't ever fill that space, we consider only about 80%
                #   of that space used.
                visible_text_ratio = 0.75
                visible_point_size = fitted_line.point_size * visible_text_ratio

                # Render side header with minimap
                side_letter = fitted_line.text[-1]  # "A" or "B"
                side_tracks = [t for t in self.tracks if t.side == side_letter]
                unused_offset = side_a_unused_duration if side_letter == "B" else 0
                # when we get to B our text_y (the bottom of where we draw up from) is only offset
                #   based on the small text point size, but we draw a subtitle point size up, which 
                #   causes overdraw.  We need to un-offset the smaller amount and then re-offset 
                #   the larger amount
                if side_letter == "B":
                    text_y = (
                        text_y 
                        - fitted_lines[i-1].point_size 
                        + visible_text_ratio 
                    )
                c.setFillColor(Color(*context.color_scheme.text))
                c.setFont(f"{context.font_config.family}-Bold", fitted_line.point_size)
                c.drawString(context.x + context.padding, text_y, fitted_line.text)

                # Draw minimap to the right of label
                label_width = c.stringWidth(fitted_line.text, f"{context.font_config.family}-Bold", fitted_line.point_size)
                minimap_left_margin = visible_point_size
                minimap_start_x = context.x + context.padding + label_width + minimap_left_margin
                minimap_available_width = text_width - label_width - minimap_left_margin
               
                text_centerline = text_y + (visible_point_size * 0.5) 
                # Calculate minimap height as 80% of subtitle size for better visual alignment
                minimap_top_y = text_centerline + visible_point_size / 2

                self._draw_minimap_for_tracks(
                    context, side_tracks, self.side_capacity,
                    minimap_start_x, minimap_top_y,
                    minimap_available_width, visible_point_size,
                    unused_offset
                )

                text_y -= visible_point_size + (visible_point_size * fitted_line.leading_ratio)

            elif is_first_line_of_track:
                # Render track (first line)
                track = fitted_line.track
                if track is None:
                    continue
                track_num_text = f"{track.track_number:2d}."
                duration_text = track.format_duration()

                # Calculate widths
                track_num_width = c.stringWidth(track_num_text, context.font_config.monospace_family, fitted_line.point_size)
                helvetica_space_width = c.stringWidth(" ", context.font_config.family, fitted_line.point_size)
                duration_width = c.stringWidth(duration_text, context.font_config.monospace_family, fitted_line.point_size)
                c.setFillColor(Color(*context.color_scheme.text))
                # Draw track number
                c.setFont(context.font_config.monospace_family, fitted_line.point_size)
                c.drawString(context.x + context.padding, text_y, track_num_text)

                # Draw space
                c.setFont(context.font_config.family, fitted_line.point_size)
                c.drawString(context.x + context.padding + track_num_width, text_y, " ")

                # Draw track title with horizontal scaling
                c.saveState()

                # Apply horizontal scaling
                if fitted_line.horizontal_scale < 1.0:
                    title_x = context.x + context.padding + track_num_width + helvetica_space_width
                    c.translate(title_x, text_y)
                    c.scale(fitted_line.horizontal_scale, 1.0)
                    c.drawString(0, 0, fitted_line.text)
                else:
                    c.drawString(
                        context.x + context.padding + track_num_width + helvetica_space_width,
                        text_y,
                        fitted_line.text
                    )
                c.restoreState()

                # Draw duration
                duration_x = context.x + context.padding + text_width - duration_width
                c.setFont(context.font_config.monospace_family, fitted_line.point_size)
                c.drawString(duration_x, text_y, duration_text)

                # Mark this track as having its first line rendered
                track_numbers_first_line_rendered.add(track.track_number)

                text_y -= fitted_line.point_size + (fitted_line.point_size * fitted_line.leading_ratio)

            elif is_continuation_line:
                # Render continuation line (indented)
                indent_width = c.stringWidth("    ", context.font_config.monospace_family, fitted_line.point_size)

                # Draw indent
                c.setFont(context.font_config.monospace_family, fitted_line.point_size)
                c.drawString(context.x + context.padding, text_y, "    ")

                # Draw continuation text with horizontal scaling
                c.saveState()
                c.setFillColor(Color(*context.color_scheme.text))
                c.setFont(context.font_config.family, fitted_line.point_size)

                if fitted_line.horizontal_scale < 1.0:
                    title_x = context.x + context.padding + indent_width
                    c.translate(title_x, text_y)
                    c.scale(fitted_line.horizontal_scale, 1.0)
                    c.drawString(0, 0, fitted_line.text)
                else:
                    c.drawString(
                        context.x + context.padding + indent_width,
                        text_y,
                        fitted_line.text
                    )
                c.restoreState()

                text_y -= fitted_line.point_size + (fitted_line.point_size * fitted_line.leading_ratio)

        return text_y

    def _render_tape_side(
        self,
        context: RendererContext,
        tape_side: TapeSide,
        label: str,
        text_y: float,
        text_width: float,
        minimap_x: float,
        minimap_y: float,
        minimap_width: float,
        minimap_height: float,
        unused_duration_offset: float = 0,
        track_size: float = 10,
        line_spacing: float = 3,
        minimap_gap: float = 4,
    ) -> float:
        """
        Render a single tape side (A or B) with tracks and horizontal minimap.

        Args:
            context: Rendering context.
            tape_side: Tape side to render.
            label: Label to display ("Side A" or "Side B").
            text_y: Current y position for text.
            text_width: Available width for track text.
            minimap_x: Unused (kept for compatibility).
            minimap_y: Unused (kept for compatibility).
            minimap_width: Unused (kept for compatibility).
            minimap_height: Height of minimap bar.
            unused_duration_offset: Duration offset for Side B tape flip logic.
            track_size: Font size for tracks.
            line_spacing: Line spacing between tracks.
            minimap_gap: Unused (minimap is inline with label).

        Returns:
            Updated text_y position after rendering.
        """
        c = context.canvas

        # Ensure text color is set (fixes white text bug for Side B)
        c.setFillColor(Color(*context.color_scheme.text))

        # Side header
        c.setFont(f"{context.font_config.family}-Bold", track_size)
        c.drawString(context.x + context.padding, text_y, label)

        # Draw horizontal minimap to the right of the side label (on the same line)
        # Position minimap starting after the label text
        label_width = c.stringWidth(label, f"{context.font_config.family}-Bold", track_size)
        minimap_left_margin = 12  # Gap between label and minimap
        minimap_start_x = context.x + context.padding + label_width + minimap_left_margin
        minimap_available_width = text_width - label_width - minimap_left_margin

        # Align minimap centerline with label text centerline
        # Text baseline is at text_y, text height is track_size
        # Text center is approximately at: text_y + track_size / 2 (accounting for descenders)
        # For better visual alignment, use text_y + track_size * 0.35 as the centerline
        text_centerline = text_y + track_size * 0.35
        # Minimap center should align with text center
        # minimap_top_y - minimap_height/2 = text_centerline
        minimap_top_y = text_centerline + minimap_height / 2

        self._draw_minimap(
            context,
            tape_side,
            minimap_start_x,
            minimap_top_y,
            minimap_available_width,
            minimap_height,
            unused_duration_offset,
        )

        text_y -= track_size + line_spacing

        # Move down after the side header (no extra space needed for minimap since it's inline)
        # text_y is already positioned for next line

        # Ensure text color is reset after minimap drawing
        c.setFillColor(Color(*context.color_scheme.text))

        # Side tracks
        # Compress word spacing by 40% to fit more text
        word_spacing = -0.4 * (c.stringWidth(" ", context.font_config.family, track_size))

        for track in tape_side.tracks:
            # Format track number as right-aligned (e.g., ' 9' or '10')
            # Split into number+period (monospace) and space (Helvetica for narrower spacing)
            track_num_text = f"{track.track_number:2d}."
            track_title_text = track.title
            duration_text = track.format_duration()

            # Calculate duration width (using monospace font)
            duration_width = c.stringWidth(
                duration_text,
                context.font_config.monospace_family,
                track_size,
            )
            # No word spacing needed for duration (monospace, no spaces)
            duration_x = context.x + context.padding + text_width - duration_width

            # Calculate available width for track text (leave gap before duration)
            gap_before_duration = 3  # points - small gap between title and duration
            available_track_width = duration_x - (context.x + context.padding) - gap_before_duration

            # Calculate widths for track number (monospace) + Helvetica space
            track_num_width = c.stringWidth(track_num_text, context.font_config.monospace_family, track_size)
            helvetica_space_width = c.stringWidth(" ", context.font_config.family, track_size)
            total_track_num_width = track_num_width + helvetica_space_width

            # Calculate available widths for line 1 and line 2
            line1_available_width = available_track_width - total_track_num_width
            # Line 2: 4 monospace spaces (indent) to right padding
            indent_width = c.stringWidth("    ", context.font_config.monospace_family, track_size)
            line2_available_width = text_width - indent_width

            # Use adaptive fitting algorithm
            fit_result = fit_text_two_lines(
                c, track_title_text,
                line1_available_width, line2_available_width,
                context.font_config.family, track_size, word_spacing, self.min_char_spacing
            )
            line1_text = fit_result['line1']
            line2_text = fit_result['line2']
            char_spacing = fit_result['line1_char_spacing']
            line2_char_spacing = fit_result['line2_char_spacing']

            # Draw track number in monospace (without space)
            c.setFont(context.font_config.monospace_family, track_size)
            c.drawString(context.x + context.padding, text_y, track_num_text)

            # Draw Helvetica space after track number
            c.setFont(context.font_config.family, track_size)
            c.drawString(context.x + context.padding + track_num_width, text_y, " ")

            # Draw first line with character spacing (after the Helvetica space)
            c.drawString(
                context.x + context.padding + total_track_num_width, text_y, line1_text,
                wordSpace=word_spacing, charSpace=char_spacing
            )

            # Draw duration in monospace font (only on first line)
            c.setFont(context.font_config.monospace_family, track_size)
            c.drawString(duration_x, text_y, duration_text)

            # Draw second line if it exists
            if line2_text:
                text_y -= track_size + line_spacing

                # Draw 4 monospace spaces for indent
                monospace_indent = "    "
                c.setFont(context.font_config.monospace_family, track_size)
                c.drawString(context.x + context.padding, text_y, monospace_indent)

                # Draw line 2 text after the monospace indent
                c.setFont(context.font_config.family, track_size)
                c.drawString(
                    context.x + context.padding + indent_width, text_y, line2_text,
                    wordSpace=word_spacing, charSpace=line2_char_spacing
                )

            text_y -= track_size + line_spacing

        return text_y

    def _calculate_required_height(
        self, context: RendererContext, font_size: float, line_spacing: float
    ) -> float:
        """
        Calculate the total height required to render all tracks at a given font size.

        This simulates the rendering process to determine how many lines each track
        will actually use (accounting for wrapping).

        Args:
            context: Rendering context.
            font_size: Font size to test.
            line_spacing: Line spacing to use.

        Returns:
            Total height in points required for all tracks.
        """
        c = context.canvas
        text_width = context.width - (context.padding * 2)
        word_spacing = -0.4 * (c.stringWidth(" ", context.font_config.family, font_size))

        total_height = 0.0

        # Add Side A header
        if self.side_a and self.side_a.tracks:
            total_height += font_size + line_spacing  # Side A header

            # Check each track
            for track in self.side_a.tracks:
                # Calculate available widths (same as in _render_tape_side)
                track_num_text = f"{track.track_number:2d}."
                duration_text = track.format_duration()

                track_num_width = c.stringWidth(track_num_text, context.font_config.monospace_family, font_size)
                helvetica_space_width = c.stringWidth(" ", context.font_config.family, font_size)
                total_track_num_width = track_num_width + helvetica_space_width

                duration_width = c.stringWidth(duration_text, context.font_config.monospace_family, font_size)
                gap_before_duration = 3
                available_track_width = text_width - duration_width - gap_before_duration

                line1_available_width = available_track_width - total_track_num_width
                indent_width = c.stringWidth("    ", context.font_config.monospace_family, font_size)
                line2_available_width = text_width - indent_width

                # Use fit_text_two_lines to check if it wraps
                fit_result = fit_text_two_lines(
                    c, track.title,
                    line1_available_width, line2_available_width,
                    context.font_config.family, font_size, word_spacing, self.min_char_spacing
                )

                # Count lines used by this track
                if fit_result['line2']:
                    # Wrapped to 2 lines
                    total_height += (font_size + line_spacing) * 2
                else:
                    # Single line
                    total_height += font_size + line_spacing

        # Add gap between sides
        if self.side_a and self.side_a.tracks and self.side_b and self.side_b.tracks:
            total_height += line_spacing

        # Add Side B header and tracks
        if self.side_b and self.side_b.tracks:
            total_height += font_size + line_spacing  # Side B header

            for track in self.side_b.tracks:
                # Same calculation as Side A
                track_num_text = f"{track.track_number:2d}."
                duration_text = track.format_duration()

                track_num_width = c.stringWidth(track_num_text, context.font_config.monospace_family, font_size)
                helvetica_space_width = c.stringWidth(" ", context.font_config.family, font_size)
                total_track_num_width = track_num_width + helvetica_space_width

                duration_width = c.stringWidth(duration_text, context.font_config.monospace_family, font_size)
                gap_before_duration = 3
                available_track_width = text_width - duration_width - gap_before_duration

                line1_available_width = available_track_width - total_track_num_width
                indent_width = c.stringWidth("    ", context.font_config.monospace_family, font_size)
                line2_available_width = text_width - indent_width

                fit_result = fit_text_two_lines(
                    c, track.title,
                    line1_available_width, line2_available_width,
                    context.font_config.family, font_size, word_spacing, self.min_char_spacing
                )

                if fit_result['line2']:
                    total_height += (font_size + line_spacing) * 2
                else:
                    total_height += font_size + line_spacing

        return total_height

    def _calculate_optimal_line_size(
        self, available_height: float, total_lines: int
    ) -> tuple[float, float]:
        """
        Calculate optimal font size and line spacing to fill available vertical space.

        Args:
            available_height: Available vertical space.
            total_lines: Total number of lines (tracks + headers).

        Returns:
            Tuple of (font_size, line_spacing).
        """
        min_size = 6
        max_size = 12

        # Try each font size from largest to smallest
        for size in range(int(max_size), int(min_size) - 1, -1):
            # Calculate spacing needed to fill the space
            # available = total_lines * (size + spacing)
            spacing = (available_height / total_lines) - size

            # Spacing should be reasonable (at least 2pt, at most 10pt)
            if spacing >= 2 and spacing <= 10:
                return (float(size), spacing)

        # Fallback: use minimum size with whatever spacing fits
        spacing = max(2.0, (available_height / total_lines) - min_size)
        return (float(min_size), spacing)

    def _calculate_track_font_size(
        self, available_height: float, total_tracks: int, num_headers: int, overhead: float
    ) -> float:
        """
        Calculate optimal track font size to fit all tracks in available space.

        Args:
            available_height: Available vertical space for tracks.
            total_tracks: Total number of tracks across both sides.
            num_headers: Number of side headers (1 or 2).
            overhead: Fixed overhead from spacing and headers.

        Returns:
            Optimal font size in points.
        """
        min_size = 6
        max_size = 12

        # Formula: height = tracks*(size+3) + headers*(size+4) + gap_between_sides
        # Each track uses: size + 3pt spacing
        # Each header uses: size + 4pt spacing
        for size in range(int(max_size), int(min_size) - 1, -1):
            track_space = total_tracks * (size + 3)
            header_space = num_headers * (size + 4)
            required_height = track_space + header_space + overhead

            if required_height <= available_height:
                return float(size)

        return float(min_size)

    def _build_minimap_segments(
        self, tape_side: TapeSide, unused_duration_offset: float = 0
    ) -> list[MinimapSegment]:
        """Build list of segments for minimap rendering."""
        segments = []

        # Add leading unused space (for Side B - tape flip logic)
        if unused_duration_offset > 0:
            segments.append(
                MinimapSegment(duration=unused_duration_offset, is_hatched=True)
            )

        # Add track segments
        for track in tape_side.tracks:
            segments.append(
                MinimapSegment(duration=track.duration, track_number=track.track_number)
            )

        # Add trailing unused space
        # Total duration = offset (if Side B) + tracks + trailing
        total_track_duration = sum(track.duration for track in tape_side.tracks)
        total_used_duration = unused_duration_offset + total_track_duration
        trailing_unused = tape_side.max_duration - total_used_duration
        if trailing_unused > 0:
            segments.append(MinimapSegment(duration=trailing_unused, is_hatched=True))

        return segments

    def _draw_minimap_for_tracks(
        self,
        context: RendererContext,
        tracks: list[Track],
        max_duration: int,
        x: float,
        y: float,
        width: float,
        height: float,
        unused_duration_offset: float = 0,
    ) -> None:
        """Draw a horizontal visual minimap of track durations."""
        if not tracks or max_duration == 0:
            return

        c = context.canvas

        # Draw border
        c.setStrokeColor(Color(*context.color_scheme.text))
        c.setLineWidth(0.5)
        c.rect(x, y - height, width, height, fill=0)

        # Build segments
        segments: list[MinimapSegment] = []

        # Add leading unused space (for Side B - tape flip logic)
        if unused_duration_offset > 0:
            segments.append(MinimapSegment(duration=unused_duration_offset, is_hatched=True))

        # Add track segments
        for track in tracks:
            segments.append(MinimapSegment(duration=track.duration, track_number=track.track_number))

        # Add trailing unused space
        total_track_duration = sum(track.duration for track in tracks)
        total_used_duration = unused_duration_offset + total_track_duration
        trailing_unused = max_duration - total_used_duration
        if trailing_unused > 0:
            segments.append(MinimapSegment(duration=trailing_unused, is_hatched=True))

        # Render each segment horizontally (left-to-right)
        current_x = x
        track_font_size = 7

        for i, segment in enumerate(segments):
            # Calculate width proportional to duration
            segment_proportion = segment.duration / max_duration
            segment_width = width * segment_proportion

            if segment.is_hatched:
                # Draw cross-hatched pattern for empty space
                self._draw_hatched_rect(c, current_x, y - height, segment_width, height)
            else:
                # Draw filled rectangle for track
                c.setFillColor(Color(*context.color_scheme.accent))
                c.rect(current_x, y - height, segment_width, height, fill=1, stroke=0)

                # Draw track number
                if segment.track_number is not None and segment_width > 5:
                    c.setFillColor(Color(*context.color_scheme.background))
                    c.setFont(f"{context.font_config.monospace_family}-Bold", track_font_size)
                    track_num_str = str(segment.track_number)
                    track_num_width = c.stringWidth(
                        track_num_str, f"{context.font_config.monospace_family}-Bold", track_font_size
                    )

                    # Check if the full track number fits
                    if track_num_width <= segment_width - 2:
                        segment_middle_x = current_x + segment_width / 2
                        text_x = segment_middle_x - track_num_width / 2
                        text_y = y - height / 2 - track_font_size / 3
                        c.drawString(text_x, text_y, track_num_str)
                    else:
                        # Show last digit with underlines for tens place
                        last_digit = segment.track_number % 10
                        tens_digit = segment.track_number // 10
                        last_digit_str = str(last_digit)
                        last_digit_width = c.stringWidth(
                            last_digit_str, f"{context.font_config.monospace_family}-Bold", track_font_size
                        )

                        segment_middle_x = current_x + segment_width / 2
                        text_x = segment_middle_x - last_digit_width / 2
                        text_y = y - height / 2 - track_font_size / 3
                        c.drawString(text_x, text_y, last_digit_str)

                        if tens_digit > 0:
                            underline_y = text_y - 1
                            underline_width = last_digit_width
                            underline_spacing = 1.5

                            for j in range(tens_digit):
                                c.setLineWidth(0.5)
                                c.line(
                                    text_x,
                                    underline_y - (j * underline_spacing),
                                    text_x + underline_width,
                                    underline_y - (j * underline_spacing)
                                )

            # Draw vertical separator line (but not after the last segment)
            current_x += segment_width
            if i < len(segments) - 1:
                c.setStrokeColor(Color(*context.color_scheme.background))
                c.setLineWidth(0.5)
                c.line(current_x, y - height, current_x, y)

    def _draw_minimap(
        self,
        context: RendererContext,
        tape_side: TapeSide,
        x: float,
        y: float,
        width: float,
        height: float,
        unused_duration_offset: float = 0,
    ) -> None:
        """Draw a horizontal visual minimap of track durations for a tape side."""
        if not tape_side.tracks or tape_side.max_duration == 0:
            return

        c = context.canvas

        # Draw border
        c.setStrokeColor(Color(*context.color_scheme.text))
        c.setLineWidth(0.5)
        c.rect(x, y - height, width, height, fill=0)

        # Build segments
        segments = self._build_minimap_segments(tape_side, unused_duration_offset)

        # Render each segment horizontally (left-to-right)
        current_x = x
        track_font_size = 7  # Increased from 6 for better print visibility

        for i, segment in enumerate(segments):
            # Calculate width proportional to duration
            segment_proportion = segment.duration / tape_side.max_duration
            segment_width = width * segment_proportion

            if segment.is_hatched:
                # Draw cross-hatched pattern for empty space
                self._draw_hatched_rect(c, current_x, y - height, segment_width, height)
            else:
                # Draw filled rectangle for track
                c.setFillColor(Color(*context.color_scheme.accent))
                c.rect(current_x, y - height, segment_width, height, fill=1, stroke=0)

                # Draw track number vertically (upright), horizontally centered in segment
                if segment.track_number is not None and segment_width > 5:
                    c.setFillColor(Color(*context.color_scheme.background))
                    # Use bold font for better print visibility
                    c.setFont(f"{context.font_config.monospace_family}-Bold", track_font_size)
                    track_num_str = str(segment.track_number)
                    track_num_width = c.stringWidth(
                        track_num_str, f"{context.font_config.monospace_family}-Bold", track_font_size
                    )

                    # Check if the full track number fits in the segment
                    if track_num_width <= segment_width - 2:  # 2pt padding
                        # Full number fits - draw normally
                        segment_middle_x = current_x + segment_width / 2
                        text_x = segment_middle_x - track_num_width / 2
                        text_y = y - height / 2 - track_font_size / 3  # Vertically center, adjust for baseline
                        c.drawString(text_x, text_y, track_num_str)
                    else:
                        # Not enough space - show last digit with underlines for tens place
                        last_digit = segment.track_number % 10
                        tens_digit = segment.track_number // 10

                        # Draw the last digit
                        last_digit_str = str(last_digit)
                        last_digit_width = c.stringWidth(
                            last_digit_str, f"{context.font_config.monospace_family}-Bold", track_font_size
                        )

                        segment_middle_x = current_x + segment_width / 2
                        text_x = segment_middle_x - last_digit_width / 2
                        text_y = y - height / 2 - track_font_size / 3
                        c.drawString(text_x, text_y, last_digit_str)

                        # Draw underline(s) beneath the digit to represent tens place
                        # Number of underlines = tens digit (1 for 10-19, 2 for 20-29, etc.)
                        if tens_digit > 0:
                            underline_y = text_y - 1  # Position underline just below the digit
                            underline_width = last_digit_width
                            underline_spacing = 1.5  # Spacing between multiple underlines

                            for i in range(tens_digit):
                                c.setLineWidth(0.5)
                                c.line(
                                    text_x,
                                    underline_y - (i * underline_spacing),
                                    text_x + underline_width,
                                    underline_y - (i * underline_spacing)
                                )

            # Draw vertical separator line (but not after the last segment)
            current_x += segment_width
            if i < len(segments) - 1:
                c.setStrokeColor(Color(*context.color_scheme.background))
                c.setLineWidth(0.5)
                c.line(current_x, y - height, current_x, y)

    def _draw_hatched_rect(self, c: Canvas, x: float, y: float, width: float, height: float) -> None:
        """Draw a rectangle with cross-hatch pattern."""
        c.saveState()

        # Draw diagonal hatch lines
        c.setStrokeColor(HexColor(0xcccccc))
        c.setLineWidth(0.25)

        spacing = 2

        # Diagonal lines from bottom-left to top-right
        for i in range(0, int(width + height), spacing):
            x1 = x + i
            y1 = y
            x2 = x
            y2 = y + i

            # Clip to bounds
            if x1 > x + width:
                y1 += (x1 - (x + width))
                x1 = x + width
            if y2 > y + height:
                x2 += (y2 - (y + height))
                y2 = y + height

            c.line(x1, y1, x2, y2)

        # Diagonal lines from top-left to bottom-right (cross-hatch)
        for i in range(0, int(width + height), spacing):
            x1 = x
            y1 = y + height - i
            x2 = x + i
            y2 = y + height

            # Clip to bounds
            if y1 < y:
                x1 += (y - y1)
                y1 = y
            if x2 > x + width:
                y2 -= (x2 - (x + width))
                x2 = x + width

            c.line(x1, y1, x2, y2)

        c.restoreState()

