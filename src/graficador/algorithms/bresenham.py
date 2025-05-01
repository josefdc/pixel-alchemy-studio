"""
Módulo de algoritmos de Bresenham.

Este módulo implementa los algoritmos clásicos de Bresenham para dibujar
líneas y circunferencias de manera eficiente en una cuadrícula de píxeles,
utilizando solo aritmética entera. Estos algoritmos son fundamentales
en gráficos por computadora para rasterizar primitivas geométricas.
"""
from typing import Callable
import pygame
from ..geometry.point import Point

# Type hint para la función callback que dibuja píxeles individuales
PixelPlotter = Callable[[int, int, pygame.Color], None]

def bresenham_line(p1: Point, p2: Point, plot_pixel: PixelPlotter, color: pygame.Color) -> None:
    """
    Dibuja una línea entre p1 y p2 usando el algoritmo de Bresenham.

    Args:
        p1 (Point): Punto de inicio de la línea.
        p2 (Point): Punto de fin de la línea.
        plot_pixel (PixelPlotter): Función callback para dibujar un píxel individual.
                                  Debe aceptar (x: int, y: int, color: pygame.Color).
        color (pygame.Color): El color con el que se dibujará la línea.

    Returns:
        None
    """
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y

    dx: int = abs(x2 - x1)
    dy: int = abs(y2 - y1)

    sx: int = 1 if x1 < x2 else -1
    sy: int = 1 if y1 < y2 else -1

    # Variable de decisión (error acumulado).
    # Nota: Se multiplica por 2 para trabajar solo con enteros.
    err: int = dx - dy

    x, y = x1, y1

    # Nota: La siguiente línea es para depuración y puede eliminarse en producción.
    print(f"Bresenham Line: p1=({x1},{y1}), p2=({x2},{y2}), dx={dx}, dy={dy}") # Debug

    while True:
        plot_pixel(x, y, color)

        if x == x2 and y == y2:
            break

        # e2 es el doble del error actual. Se usa para decidir el próximo paso.
        e2: int = 2 * err
        # Comprobar si mover en el eje x
        if e2 > -dy: # Equivalente a err > -dy/2
            err -= dy
            x += sx
        # Comprobar si mover en el eje y
        if e2 < dx:  # Equivalente a err < dx/2
            err += dx
            y += sy

def bresenham_circle(center: Point, radius: int, plot_pixel: PixelPlotter, color: pygame.Color) -> None:
    """
    Dibuja una circunferencia usando el algoritmo de Bresenham/Punto Medio.

    Calcula los píxeles para un octante y utiliza la simetría para dibujar
    la circunferencia completa.

    Args:
        center (Point): El punto central (x, y) de la circunferencia.
        radius (int): El radio entero de la circunferencia. Debe ser no negativo.
        plot_pixel (PixelPlotter): Función callback para dibujar un píxel individual.
                                  Debe aceptar (x: int, y: int, color: pygame.Color).
        color (pygame.Color): El color con el que se dibujará la circunferencia.

    Returns:
        None
    """
    if radius < 0:
        print("Advertencia: El radio de la circunferencia no puede ser negativo.")
        return
    if radius == 0:
        plot_pixel(center.x, center.y, color)
        return

    xc, yc = center.x, center.y
    x: int = 0
    y: int = radius
    # Parámetro de decisión inicial p = 1 - radio (ajustado para aritmética entera).
    # Determina si el punto medio entre dos píxeles candidatos está dentro o fuera.
    p: int = 1 - radius

    # Nota: La siguiente línea es para depuración y puede eliminarse en producción.
    print(f"Bresenham Circle: center=({xc},{yc}), radius={radius}") # Debug

    # --- Función auxiliar interna ---
    def _plot_circle_points(center_x: int, center_y: int, current_x: int, current_y: int,
                           plot_func: PixelPlotter, point_color: pygame.Color) -> None:
        """Dibuja los 8 puntos simétricos de la circunferencia."""
        plot_func(center_x + current_x, center_y + current_y, point_color)
        plot_func(center_x - current_x, center_y + current_y, point_color)
        plot_func(center_x + current_x, center_y - current_y, point_color)
        plot_func(center_x - current_x, center_y - current_y, point_color)
        plot_func(center_x + current_y, center_y + current_x, point_color) # Simetría x <-> y
        plot_func(center_x - current_y, center_y + current_x, point_color) # Simetría x <-> y
        plot_func(center_x + current_y, center_y - current_x, point_color) # Simetría x <-> y
        plot_func(center_x - current_y, center_y - current_x, point_color) # Simetría x <-> y
    # --- Fin función auxiliar ---

    # Dibujar los primeros puntos basados en (0, R) y sus simetrías
    _plot_circle_points(xc, yc, x, y, plot_pixel, color)

    # Iterar mientras x <= y (calculando un octante, desde 90 a 45 grados)
    while x < y:
        x += 1
        if p < 0:
            # El punto medio está dentro del círculo, mantener y.
            # Actualizar p: p_nuevo = p_viejo + 2x_nuevo + 1
            p += 2 * x + 1
        else:
            # El punto medio está fuera o sobre el círculo, decrementar y.
            # Actualizar p: p_nuevo = p_viejo + 2x_nuevo + 1 - 2y_nuevo
            y -= 1
            p += 2 * (x - y) + 1

        # Dibujar los puntos simétricos para el nuevo (x, y) calculado
        _plot_circle_points(xc, yc, x, y, plot_pixel, color)