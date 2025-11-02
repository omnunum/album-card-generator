"""Container section for vertical/horizontal layout of child sections."""

from cardgen.design.base import CardSection, RendererContext
from cardgen.types import SizeStyle
from cardgen.utils.dimensions import Dimensions


class ContainerSection(CardSection):
    """
    A container that lays out child sections either horizontally or vertically.

    This section doesn't render anything itself but manages the layout and rendering
    of its child sections.
    """

    def __init__(
        self,
        name: str,
        dimensions: Dimensions,
        children: list[CardSection],
        layout: str = "horizontal",
        size_style: SizeStyle = "full",
    ) -> None:
        """
        Initialize container section.

        Args:
            name: Section name.
            dimensions: Container dimensions.
            children: List of child sections to lay out.
            layout: Layout direction - "horizontal" or "vertical".
            size_style: Size style - "full" or "compact" (default: "full").

        Raises:
            ValueError: If layout is not "horizontal" or "vertical".
            ValueError: If children list is empty.
        """
        if layout not in ("horizontal", "vertical"):
            raise ValueError(f"Layout must be 'horizontal' or 'vertical', got: {layout}")

        if not children:
            raise ValueError("Container must have at least one child section")

        # Set children and layout before calling super().__init__() so the dimensions
        # setter can use them to layout children
        self.children = children
        self.layout = layout

        # Call parent __init__ which will set dimensions and trigger _layout_children()
        super().__init__(name, dimensions, size_style)

    @property
    def dimensions(self) -> Dimensions:
        """Get container dimensions."""
        return self._dimensions

    @dimensions.setter
    def dimensions(self, value: Dimensions) -> None:
        """
        Set container dimensions and re-layout children.

        This ensures that when a parent container updates this container's dimensions,
        the children are automatically re-laid out with the new dimensions.
        """
        self._dimensions = value
        # Only layout children if they've been set (handles initialization order)
        if hasattr(self, 'children') and hasattr(self, 'layout'):
            self._layout_children()

    def _layout_children(self) -> None:
        """Calculate and set dimensions for all child sections."""
        num_children = len(self.children)

        if self.layout == "horizontal":
            # Divide width equally among children
            child_width = self.dimensions.width / num_children
            child_height = self.dimensions.height

            for i, child in enumerate(self.children):
                child.dimensions = Dimensions(
                    x=self.dimensions.x + (i * child_width),
                    y=self.dimensions.y,
                    width=child_width,
                    height=child_height,
                )
        else:  # vertical
            # Divide height equally among children
            child_width = self.dimensions.width
            child_height = self.dimensions.height / num_children

            for i, child in enumerate(self.children):
                # Note: Y coordinates go up from bottom in PDF, so we reverse the order
                child.dimensions = Dimensions(
                    x=self.dimensions.x,
                    y=self.dimensions.y + (i * child_height),
                    width=child_width,
                    height=child_height,
                )

    def render(self, context: RendererContext) -> None:
        """
        Render all child sections with adjusted contexts.

        Args:
            context: Rendering context for this container.
        """
        container_points = self.dimensions.to_points()

        for child in self.children:
            # Create adjusted context for each child based on its dimensions
            child_points = child.dimensions.to_points()

            # Calculate offset from container origin
            child_context = RendererContext(
                canvas=context.canvas,
                x=context.x + (child_points.x - container_points.x),
                y=context.y + (child_points.y - container_points.y),
                width=child_points.width,
                height=child_points.height,
                theme=context.theme,
                padding=context.padding,
                dpi=context.dpi,
            )
            child.render(child_context)
