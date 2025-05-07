"""
src/graficador/algorithms/dda.py
Módulo del algoritmo DDA (Digital Differential Analyzer).

Este módulo implementa el algoritmo DDA para dibujar líneas rectas en una
cuadrícula de píxeles. DDA es un algoritmo simple de rasterización de líneas
basado en el cálculo de incrementos.
"""

from typing import Callable
from ..geometry.point import Point
import pygame

# Type hint para la función callback que dibuja píxeles individuales
PixelPlotter = Callable[[int, int, pygame.Color], None]

# Nota: Se necesita pygame aquí principalmente para el tipo pygame.Color.
# Podría desacoplarse si fuera un requisito estricto.

def dda_line(p1: Point, p2: Point, plot_pixel: PixelPlotter, color: pygame.Color) -> None:
    """
    Dibuja una línea entre p1 y p2 usando el algoritmo DDA.

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

    dx: int = x2 - x1
    dy: int = y2 - y1

    # Determinar el número de pasos necesarios basado en la dimensión dominante
    steps: int
    if abs(dx) > abs(dy):
        steps = abs(dx)
    else:
        steps = abs(dy)

    # Evitar división por cero si los puntos inicial y final coinciden
    if steps == 0:
        plot_pixel(x1, y1, color)
        return

    # Calcular incrementos para x e y por cada paso
    x_increment: float = dx / steps
    y_increment: float = dy / steps

    # Inicializar coordenadas flotantes en el punto de inicio
    x: float = float(x1)
    y: float = float(y1)

    # Nota: La siguiente línea es para depuración y puede eliminarse en producción.
    print(f"DDA: p1=({x1},{y1}), p2=({x2},{y2}), steps={steps}, incr=({x_increment:.2f},{y_increment:.2f})") # Debug

    # Iterar 'steps' veces para dibujar la línea
    for _ in range(steps + 1): # +1 para asegurar que se dibuje el último punto (p2)
        # Redondear las coordenadas flotantes al píxel entero más cercano
        plot_pixel(round(x), round(y), color)
        x += x_increment
        y += y_increment