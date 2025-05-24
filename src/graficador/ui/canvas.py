"""
Canvas module for the drawing interface.

Defines the Canvas class that represents the main area where users draw geometric shapes.
Manages its own surface, background color, and provides methods for drawing pixels and
coordinate conversion.
"""

import pygame
from typing import Tuple
from ..geometry.point import Point
from .. import config

class Canvas:
    """
    Interactive drawing area for the application.

    Manages a separate Pygame surface where all drawing operations are performed.
    Provides methods to clear the canvas, draw individual pixels, and convert coordinates
    between the canvas relative system and screen absolute coordinates.

    Attributes:
        rect (pygame.Rect): Rectangle defining canvas position and size within main window.
        surface (pygame.Surface): Pygame surface where drawing occurs.
        bg_color (pygame.Color): Current canvas background color.
    """

    def __init__(self, x: int, y: int, width: int, height: int, bg_color: pygame.Color):
        """
        Initialize the canvas.

        Args:
            x: X position of canvas top-left corner on screen.
            y: Y position of canvas top-left corner on screen.
            width: Canvas width in pixels.
            height: Canvas height in pixels.
            bg_color: Initial canvas background color.
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.surface: pygame.Surface = pygame.Surface((width, height))
        self.bg_color: pygame.Color = bg_color
        self.clear()

    def clear(self) -> None:
        """Clear the canvas by filling it with the background color."""
        self.surface.fill(self.bg_color)

    def draw_pixel(self, x: int, y: int, color: pygame.Color) -> None:
        """
        Draw a pixel on the canvas at relative coordinates.

        Args:
            x: X coordinate relative to canvas.
            y: Y coordinate relative to canvas.
            color: Pixel color to draw.
        """
        if 0 <= x < self.rect.width and 0 <= y < self.rect.height:
            try:
                self.surface.set_at((x, y), color)
            except IndexError:
                print(f"Warning: Attempted to draw pixel outside canvas bounds at ({x}, {y})")

    def render(self, target_surface: pygame.Surface) -> None:
        """
        Render this canvas surface onto a target surface.

        Args:
            target_surface: Surface where canvas content will be rendered.
        """
        target_surface.blit(self.surface, self.rect.topleft)

    def to_absolute_pos(self, point: Point) -> Tuple[int, int]:
        """
        Convert canvas-relative coordinates to absolute screen coordinates.

        Args:
            point: Point with coordinates relative to canvas.

        Returns:
            Tuple with absolute coordinates in the main window.
        """
        return (point.x + self.rect.x, point.y + self.rect.y)

    def to_relative_pos(self, point: Point) -> Point:
        """
        Convert absolute screen coordinates to canvas-relative coordinates.

        Args:
            point: Point with absolute screen coordinates.

        Returns:
            New Point with coordinates relative to canvas top-left corner.
        """
        return Point(point.x - self.rect.x, point.y - self.rect.y)