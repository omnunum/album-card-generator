"""Tracklist section implementation."""

from dataclasses import dataclass
from typing import Optional

from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen.canvas import Canvas

from cardgen.api.models import Track
from cardgen.design.base import CardSection, RendererContext
from cardgen.utils.dimensions import Dimensions, inches_to_points
from cardgen.utils.text import fit_text_block, Line, measure_text_height, calculate_line_advancement
from cardgen.fonts import resolve_font


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
        min_track_title_char_spacing: float = -1.0,
        use_tape_flip_offset: bool = True,
        header_padding: float = 1/32,
        header_leading_ratio: float = 1/8,
        track_leading_ratio: float = 0.35,
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
            min_track_title_char_spacing: Minimum character spacing for track titles (negative = compressed).
            use_tape_flip_offset: Whether to offset Side B minimap by Side A unused space (for tape flip logic).
            header_leading_ratio: Leading ratio for Side A/B headers (default: 0.44).
                                 Updated from 0.33 to account for canonical formula using adjusted_point_size.
            track_leading_ratio: Leading ratio for track lines (default: 0.23).
                                Updated from 0.17 to account for canonical formula using adjusted_point_size.
            header_padding: Extra padding in inches before Side A and Side B headers (default: 1/16).
        """
        super().__init__(name, dimensions)
        self.tracks = tracks
        self.side_capacity = side_capacity
        self.title = title
        self.track_title_overflow = track_title_overflow
        self.min_track_title_char_spacing = min_track_title_char_spacing
        self.use_tape_flip_offset = use_tape_flip_offset
        self.header_leading_ratio = header_leading_ratio
        self.track_leading_ratio = track_leading_ratio
        self.header_padding = header_padding

    def render(self, context: RendererContext) -> None:
        """Render track listing with Side A/B and duration minimap."""
        c = context.canvas

        c.setFillColor(Color(*context.theme.effective_text_color))

        # Title
        tracklist_title_font_size = 18
        title_font = resolve_font(f"{context.theme.font_family}-bold")
        c.setFont(title_font, tracklist_title_font_size)
        title_y = (
            context.y # location of the bottom of the card within the page
            + context.height # start at the top of the card
            - context.padding # go down the size of the padding
            - measure_text_height(self.title, title_font, tracklist_title_font_size) # go down the size of the title text
        )
        # text will draw "above" where our text_y line is
        c.drawString(context.x + context.padding, title_y, self.title)

        # Calculate available space left for the rest of the text
        # Account for header_padding that will be applied before each side header during rendering
        num_sides = len(set(t.side for t in self.tracks))  # Count unique sides
        header_padding_points = inches_to_points(self.header_padding)

        available_height = (
            title_y
            - context.y
            - context.padding
            - (num_sides * header_padding_points)  # Subtract padding for each side header
        )
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
            - (tracklist_title_font_size * 0.2) # go down portion of the title text for a text-to-text buffer
            - fitted_lines[0].adjusted_point_size # go down the size of our first line
        )

        # Calculate Side A unused space for Side B offset (if using tape flip logic)
        side_a_unused_duration = 0.0
        if self.use_tape_flip_offset:
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
                point_size=context.theme.subtitle_font_size,
                leading_ratio=self.header_leading_ratio,
                fixed_size=True,  # Never reduce this during iterations
                font_family=f"{context.theme.font_family}-Bold"
            ))

            # Side A tracks (normal text that can be reduced)
            for track in [t for t in self.tracks if t.side == "A"]:
                lines.append(Line(
                    text=track.title,
                    point_size=context.theme.track_font_size,
                    leading_ratio=self.track_leading_ratio,
                    track=track,  # Reference to original track
                    font_family=context.theme.font_family,
                    prefix=f"{track.track_number:2d}. ",
                    suffix=f" {track.format_duration()}"
                ))

        # Side B header (fixed)
        if any(t.side == "B" for t in self.tracks):
            lines.append(Line(
                text="Side B",
                point_size=context.theme.subtitle_font_size,
                leading_ratio=self.header_leading_ratio,
                fixed_size=True,  # Never reduce this during iterations
                font_family=f"{context.theme.font_family}-Bold"
            ))

            # Side B tracks (normal text that can be reduced)
            for track in [t for t in self.tracks if t.side == "B"]:
                lines.append(Line(
                    text=track.title,
                    point_size=context.theme.track_font_size,
                    leading_ratio=self.track_leading_ratio,
                    track=track,  # Reference to original track
                    font_family=context.theme.font_family,
                    prefix=f"{track.track_number:2d}. ",
                    suffix=f" {track.format_duration()}"
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

        # Track which (side, track_number) pairs we've rendered the first line for
        tracks_first_line_rendered: set[tuple[str | None, int]] = set()

        for i, fitted_line in enumerate(fitted_lines):
            # Determine line type
            is_header = fitted_line.text in ["Side A", "Side B"]
            is_first_line_of_track = fitted_line.track is not None and (fitted_line.track.side, fitted_line.track.track_number) not in tracks_first_line_rendered

            if is_header:
                # Use actual measured text height for better visual alignment
                visible_point_size = fitted_line.adjusted_point_size

                # Render side header with minimap
                side_letter = fitted_line.text[-1]  # "A" or "B"
                side_tracks = [t for t in self.tracks if t.side == side_letter]
                unused_offset = side_a_unused_duration if side_letter == "B" else 0

                # Add extra padding before both Side A and Side B headers
                header_padding_points = inches_to_points(self.header_padding)
                if side_letter == "A":
                    # For Side A, just add the header padding
                    text_y -= header_padding_points
                elif side_letter == "B":
                    # For Side B, we need to un-offset the smaller amount and then re-offset
                    # the larger amount (to fix overdraw), plus add extra padding
                    text_y = (
                        text_y
                        + fitted_lines[i-1].adjusted_point_size
                        - fitted_line.adjusted_point_size
                        - header_padding_points
                    )
                c.setFillColor(Color(*context.theme.effective_text_color))
                c.setFont(f"{context.theme.font_family}-Bold", fitted_line.point_size)
                c.drawString(context.x + context.padding, text_y, fitted_line.text)

                # Draw minimap to the right of label
                label_width = c.stringWidth(fitted_line.text, f"{context.theme.font_family}-Bold", fitted_line.point_size)
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

                text_y -= calculate_line_advancement(fitted_line)

            else:
                # Render track line (first line or continuation)
                track = fitted_line.track
                if track is None:
                    continue

                # Determine prefix and suffix for this line
                if is_first_line_of_track:
                    # First line: use track number and duration
                    prefix = fitted_line.prefix
                    suffix = fitted_line.suffix
                    tracks_first_line_rendered.add((track.side, track.track_number))
                else:
                    # Continuation line: use indent, no duration
                    prefix = "    "
                    suffix = ""

                # Get fonts
                prefix_font = fitted_line.prefix_font or context.theme.monospace_family
                suffix_font = fitted_line.suffix_font or context.theme.monospace_family

                # Calculate widths
                prefix_width = c.stringWidth(prefix, prefix_font, fitted_line.point_size) if prefix else 0
                suffix_width = c.stringWidth(suffix, suffix_font, fitted_line.point_size) if suffix else 0

                c.setFillColor(Color(*context.theme.effective_text_color))

                # Draw prefix
                if prefix:
                    c.setFont(prefix_font, fitted_line.point_size)
                    c.drawString(context.x + context.padding, text_y, prefix)

                # Draw track title with horizontal scaling
                c.setFont(context.theme.font_family, fitted_line.point_size)
                
                c.saveState()
                title_x = context.x + context.padding + prefix_width
                c.translate(title_x, text_y)
                c.scale(fitted_line.horizontal_scale, 1.0)
                c.drawString(0, 0, fitted_line.text)
                c.restoreState()

                # Draw suffix (duration) - right-aligned
                if suffix:
                    suffix_x = context.x + context.padding + text_width - suffix_width
                    c.setFont(suffix_font, fitted_line.point_size)
                    c.drawString(suffix_x, text_y, suffix)

                text_y -= calculate_line_advancement(fitted_line)

        return text_y

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
        c.setStrokeColor(Color(*context.theme.effective_text_color))
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
                c.setFillColor(Color(*context.theme.effective_accent_color))
                c.rect(current_x, y - height, segment_width, height, fill=1, stroke=0)

                # Draw track number
                if segment.track_number is not None and segment_width > 5:
                    c.setFillColor(Color(*context.theme.background_color))
                    c.setFont(context.theme.monospace_family_bold, track_font_size)
                    track_num_str = str(segment.track_number)
                    track_num_width = c.stringWidth(
                        track_num_str, context.theme.monospace_family_bold, track_font_size
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
                            last_digit_str, context.theme.monospace_family_bold, track_font_size
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
                c.setStrokeColor(Color(*context.theme.background_color))
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

