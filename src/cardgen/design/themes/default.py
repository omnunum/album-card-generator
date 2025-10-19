"""Default theme implementation."""

from cardgen.config import DefaultThemeConfig
from cardgen.design.base import ColorScheme, FontConfig, Theme
from cardgen.fonts import is_iosevka_available
from cardgen.types import CoverArtAlign, CoverArtMode, TrackTitleOverflow


class DefaultTheme(Theme):
    """Default clean theme for j-cards with optional gradient background."""

    def __init__(self, config: DefaultThemeConfig | None = None, cover_art: bytes | None = None) -> None:
        """
        Initialize default theme.

        Args:
            config: Theme configuration from config file. If None, uses defaults.
            cover_art: Optional album art for gradient color extraction.
        """
        if config is None:
            from cardgen.config import DefaultThemeConfig

            config = DefaultThemeConfig()

        self.config = config
        self.cover_art = cover_art
        self.gradient_start = None
        self.gradient_end = None

        # Extract gradient colors if enabled and cover art is provided
        if config.use_gradient and cover_art is not None:
            from cardgen.utils.color_extraction import get_gradient_colors
            self.gradient_start, self.gradient_end = get_gradient_colors(cover_art)

    def get_font_config(self) -> FontConfig:
        """
        Get font configuration for this theme.

        Returns:
            FontConfig object.
        """
        # Use Iosevka if available, otherwise fall back to Courier
        monospace_family = self.config.monospace_font_family
        if monospace_family == "Iosevka" and not is_iosevka_available():
            monospace_family = "Courier"

        return FontConfig(
            family=self.config.font_family,
            monospace_family=monospace_family,
            title_size=self.config.title_font_size,
            artist_size=self.config.artist_font_size,
            track_size=self.config.track_font_size,
            metadata_size=self.config.metadata_font_size,
        )

    def get_color_scheme(self) -> ColorScheme:
        """
        Get color scheme for this theme.

        Returns:
            ColorScheme object with gradient enabled if configured.
        """
        # Use gradient colors if enabled and extracted
        if self.config.use_gradient and self.gradient_start and self.gradient_end:
            return ColorScheme(
                background=self.gradient_start,  # Fallback background
                text=tuple(self.config.gradient_text_color),  # type: ignore
                accent=tuple(self.config.gradient_accent_color),  # type: ignore
                gradient_enabled=True,
                gradient_start=self.gradient_start,
                gradient_end=self.gradient_end,
            )

        # Standard solid color scheme
        return ColorScheme(
            background=tuple(self.config.background_color),  # type: ignore
            text=tuple(self.config.text_color),  # type: ignore
            accent=tuple(self.config.accent_color),  # type: ignore
        )

    def get_padding(self) -> float:
        """
        Get default padding in inches.

        Returns:
            Padding in inches.
        """
        return 0.125  # 1/8 inch padding

    def get_track_title_overflow(self) -> TrackTitleOverflow:
        """
        Get track title overflow mode for tracklists.

        Returns:
            "truncate" or "wrap".
        """
        return self.config.track_title_overflow

    def get_cover_art_mode(self) -> CoverArtMode:
        """
        Get cover art display mode.

        Returns:
            "square" or "fullscale".
        """
        return self.config.cover_art_mode

    def get_cover_art_align(self) -> CoverArtAlign:
        """
        Get cover art horizontal alignment for fullscale mode.

        Returns:
            "center", "left", or "right".
        """
        return self.config.cover_art_align
