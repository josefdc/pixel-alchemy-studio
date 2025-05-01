"""
Módulo de la interfaz de usuario para el lienzo de dibujo.

Define la clase `Canvas`, que representa el área principal donde los usuarios
dibujan las formas geométricas. Gestiona su propia superficie, color de fondo,
y proporciona métodos para dibujar píxeles y convertir coordenadas.
"""

import pygame
from typing import Tuple # Importar Tuple
from ..geometry.point import Point
# Nota: 'config' se importa pero no se usa directamente en este fragmento.
# Se mantiene por si es usado en otras partes del archivo original o proyecto.
from .. import config

class Canvas:
    """
    Representa el área de dibujo (lienzo) interactiva de la aplicación.

    Gestiona una superficie de Pygame separada donde se realizan todas las
    operaciones de dibujo. Proporciona métodos para limpiar el lienzo,
    dibujar píxeles individuales en coordenadas relativas, y convertir
    coordenadas entre el sistema relativo del lienzo y el absoluto de la pantalla.

    Attributes:
        rect (pygame.Rect): El rectángulo que define la posición y tamaño del lienzo
                            dentro de la ventana principal.
        surface (pygame.Surface): La superficie de Pygame donde se dibuja.
        bg_color (pygame.Color): El color de fondo actual del lienzo.
    """

    def __init__(self, x: int, y: int, width: int, height: int, bg_color: pygame.Color):
        """
        Inicializa el lienzo.

        Args:
            x (int): Posición X de la esquina superior izquierda del lienzo en la pantalla.
            y (int): Posición Y de la esquina superior izquierda del lienzo en la pantalla.
            width (int): Ancho del lienzo en píxeles.
            height (int): Alto del lienzo en píxeles.
            bg_color (pygame.Color): Color de fondo inicial del lienzo.
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.surface: pygame.Surface = pygame.Surface((width, height))
        self.bg_color: pygame.Color = bg_color
        self.clear() # Establecer el color de fondo inicial

        # Nota: La siguiente línea es para depuración y puede eliminarse en producción.
        print(f"Canvas inicializado en {self.rect} con color {bg_color}") # Debug

    def clear(self) -> None:
        """
        Limpia el lienzo llenándolo completamente con su color de fondo.

        Returns:
            None
        """
        self.surface.fill(self.bg_color)
        # Posible mejora futura: dibujar un borde alrededor del lienzo.
        # pygame.draw.rect(self.surface, config.DARK_GRAY, self.surface.get_rect(), 1)

    def draw_pixel(self, x: int, y: int, color: pygame.Color) -> None:
        """
        Dibuja un píxel en el lienzo en coordenadas relativas.

        Las coordenadas (x, y) deben ser relativas a la esquina superior
        izquierda del lienzo (0, 0). El método verifica que las coordenadas
        estén dentro de los límites del lienzo antes de dibujar.

        Args:
            x (int): Coordenada X relativa al lienzo.
            y (int): Coordenada Y relativa al lienzo.
            color (pygame.Color): Color del píxel a dibujar.

        Returns:
            None
        """
        if 0 <= x < self.rect.width and 0 <= y < self.rect.height:
            try:
                # set_at es la forma directa de Pygame para modificar un píxel
                self.surface.set_at((x, y), color)
            except IndexError:
                # Aunque la comprobación de límites debería prevenir esto,
                # set_at puede lanzar IndexError bajo ciertas circunstancias.
                print(f"Advertencia: Intento de dibujar píxel fuera de los límites del lienzo en ({x}, {y}) vía set_at")
        # else: # No es necesario advertir si está fuera, la comprobación ya lo evita.
            # print(f"Advertencia: Coordenadas ({x}, {y}) fuera del lienzo.")

    def render(self, target_surface: pygame.Surface) -> None:
        """
        Dibuja (blit) la superficie de este lienzo sobre una superficie destino.

        Args:
            target_surface (pygame.Surface): La superficie donde se renderizará
                                             el contenido del lienzo (e.g., la pantalla principal).

        Returns:
            None
        """
        target_surface.blit(self.surface, self.rect.topleft)

    def to_absolute_pos(self, point: Point) -> Tuple[int, int]:
        """
        Convierte un punto con coordenadas relativas al lienzo a coordenadas absolutas de la pantalla.

        Args:
            point (Point): Un punto con coordenadas (x, y) relativas al lienzo.

        Returns:
            Tuple[int, int]: Una tupla (x, y) con las coordenadas absolutas correspondientes
                             en la ventana principal.
        """
        return (point.x + self.rect.x, point.y + self.rect.y)

    def to_relative_pos(self, point: Point) -> Point:
        """
        Convierte un punto con coordenadas absolutas de la pantalla a coordenadas relativas del lienzo.

        Args:
            point (Point): Un punto con coordenadas (x, y) absolutas en la pantalla.

        Returns:
            Point: Un nuevo objeto Point con las coordenadas (x, y) relativas a la esquina
                   superior izquierda del lienzo.
        """
        return Point(point.x - self.rect.x, point.y - self.rect.y)