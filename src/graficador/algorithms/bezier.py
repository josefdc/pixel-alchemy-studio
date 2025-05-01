"""
Módulo de algoritmos para curvas de Bézier.

Este módulo implementa algoritmos para dibujar curvas de Bézier cúbicas en un contexto gráfico
usando Pygame. Proporciona dos implementaciones diferentes:
- Una basada en segmentos de línea que conectan puntos calculados en la curva
- Otra más tradicional que dibuja punto a punto

Las curvas de Bézier son útiles para crear formas suaves y controlables, ampliamente
utilizadas en diseño gráfico y modelado geométrico.
"""
from typing import Callable, List
import pygame
from ..geometry.point import Point

# Type hint para la función callback que dibuja píxeles individuales
PixelPlotter = Callable[[int, int, pygame.Color], None]
# Type hint para la función callback que dibuja segmentos de línea
LineDrawer = Callable[[Point, Point, pygame.Color], None]

def cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point,
                 draw_line_func: LineDrawer,
                 color: pygame.Color,
                 num_segments: int = 50) -> None:
    """
    Dibuja una curva de Bézier cúbica conectando puntos calculados
    con segmentos de línea para mejor conectividad visual.

    Args:
        p0 (Point): Punto de inicio.
        p1 (Point): Primer punto de control.
        p2 (Point): Segundo punto de control.
        p3 (Point): Punto final.
        draw_line_func (LineDrawer): Función callback para dibujar un segmento de línea.
                        Debe aceptar (start_point: Point, end_point: Point, color: pygame.Color).
        color (pygame.Color): Color de la curva.
        num_segments (int, optional): Número de segmentos de línea a usar. Default: 50.

    Returns:
        None
    """
    if num_segments < 1:
        num_segments = 1

    # Nota: La siguiente línea es para depuración y puede eliminarse en producción.
    print(f"Bézier (con líneas): P0={p0}, P1={p1}, P2={p2}, P3={p3}, segments={num_segments}") # Debug

    points: List[Point] = []

    # Calcular los puntos a lo largo de la curva
    for i in range(num_segments + 1):
        t = i / num_segments # Parámetro t va de 0 a 1

        # Fórmula de Bézier cúbica
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

    # Dibujar líneas entre puntos consecutivos calculados
    # Iteramos hasta num_segments porque dibujamos entre points[i] y points[i+1]
    for i in range(num_segments):
        # Evitar dibujar líneas de longitud cero si puntos consecutivos son iguales
        if points[i] != points[i+1]:
            draw_line_func(points[i], points[i+1], color)

def cubic_bezier_points(p0: Point, p1: Point, p2: Point, p3: Point,
                        plot_pixel: PixelPlotter, color: pygame.Color,
                        num_segments: int = 50) -> None:
    """
    Dibuja una curva de Bézier cúbica dibujando píxeles individuales.

    Esta implementación calcula puntos a lo largo de la curva de Bézier y dibuja
    píxeles individuales, evitando repeticiones de píxeles consecutivos.

    Args:
        p0 (Point): Punto de inicio.
        p1 (Point): Primer punto de control.
        p2 (Point): Segundo punto de control.
        p3 (Point): Punto final.
        plot_pixel (PixelPlotter): Función callback para dibujar un píxel.
                    Debe aceptar (x: int, y: int, color: pygame.Color).
        color (pygame.Color): Color de la curva.
        num_segments (int, optional): Número de puntos a calcular a lo largo de la curva. Default: 50.

    Returns:
        None
    """
    if num_segments < 1: num_segments = 1
    last_x, last_y = -1, -1 # Usado para evitar dibujar el mismo píxel múltiples veces
    for i in range(num_segments + 1):
        t = i / num_segments # Parámetro t va de 0 a 1
        one_minus_t = 1 - t

        # Fórmula de Bézier cúbica
        b_x = (one_minus_t**3 * p0.x + 3 * one_minus_t**2 * t * p1.x + 3 * one_minus_t * t**2 * p2.x + t**3 * p3.x)
        b_y = (one_minus_t**3 * p0.y + 3 * one_minus_t**2 * t * p1.y + 3 * one_minus_t * t**2 * p2.y + t**3 * p3.y)

        pixel_x, pixel_y = round(b_x), round(b_y)
        # Solo dibuja si el píxel es diferente al anterior
        if pixel_x != last_x or pixel_y != last_y:
            plot_pixel(pixel_x, pixel_y, color)
            last_x, last_y = pixel_x, pixel_y