# src/graficador/geometry/point.py
"""
Point geometry module.

This module defines a Point class to represent 2D coordinates with integer values.
"""
from typing import NamedTuple

class Point(NamedTuple):
    """Represents a 2D point with integer coordinates."""
    x: int
    y: int