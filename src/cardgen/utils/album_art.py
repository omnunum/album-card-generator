"""Album artwork management with color extraction and image processing."""

from io import BytesIO
from typing import Literal

from PIL import Image
from reportlab.lib.utils import ImageReader

from cardgen.types import HSVColor, RGBColor
from Pylette import extract_colors
from Pylette.types import ExtractionMethod


class AlbumArt:
    """Manages album artwork with color extraction and image processing."""

    def __init__(self, image_bytes: bytes):
        """
        Load and prepare image from bytes.

        Args:
            image_bytes: Raw image data (JPEG, PNG, etc.).
        """
        self._image = Image.open(BytesIO(image_bytes))
        if self._image.mode != "RGB":
            self._image = self._image.convert("RGB")
        self._color_palette: list[RGBColor] | None = None

    @property
    def image(self) -> Image.Image:
        """Get original PIL Image."""
        return self._image

    def get_color_palette(self, max_colors: int = 8) -> list[RGBColor]:
        """
        Extract and cache dominant colors.

        Args:
            max_colors: Maximum number of colors to extract (default: 8).

        Returns:
            List of RGB tuples in 0-1 range.
        """
        if self._color_palette is None:
            self._color_palette = self._extract_dominant_colors(self._image, max_colors)
        return self._color_palette

    def resize_and_crop(
        self,
        target_size: tuple[int, int],
        mode: Literal["square", "fullscale"] = "square",
        align: Literal["center", "left", "right"] = "center",
    ) -> Image.Image:
        """
        Resize and crop image to target size.

        Args:
            target_size: (width, height) in pixels
            mode: "square" for aspect-preserving center crop,
                  "fullscale" for height-based scaling with horizontal crop
            align: Horizontal alignment for fullscale mode ("center", "left", "right")

        Returns:
            Cropped PIL.Image copy (original unchanged)
        """
        target_width, target_height = target_size

        if mode == "square":
            # Square mode: aspect-preserving center crop
            # Calculate aspect ratios
            target_ratio = target_width / target_height
            img_ratio = self._image.width / self._image.height

            # Determine resize dimensions to cover target area
            if img_ratio > target_ratio:
                # Image is wider, scale by height
                new_height = target_height
                new_width = int(target_height * img_ratio)
            else:
                # Image is taller, scale by width
                new_width = target_width
                new_height = int(target_width / img_ratio)

            # Resize with high-quality resampling
            img = self._image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Center crop to target size
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height

            return img.crop((left, top, right, bottom))

        elif mode == "fullscale":
            # Fullscale mode: height-based scaling with horizontal crop/alignment
            # Scale image to match target height (maintains aspect ratio)
            scale_factor = target_height / self._image.height
            new_height = target_height
            new_width = int(self._image.width * scale_factor)

            # Resize with high-quality resampling
            img = self._image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Crop horizontally based on alignment
            if new_width <= target_width:
                # Image is narrower than target, no crop needed (center it)
                left = 0
                right = new_width
            else:
                # Image is wider than target, crop based on alignment
                if align == "left":
                    # Align left edge, crop from right
                    left = 0
                    right = target_width
                elif align == "right":
                    # Align right edge, crop from left
                    left = new_width - target_width
                    right = new_width
                else:  # "center" (default)
                    # Center crop
                    left = (new_width - target_width) // 2
                    right = left + target_width

            # Top and bottom are always aligned (full height)
            top = 0
            bottom = target_height

            return img.crop((left, top, right, bottom))

        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'square' or 'fullscale'")

    def to_image_reader(self, processed_image: Image.Image) -> ImageReader:
        """
        Convert a processed PIL Image to ReportLab ImageReader.

        Args:
            processed_image: PIL Image object to convert.

        Returns:
            ImageReader object ready for canvas.drawImage().
        """
        return self.pil_to_image_reader(processed_image)

    @staticmethod
    def pil_to_image_reader(image: Image.Image) -> ImageReader:
        """
        Convert any PIL Image to ReportLab ImageReader.

        Args:
            image: PIL Image object to convert.

        Returns:
            ImageReader object ready for canvas.drawImage().
        """
        img_buffer = BytesIO()
        image.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return ImageReader(img_buffer)

    def _extract_dominant_colors(
        self, image: Image.Image, max_colors: int = 8
    ) -> list[RGBColor]:
        """
        Extract distinct dominant colors from an image using Pylette.

        Extracts up to max_colors using K-means clustering.
        Returns 2-max_colors colors sorted by hue (or frequency) for deterministic ordering.

        Args:
            image: PIL Image object.
            max_colors: Maximum number of colors to extract (default: 8).

        Returns:
            List of 2-max_colors RGB tuples in 0-1 range, sorted by hue or frequency.
        """
        # Extract colors using Pylette - pass PIL Image directly
        palette = extract_colors(image=image, palette_size=max_colors, resize=True, mode=ExtractionMethod.KM)

        # Convert to our format (RGB 0-1 tuples)
        colors: list[RGBColor] = []
        for color in palette:
            # Pylette returns RGB as (R, G, B) in 0-255 range
            r, g, b = color.rgb
            colors.append((r / 255.0, g / 255.0, b / 255.0))

        # Ensure we have at least 2 colors
        if len(colors) < 2:
            # Fallback: use black and white
            return [(0.1, 0.1, 0.1), (0.9, 0.9, 0.9)]
        
        return colors

    @staticmethod
    def _rgb_to_hsv(r: float, g: float, b: float) -> HSVColor:
        """
        Convert RGB color to HSV.

        Args:
            r, g, b: RGB values in 0-1 range.

        Returns:
            Tuple of (h, s, v) in 0-1 range.
        """
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        diff = max_c - min_c

        # Value
        v = max_c

        # Saturation
        if max_c == 0:
            s = 0
        else:
            s = diff / max_c

        # Hue
        if diff == 0:
            h = 0
        elif max_c == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_c == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        return (h / 360.0, s, v)

    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> RGBColor:
        """
        Convert HSV color to RGB.

        Args:
            h, s, v: HSV values in 0-1 range.

        Returns:
            Tuple of (r, g, b) in 0-1 range.
        """
        h = h * 360  # Convert to degrees

        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x

        return (r + m, g + m, b + m)
