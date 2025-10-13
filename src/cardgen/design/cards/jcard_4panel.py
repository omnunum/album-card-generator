"""4-panel cassette j-card layout implementation."""

from cardgen.api.models import Album
from cardgen.design.base import Card, CardSection, Theme
from cardgen.design.sections import CoverSection, MetadataSection, SpineSection, TracklistSection
from cardgen.utils.dimensions import (
    JCARD_BACK_WIDTH,
    JCARD_PANEL_WIDTH,
    JCARD_SPINE_WIDTH,
    Dimensions,
    get_jcard_4_panel_dimensions,
    get_panel_dimensions,
)
from cardgen.utils.tape import split_tracks_by_tape_sides


class JCard4Panel(Card):
    """
    4-panel cassette j-card layout.

    Layout (left to right): Back | Spine | Front | Inside
    When folded, back wraps around outside back, front is on outside front, inside opens to the right.
    """

    def __init__(self, album: Album, theme: Theme, tape_length_minutes: int = 90) -> None:
        """
        Initialize 4-panel j-card.

        Args:
            album: Album data to display.
            theme: Theme for styling.
            tape_length_minutes: Length of cassette tape in minutes (default: 90 for C90).
        """
        super().__init__(album, theme, tape_length_minutes)
        self.panels = get_panel_dimensions()

        # Split tracks into tape sides
        self.side_a, self.side_b = split_tracks_by_tape_sides(album.tracks, tape_length_minutes)

    def get_dimensions(self) -> Dimensions:
        """
        Get overall card dimensions.

        Returns:
            Dimensions object for entire card.
        """
        return get_jcard_4_panel_dimensions()

    def get_sections(self) -> list[CardSection]:
        """
        Get all sections that make up this card.

        Returns:
            List of CardSection objects with content specifications.
        """
        sections: list[CardSection] = []

        # Inside panel - Track listing with sides
        sections.append(
            TracklistSection(
                name="inside",
                dimensions=self.panels["inside"],
                side_a=self.side_a,
                side_b=self.side_b,
                title="Tracklist",
            )
        )

        # Back panel - Metadata (genres, label)
        metadata_items: list[str] = []
        if self.album.genre:
            metadata_items.append(f"Genre: {self.album.genre}")
        if self.album.label:
            metadata_items.append(f"Label: {self.album.label}")
        if self.album.year:
            metadata_items.append(f"Year: {self.album.year}")

        # Add total duration
        metadata_items.append(f"Duration: {self.album.format_total_duration()}")

        sections.append(
            MetadataSection(
                name="back",
                dimensions=self.panels["back"],
                items=metadata_items,
            )
        )

        # Spine panel - Artist, Title, Year (vertical text)
        spine_text: list[str] = []
        spine_text.append(self.album.artist)
        spine_text.append(self.album.title)
        if self.album.year:
            spine_text.append(str(self.album.year))

        sections.append(
            SpineSection(
                name="spine",
                dimensions=self.panels["spine"],
                text_lines=spine_text,
            )
        )

        # Front panel - Album art, Title, Artist
        sections.append(
            CoverSection(
                name="front",
                dimensions=self.panels["front"],
                cover_art=self.album.cover_art,
                title=self.album.title,
                artist=self.album.artist,
            )
        )

        return sections

    def get_fold_lines(self) -> list[float]:
        """
        Get x-coordinates of fold lines (in inches from left edge).

        Returns:
            List of x-coordinates for fold lines.
        """
        # Fold lines between each panel
        # Back (1.0") | Spine (0.5") | Front (2.5") | Inside (2.5")
        return [
            JCARD_BACK_WIDTH,  # Between back and spine
            JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH,  # Between spine and front
            JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH,  # Between front and inside
        ]
