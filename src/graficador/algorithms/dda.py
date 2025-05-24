"""
DDA (Digital Differential Analyzer) algorithm module.

This module implements the DDA algorithm for drawing straight lines on a
pixel grid. DDA is a simple line rasterization algorithm based on the
calculation of increments.
"""

from typing import Callable
from ..geometry.point import Point
import pygame

PixelPlotter = Callable[[int, int, pygame.Color], None]

def dda_line(p1: Point, p2: Point, plot_pixel: PixelPlotter, color: pygame.Color) -> None:
    """
    Draw a line between p1 and p2 using the DDA algorithm.

    Args:
        p1: Starting point of the line.
        p2: End point of the line.
        plot_pixel: Callback function to draw an individual pixel.
                   Must accept (x: int, y: int, color: pygame.Color).
        color: Color to draw the line with.
    """
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y

    dx: int = x2 - x1
    dy: int = y2 - y1

    steps: int
    if abs(dx) > abs(dy):
        steps = abs(dx)
    else:
        steps = abs(dy)

    if steps == 0:
        plot_pixel(x1, y1, color)
        return

    x_increment: float = dx / steps
    y_increment: float = dy / steps

    x: float = float(x1)
    y: float = float(y1)

    for _ in range(steps + 1):
        plot_pixel(round(x), round(y), color)
        x += x_increment
        y += y_increment