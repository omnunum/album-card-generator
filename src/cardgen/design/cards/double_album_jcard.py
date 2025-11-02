"""Double album cassette j-card layout implementation."""

from cardgen.api.models import Album
from cardgen.config import Theme
from cardgen.design.base import Card, CardSection
from cardgen.design.sections import CoverSection, MetadataSection, SpineSection, TracklistSection
from cardgen.design.sections.container import ContainerSection
from cardgen.design.sections.descriptors import DescriptorsSection
from cardgen.design.sections.genre_tree import GenreTreeSection
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import (
    JCARD_5_PANEL_HEIGHT,
    JCARD_5_PANEL_WIDTH,
    JCARD_BACK_WIDTH,
    JCARD_HEIGHT,
    JCARD_PANEL_WIDTH,
    JCARD_SPINE_WIDTH,
    Dimensions,
)


class DoubleAlbumJCard(Card):
    """
    5-panel double album cassette j-card layout.

    Layout (left to right): Metadata | Spine | Cover | Tracklist | Genre/Descriptors
    - Metadata and Cover panels: split vertically (top/bottom) for two albums
    - Genre/Descriptors panel: split vertically (top/bottom) for two albums, each album's
      section further split horizontally (left/right) with genre tree on left, descriptors on right

    Visual layout:
    __________
    M    A     G D
       S     T
    M    A     G D
    __________
    """

    def __init__(
        self,
        album1: Album,
        album2: Album,
        theme: Theme,
        album_art1: AlbumArt | None,
        album_art2: AlbumArt | None,
        tape_length_minutes: int = 90
    ) -> None:
        """
        Initialize double album 5-panel j-card.

        Args:
            album1: First album data to display.
            album2: Second album data to display.
            theme: Theme for styling.
            album_art1: AlbumArt object for first album.
            album_art2: AlbumArt object for second album.
            tape_length_minutes: Length of cassette tape in minutes (default: 90 for C90).
        """
        # Store both albums (use album1 as primary for base class)
        # Override theme to use compact mode for double album covers
        compact_theme = theme.model_copy(update={"cover_art_mode": "compact"})
        super().__init__(album1, compact_theme, tape_length_minutes)
        self.album1 = album1
        self.album2 = album2
        self.album_art1 = album_art1
        self.album_art2 = album_art2

        # Manually assign sides based on album (album1 → Side A, album2 → Side B)
        for track in self.album1.tracks:
            track.side = "A"
        for track in self.album2.tracks:
            track.side = "B"

        # Calculate side capacity in seconds (not minutes!)
        self.side_capacity = (tape_length_minutes * 60) // 2

    def get_dimensions(self) -> Dimensions:
        """
        Get overall card dimensions.

        Returns:
            Dimensions object for entire card (same as 5-panel).
        """
        return Dimensions(width=JCARD_5_PANEL_WIDTH, height=JCARD_5_PANEL_HEIGHT)

    def get_sections(self) -> list[CardSection]:
        """
        Get all sections that make up this card.

        Returns:
            List of CardSection objects including containers for split panels.
        """
        sections: list[CardSection] = []

        # Calculate x positions for each panel
        panel_1_x = 0.0  # Metadata (split)
        panel_2_x = JCARD_BACK_WIDTH  # Spine
        panel_3_x = JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH  # Cover (split)
        panel_4_x = JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH  # Tracklist
        panel_5_x = JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH + JCARD_PANEL_WIDTH  # Genre/Descriptors (split)

        # Panel 1: Metadata (vertical split - top: album1, bottom: album2)
        metadata1 = MetadataSection(
            name="metadata_album1",
            dimensions=Dimensions(width=0, height=0, x=0, y=0),  # Will be set by container
            album=self.album1,
            font_size=9.0,
            padding_override=1/32
        )
        metadata2 = MetadataSection(
            name="metadata_album2",
            dimensions=Dimensions(width=0, height=0, x=0, y=0),  # Will be set by container
            album=self.album2,
            font_size=9.0,
            padding_override=1/32
        )
        sections.append(
            ContainerSection(
                name="back",
                dimensions=Dimensions(
                    width=JCARD_BACK_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_1_x,
                    y=0.0
                ),
                children=[metadata2, metadata1],  # Bottom to top (PDF coordinates)
                layout="vertical"
            )
        )

        lines : list[str] = list()
        # Panel 2: Spine (with both albums)
        for album in (self.album1, self.album2):
            lines.append(" • ".join([album.artist, album.title, str(album.year)]))

        sections.append(
            SpineSection(
                name="spine",
                dimensions=Dimensions(
                    width=JCARD_SPINE_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_2_x,
                    y=0.0
                ),
                text_lines=lines,
                album_art_left=self.album_art2,
                album_art_right=self.album_art1,
                show_dolby_logo=(self.album1.show_dolby_logo or self.album2.show_dolby_logo),
            )
        )

        # Panel 3: Cover (vertical split - top: album1, bottom: album2)
        # Use compact mode: art (2") + rotated text (0.5") for full bleed art
        cover1 = CoverSection(
            name="cover_album1",
            dimensions=Dimensions(width=0, height=0, x=0, y=0),  # Will be set by container
            album_art=self.album_art1,
            title=self.album1.title,
            artist=self.album1.artist,
            show_dolby_logo=False,  # Disabled in compact mode (not enough space)
        )
        cover2 = CoverSection(
            name="cover_album2",
            dimensions=Dimensions(width=0, height=0, x=0, y=0),  # Will be set by container
            album_art=self.album_art2,
            title=self.album2.title,
            artist=self.album2.artist,
            show_dolby_logo=False,  # Disabled in compact mode (not enough space)
        )
        sections.append(
            ContainerSection(
                name="front",
                dimensions=Dimensions(
                    width=JCARD_PANEL_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_3_x,
                    y=0.0
                ),
                children=[cover2, cover1],  # Bottom to top (PDF coordinates)
                layout="vertical"
            )
        )

        # Panel 4: Tracklist (combined tracks from both albums)
        combined_tracks = self.album1.tracks + self.album2.tracks
        sections.append(
            TracklistSection(
                name="inside",
                dimensions=Dimensions(
                    width=JCARD_PANEL_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_4_x,
                    y=0.0
                ),
                tracks=combined_tracks,
                side_capacity=self.side_capacity,
                title="Tracklist",
                track_title_overflow=self.theme.track_title_overflow,
                min_track_title_char_spacing=self.theme.min_track_title_char_spacing,
                use_tape_flip_offset=False,  # Don't offset Side B - they're separate albums
            )
        )

        # Panel 5: Genre/Descriptors (vertical split - top: album1, bottom: album2)
        # Each half further split into genre tree (top 50%) and descriptors (bottom 50%)

        # Album 1 sections (top half of panel 5)
        genre1 = GenreTreeSection(
            name="genre_tree_album1",
            dimensions=Dimensions(width=0, height=0, x=0, y=0),  # Will be set by container
            album=self.album1,
            font_size=9.0,
            padding_override=0.0625,  # Half of standard padding
        )
        descriptors1 = DescriptorsSection(
            name="descriptors_album1",
            dimensions=Dimensions(width=0, height=0, x=0, y=0),  # Will be set by container
            album=self.album1,
            font_size=9.0,
            padding_override=0.0625,  # Half of standard padding
        )

        # Album 2 sections (bottom half of panel 5)
        genre2 = GenreTreeSection(
            name="genre_tree_album2",
            dimensions=Dimensions(width=0, height=0, x=0, y=0),  # Will be set by container
            album=self.album2,
            font_size=9.0,
            padding_override=0.0625,  # Half of standard padding
        )
        descriptors2 = DescriptorsSection(
            name="descriptors_album2",
            dimensions=Dimensions(width=0, height=0, x=0, y=0),  # Will be set by container
            album=self.album2,
            font_size=9.0,
            padding_override=0.0625,  # Half of standard padding
        )

        # Create nested containers: outer vertical split for albums, inner horizontal split for genre/descriptors
        # Give containers real dimensions so their children get proper sizes when _layout_children() runs
        album1_container = ContainerSection(
            name="album1_genre_descriptors",
            dimensions=Dimensions(
                width=JCARD_PANEL_WIDTH,
                height=JCARD_HEIGHT / 2,  # Top half
                x=panel_5_x,
                y=JCARD_HEIGHT / 2
            ),
            children=[genre1, descriptors1],  # Left to right
            layout="horizontal"
        )

        album2_container = ContainerSection(
            name="album2_genre_descriptors",
            dimensions=Dimensions(
                width=JCARD_PANEL_WIDTH,
                height=JCARD_HEIGHT / 2,  # Bottom half
                x=panel_5_x,
                y=0.0
            ),
            children=[genre2, descriptors2],  # Left to right
            layout="horizontal"
        )

        sections.append(
            ContainerSection(
                name="genre_descriptors",
                dimensions=Dimensions(
                    width=JCARD_PANEL_WIDTH,
                    height=JCARD_HEIGHT,
                    x=panel_5_x,
                    y=0.0
                ),
                children=[album2_container, album1_container],  # Bottom to top
                layout="vertical"
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
        return [
            JCARD_BACK_WIDTH,  # Between metadata and spine
            JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH,  # Between spine and cover
            JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH,  # Between cover and tracklist
            JCARD_BACK_WIDTH + JCARD_SPINE_WIDTH + JCARD_PANEL_WIDTH + JCARD_PANEL_WIDTH,  # Between tracklist and genre panel
        ]
