"""
src/graficador/algorithms/shapes.py
Módulo de algoritmos para dibujar formas geométricas básicas.

Este módulo implementa algoritmos para dibujar formas como elipses
utilizando técnicas eficientes como el algoritmo del punto medio.
"""

from typing import Callable
import pygame
from ..geometry.point import Point

# Type hint para la función callback que dibuja píxeles individuales
PixelPlotter = Callable[[int, int, pygame.Color], None]

def midpoint_ellipse(center: Point, rx: int, ry: int, plot_pixel: PixelPlotter, color: pygame.Color) -> None:
    """
    Dibuja una elipse usando el algoritmo del punto medio.

    El algoritmo divide el cálculo en dos regiones basadas en la pendiente
    de la curva y utiliza simetría cuádruple para dibujar la elipse completa.

    Args:
        center (Point): El punto central (xc, yc) de la elipse.
        rx (int): El radio horizontal (semieje mayor en x). Debe ser positivo.
        ry (int): El radio vertical (semieje mayor en y). Debe ser positivo.
        plot_pixel (PixelPlotter): Función callback para dibujar un píxel individual.
                                  Debe aceptar (x: int, y: int, color: pygame.Color).
        color (pygame.Color): El color con el que se dibujará la elipse.

    Returns:
        None
    """
    if rx <= 0 or ry <= 0:
        print("Advertencia: Los radios de la elipse deben ser positivos.")
        # Dibuja un punto si ambos radios son cero
        if rx == 0 and ry == 0:
             plot_pixel(center.x, center.y, color)
        # Nota: Podría implementarse el dibujo de una línea si solo un radio es 0.
        return

    xc, yc = center.x, center.y
    rx_sq: int = rx * rx
    ry_sq: int = ry * ry

    # --- Función auxiliar interna ---
    def _plot_ellipse_points(center_x: int, center_y: int, current_x: int, current_y: int,
                            plot_func: PixelPlotter, point_color: pygame.Color) -> None:
        """Dibuja los 4 puntos simétricos de la elipse."""
        plot_func(center_x + current_x, center_y + current_y, point_color)
        plot_func(center_x - current_x, center_y + current_y, point_color)
        plot_func(center_x + current_x, center_y - current_y, point_color)
        plot_func(center_x - current_x, center_y - current_y, point_color)
    # --- Fin función auxiliar ---

    # Nota: La siguiente línea es para depuración y puede eliminarse en producción.
    print(f"Midpoint Ellipse: center=({xc},{yc}), rx={rx}, ry={ry}") # Debug

    # --- Región 1 (dy/dx > -1) ---
    x: int = 0
    y: int = ry
    # Parámetro de decisión inicial para la región 1 (basado en p = ry^2 - rx^2*ry + rx^2/4)
    p1: float = ry_sq - rx_sq * ry + 0.25 * rx_sq

    # Dibujar los primeros puntos (0, ry) y sus simétricos
    _plot_ellipse_points(xc, yc, x, y, plot_pixel, color)

    # Iterar mientras la pendiente sea mayor que -1 (en magnitud)
    while (ry_sq * x) < (rx_sq * y):
        x += 1
        if p1 < 0:
            # El punto medio está dentro de la elipse, mantener y.
            # Actualizar p1: p1_nuevo = p1_viejo + 2*ry^2*x_nuevo + ry^2
            p1 += 2 * ry_sq * x + ry_sq
        else:
            # El punto medio está fuera o sobre la elipse, decrementar y.
            # Actualizar p1: p1_nuevo = p1_viejo + 2*ry^2*x_nuevo - 2*rx^2*y_nuevo + ry^2
            y -= 1
            p1 += 2 * ry_sq * x - 2 * rx_sq * y + ry_sq
        _plot_ellipse_points(xc, yc, x, y, plot_pixel, color)

    # --- Región 2 (dy/dx <= -1) ---
    # Parámetro de decisión inicial para la región 2, calculado a partir
    # del último punto (x, y) de la región 1.
    # (basado en p = ry^2*(x+1/2)^2 + rx^2*(y-1)^2 - rx^2*ry^2)
    p2: float = ry_sq * (x + 0.5)**2 + rx_sq * (y - 1)**2 - rx_sq * ry_sq

    # Iterar mientras y sea no negativo
    while y >= 0:
        y -= 1
        if p2 > 0:
            # El punto medio está fuera de la elipse, mantener x.
            # Actualizar p2: p2_nuevo = p2_viejo - 2*rx^2*y_nuevo + rx^2
            p2 += -2 * rx_sq * y + rx_sq
        else:
            # El punto medio está dentro o sobre la elipse, incrementar x.
            # Actualizar p2: p2_nuevo = p2_viejo + 2*ry^2*x_nuevo - 2*rx^2*y_nuevo + rx^2
            x += 1
            p2 += 2 * ry_sq * x - 2 * rx_sq * y + rx_sq
        _plot_ellipse_points(xc, yc, x, y, plot_pixel, color)