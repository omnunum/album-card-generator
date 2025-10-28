"""4-panel cassette j-card layout implementation."""

from cardgen.api.models import Album
from cardgen.design.base import Card, CardSection, Theme
from cardgen.design.sections import CoverSection, MetadataSection, SpineSection, TracklistSection
from cardgen.design.sections.descriptors import DescriptorsSection
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import (
    JCARD_BACK_WIDTH,
    JCARD_HEIGHT,
    JCARD_PANEL_WIDTH,
    JCARD_SPINE_WIDTH,
    Dimensions,
    get_jcard_4_panel_dimensions,
    get_panel_dimensions,
)
from cardgen.utils.tape import assign_tape_sides


class JCard4Panel(Card):
    """
    4-panel cassette j-card layout.

    Layout (left to right): Back | Spine | Front | Inside
    When folded, back wraps around outside back, front is on outside front, inside opens to the right.
    """

    def __init__(self, album: Album, theme: Theme, album_art: AlbumArt | None, tape_length_minutes: int = 90) -> None:
        """
        Initialize 4-panel j-card.

        Args:
            album: Album data to display.
            theme: Theme for styling.
            album_art: AlbumArt object for image processing.
            tape_length_minutes: Length of cassette tape in minutes (default: 90 for C90).
        """
        super().__init__(album, theme, tape_length_minutes)
        self.album_art = album_art
        self.panels = get_panel_dimensions()

        # Assign tracks to tape sides (modifies tracks in place)
        self.side_capacity = assign_tape_sides(album.tracks, tape_length_minutes)

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

        # Inside panel - Split vertically: 70% tracklist, 30% descriptors
        inside_panel = self.panels["inside"]

        # Tracklist at top: 70% of height
        tracklist_height = inside_panel.height * 0.7
        tracklist_y = inside_panel.y + (inside_panel.height * 0.3)  # Positioned above descriptors

        sections.append(
            TracklistSection(
                name="inside_tracklist",
                dimensions=Dimensions(
                    width=inside_panel.width,
                    height=tracklist_height,
                    x=inside_panel.x,
                    y=tracklist_y
                ),
                tracks=self.album.tracks,
                side_capacity=self.side_capacity,
                title="Tracklist",
                track_title_overflow=self.theme.get_track_title_overflow(),
                min_char_spacing=self.theme.get_min_track_title_char_spacing(),
            )
        )

        # Descriptors at bottom: 30% of height
        descriptors_height = inside_panel.height * 0.3
        descriptors_y = inside_panel.y  # At bottom of panel

        sections.append(
            DescriptorsSection(
                name="inside_descriptors",
                dimensions=Dimensions(
                    width=inside_panel.width,
                    height=descriptors_height,
                    x=inside_panel.x,
                    y=descriptors_y
                ),
                album=self.album,
                font_size=10.0,
                padding_override=0.125,
            )
        )

        sections.append(
            MetadataSection(
                name="back",
                dimensions=self.panels["back"],
                album=self.album,
                font_size=9.0,  # Increased from 5.0, fits better than 10.0
                padding_override=1/16
            )
        )

        # Spine panel - Artist, Title, Year (vertical text, all bold)
        spine_items: list[str] = []
        spine_items.append(self.album.artist)
        spine_items.append(self.album.title)
        if self.album.year:
            spine_items.append(str(self.album.year))

        sections.append(
            SpineSection(
                name="spine",
                dimensions=self.panels["spine"],
                text_lines=spine_items,
                album_art=self.album_art,
                show_dolby_logo=self.album.show_dolby_logo,
            )
        )

        # Front panel - Album art, Title, Artist
        sections.append(
            CoverSection(
                name="front",
                dimensions=self.panels["front"],
                album_art=self.album_art,
                title=self.album.title,
                artist=self.album.artist,
                show_dolby_logo=self.album.show_dolby_logo,
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
