"""
Bezier curve algorithms module.

This module implements algorithms for drawing cubic Bezier curves in a graphics context
using Pygame. It provides two different implementations:
- One based on line segments connecting calculated points on the curve
- Another more traditional approach that draws point by point

Bezier curves are useful for creating smooth and controllable shapes, widely
used in graphic design and geometric modeling.
"""
from typing import Callable, List
import pygame
from ..geometry.point import Point

PixelPlotter = Callable[[int, int, pygame.Color], None]
LineDrawer = Callable[[Point, Point, pygame.Color], None]

def cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point,
                 draw_line_func: LineDrawer,
                 color: pygame.Color,
                 num_segments: int = 50) -> None:
    """
    Draw a cubic Bezier curve by connecting calculated points with line segments.
    
    This implementation provides better visual connectivity by drawing line segments
    between consecutive points on the curve.

    Args:
        p0: Starting point of the curve.
        p1: First control point.
        p2: Second control point.
        p3: End point of the curve.
        draw_line_func: Callback function to draw a line segment.
                       Must accept (start_point: Point, end_point: Point, color: pygame.Color).
        color: Color of the curve.
        num_segments: Number of line segments to use. Defaults to 50.
    """
    if num_segments < 1:
        num_segments = 1

    points: List[Point] = []

    for i in range(num_segments + 1):
        t = i / num_segments

        one_minus_t = 1 - t
        b_x = (one_minus_t**3 * p0.x +
               3 * one_minus_t**2 * t * p1.x +
               3 * one_minus_t * t**2 * p2.x +
               t**3 * p3.x)
        b_y = (one_minus_t**3 * p0.y +
               3 * one_minus_t**2 * t * p1.y +
               3 * one_minus_t * t**2 * p2.y +
               t**3 * p3.y)

        points.append(Point(round(b_x), round(b_y)))

    for i in range(num_segments):
        if points[i] != points[i+1]:
            draw_line_func(points[i], points[i+1], color)

def cubic_bezier_points(p0: Point, p1: Point, p2: Point, p3: Point,
                        plot_pixel: PixelPlotter, color: pygame.Color,
                        num_segments: int = 50) -> None:
    """
    Draw a cubic Bezier curve by plotting individual pixels.

    This implementation calculates points along the Bezier curve and draws
    individual pixels, avoiding repetition of consecutive pixels.

    Args:
        p0: Starting point of the curve.
        p1: First control point.
        p2: Second control point.
        p3: End point of the curve.
        plot_pixel: Callback function to draw a pixel.
                   Must accept (x: int, y: int, color: pygame.Color).
        color: Color of the curve.
        num_segments: Number of points to calculate along the curve. Defaults to 50.
    """
    if num_segments < 1: num_segments = 1
    last_x, last_y = -1, -1
    for i in range(num_segments + 1):
        t = i / num_segments
        one_minus_t = 1 - t

        b_x = (one_minus_t**3 * p0.x + 3 * one_minus_t**2 * t * p1.x + 3 * one_minus_t * t**2 * p2.x + t**3 * p3.x)
        b_y = (one_minus_t**3 * p0.y + 3 * one_minus_t**2 * t * p1.y + 3 * one_minus_t * t**2 * p2.y + t**3 * p3.y)

        pixel_x, pixel_y = round(b_x), round(b_y)
        if pixel_x != last_x or pixel_y != last_y:
            plot_pixel(pixel_x, pixel_y, color)
            last_x, last_y = pixel_x, pixel_y