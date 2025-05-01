# src/graficador/geometry/point.py
from typing import NamedTuple

class Point(NamedTuple):
    """Representa un punto 2D con coordenadas enteras."""
    x: int
    y: int