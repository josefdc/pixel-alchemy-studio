"""
src/graficador/ui/button.py
Módulo de la interfaz de usuario para botones.

Define la clase `Button` que representa un botón interactivo simple
utilizado en la interfaz gráfica de la aplicación. Permite detectar
hover, clics y mantener un estado de selección visual.
"""
import pygame
from typing import Optional, Tuple # Importar Optional y Tuple

class Button:
    """
    Representa un botón simple clickeable con texto y estado de selección.

    Attributes:
        rect (pygame.Rect): El rectángulo que define la posición y tamaño del botón.
        text (str): El texto mostrado en el botón.
        identifier (str): Un identificador único para el botón (e.g., 'dda_line').
        font (pygame.font.Font): La fuente usada para renderizar el texto.
        base_color (pygame.Color): El color de fondo normal del botón.
        hover_color (pygame.Color): El color de fondo cuando el ratón está encima.
        selected_border_color (pygame.Color): El color del borde cuando el botón está seleccionado.
        current_color (pygame.Color): El color de fondo actual (cambia con hover).
        text_surf (pygame.Surface): La superficie pre-renderizada del texto.
        text_rect (pygame.Rect): El rectángulo de la superficie del texto, centrado.
        is_hovered (bool): True si el ratón está actualmente sobre el botón.
        is_selected (bool): True si el botón está actualmente marcado como seleccionado.
    """
    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, identifier: str,
                 font: pygame.font.Font,
                 base_color: pygame.Color,
                 hover_color: Optional[pygame.Color] = None, # Usar Optional
                 selected_border_color: pygame.Color = pygame.Color("gold")):
        """
        Inicializa un nuevo botón.

        Args:
            x (int): Coordenada X de la esquina superior izquierda.
            y (int): Coordenada Y de la esquina superior izquierda.
            width (int): Ancho del botón.
            height (int): Alto del botón.
            text (str): Texto a mostrar en el botón.
            identifier (str): Identificador único para este botón.
            font (pygame.font.Font): Fuente para el texto.
            base_color (pygame.Color): Color de fondo base.
            hover_color (Optional[pygame.Color], optional): Color de fondo al pasar el ratón.
                                                            Si es None, usa base_color. Defaults to None.
            selected_border_color (pygame.Color, optional): Color del borde cuando está seleccionado.
                                                            Defaults to pygame.Color("gold").
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.identifier: str = identifier
        self.font: pygame.font.Font = font
        self.base_color: pygame.Color = base_color
        self.hover_color: pygame.Color = hover_color if hover_color else base_color
        self.selected_border_color: pygame.Color = selected_border_color
        self.current_color: pygame.Color = base_color

        # Pre-renderizar texto para eficiencia
        self.text_surf: pygame.Surface = self.font.render(self.text, True, pygame.Color("black"))
        self.text_rect: pygame.Rect = self.text_surf.get_rect(center=self.rect.center)

        self.is_hovered: bool = False
        self.is_selected: bool = False

    def check_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """
        Verifica si el ratón está sobre el botón y actualiza el estado y color.

        Args:
            mouse_pos (Tuple[int, int]): La posición actual del cursor del ratón (x, y).

        Returns:
            None
        """
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        # El color de fondo cambia solo con hover, no con selección
        self.current_color = self.hover_color if self.is_hovered else self.base_color

    def draw(self, surface: pygame.Surface) -> None:
        """
        Dibuja el botón en la superficie especificada.

        Incluye el fondo, borde normal, borde de selección (si aplica) y texto.

        Args:
            surface (pygame.Surface): La superficie de Pygame donde dibujar el botón.

        Returns:
            None
        """
        # Dibujar fondo del botón
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=5)

        # Dibujar borde normal
        pygame.draw.rect(surface, pygame.Color("darkgray"), self.rect, 1, border_radius=5)

        # Dibujar borde de selección si está activo
        if self.is_selected:
            pygame.draw.rect(surface, self.selected_border_color, self.rect, 3, border_radius=5) # Borde más grueso

        # Dibujar texto
        if self.text:
            surface.blit(self.text_surf, self.text_rect)

    def handle_click(self) -> Optional[str]:
         """
         Procesa un evento de clic. Retorna el identificador del botón si fue clickeado.

         Solo retorna el identificador si el cursor estaba sobre el botón (`is_hovered` es True)
         en el momento de llamar a esta función (generalmente después de un evento MOUSEBUTTONDOWN).

         Returns:
             Optional[str]: El identificador del botón si fue clickeado mientras estaba hover,
                            o None en caso contrario.
         """
         if self.is_hovered:
             # La acción específica (como imprimir o cambiar estado) se maneja fuera de Button.
             return self.identifier
         return None
