"""
Bresenham algorithms module.

This module implements the classic Bresenham algorithms for drawing
lines and circles efficiently on a pixel grid using only integer arithmetic.
These algorithms are fundamental in computer graphics for rasterizing
geometric primitives.
"""
from typing import Callable
import pygame
from ..geometry.point import Point

PixelPlotter = Callable[[int, int, pygame.Color], None]

def bresenham_line(p1: Point, p2: Point, plot_pixel: PixelPlotter, color: pygame.Color) -> None:
    """
    Draw a line between p1 and p2 using Bresenham's line algorithm.

    Args:
        p1: Starting point of the line.
        p2: End point of the line.
        plot_pixel: Callback function to draw an individual pixel.
                   Must accept (x: int, y: int, color: pygame.Color).
        color: Color to draw the line with.
    """
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y

    dx: int = abs(x2 - x1)
    dy: int = abs(y2 - y1)

    sx: int = 1 if x1 < x2 else -1
    sy: int = 1 if y1 < y2 else -1

    err: int = dx - dy

    x, y = x1, y1

    while True:
        plot_pixel(x, y, color)

        if x == x2 and y == y2:
            break

        e2: int = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

def bresenham_circle(center: Point, radius: int, plot_pixel: PixelPlotter, color: pygame.Color) -> None:
    """
    Draw a circle using Bresenham's/Midpoint circle algorithm.

    Calculates pixels for one octant and uses symmetry to draw
    the complete circle.

    Args:
        center: Center point (x, y) of the circle.
        radius: Integer radius of the circle. Must be non-negative.
        plot_pixel: Callback function to draw an individual pixel.
                   Must accept (x: int, y: int, color: pygame.Color).
        color: Color to draw the circle with.
    """
    if radius < 0:
        print("Warning: Circle radius cannot be negative.")
        return
    if radius == 0:
        plot_pixel(center.x, center.y, color)
        return

    xc, yc = center.x, center.y
    x: int = 0
    y: int = radius
    p: int = 1 - radius

    def _plot_circle_points(center_x: int, center_y: int, current_x: int, current_y: int,
                           plot_func: PixelPlotter, point_color: pygame.Color) -> None:
        """Draw the 8 symmetric points of the circle."""
        plot_func(center_x + current_x, center_y + current_y, point_color)
        plot_func(center_x - current_x, center_y + current_y, point_color)
        plot_func(center_x + current_x, center_y - current_y, point_color)
        plot_func(center_x - current_x, center_y - current_y, point_color)
        plot_func(center_x + current_y, center_y + current_x, point_color)
        plot_func(center_x - current_y, center_y + current_x, point_color)
        plot_func(center_x + current_y, center_y - current_x, point_color)
        plot_func(center_x - current_y, center_y - current_x, point_color)

    _plot_circle_points(xc, yc, x, y, plot_pixel, color)

    while x < y:
        x += 1
        if p < 0:
            p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1

        _plot_circle_points(xc, yc, x, y, plot_pixel, color)