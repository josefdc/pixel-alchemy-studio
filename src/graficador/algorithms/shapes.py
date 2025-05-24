"""
Basic geometric shapes drawing algorithms module.

This module implements algorithms for drawing shapes like ellipses
using efficient techniques such as the midpoint algorithm.
"""

from typing import Callable
import pygame
from ..geometry.point import Point

PixelPlotter = Callable[[int, int, pygame.Color], None]

def midpoint_ellipse(center: Point, rx: int, ry: int, plot_pixel: PixelPlotter, color: pygame.Color) -> None:
    """
    Draw an ellipse using the midpoint algorithm.

    The algorithm divides the calculation into two regions based on the slope
    of the curve and uses quadruple symmetry to draw the complete ellipse.

    Args:
        center: Center point (xc, yc) of the ellipse.
        rx: Horizontal radius (semi-major axis in x). Must be positive.
        ry: Vertical radius (semi-major axis in y). Must be positive.
        plot_pixel: Callback function to draw an individual pixel.
                   Must accept (x: int, y: int, color: pygame.Color).
        color: Color to draw the ellipse with.
    """
    if rx <= 0 or ry <= 0:
        print("Warning: Ellipse radii must be positive.")
        if rx == 0 and ry == 0:
             plot_pixel(center.x, center.y, color)
        return

    xc, yc = center.x, center.y
    rx_sq: int = rx * rx
    ry_sq: int = ry * ry

    def _plot_ellipse_points(center_x: int, center_y: int, current_x: int, current_y: int,
                            plot_func: PixelPlotter, point_color: pygame.Color) -> None:
        """Draw the 4 symmetric points of the ellipse."""
        plot_func(center_x + current_x, center_y + current_y, point_color)
        plot_func(center_x - current_x, center_y + current_y, point_color)
        plot_func(center_x + current_x, center_y - current_y, point_color)
        plot_func(center_x - current_x, center_y - current_y, point_color)

    x: int = 0
    y: int = ry
    p1: float = ry_sq - rx_sq * ry + 0.25 * rx_sq

    _plot_ellipse_points(xc, yc, x, y, plot_pixel, color)

    while (ry_sq * x) < (rx_sq * y):
        x += 1
        if p1 < 0:
            p1 += 2 * ry_sq * x + ry_sq
        else:
            y -= 1
            p1 += 2 * ry_sq * x - 2 * rx_sq * y + ry_sq
        _plot_ellipse_points(xc, yc, x, y, plot_pixel, color)

    p2: float = ry_sq * (x + 0.5)**2 + rx_sq * (y - 1)**2 - rx_sq * ry_sq

    while y >= 0:
        y -= 1
        if p2 > 0:
            p2 += -2 * rx_sq * y + rx_sq
        else:
            x += 1
            p2 += 2 * ry_sq * x - 2 * rx_sq * y + rx_sq
        _plot_ellipse_points(xc, yc, x, y, plot_pixel, color)