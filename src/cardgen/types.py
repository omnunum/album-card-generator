"""Type aliases used across the cardgen package."""

from typing import Literal, Tuple

# Color types
RGBColor = Tuple[float, float, float]  # RGB color in 0-1 range
HSVColor = Tuple[float, float, float]  # HSV color in 0-1 range

# Cover art display options
CoverArtMode = Literal["square", "fullscale"]
CoverArtAlign = Literal["center", "left", "right"]

# Track title overflow options
TrackTitleOverflow = Literal["truncate", "wrap"]
