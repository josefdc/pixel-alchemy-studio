"""
User interface button module.

Defines the `Button` class that represents a simple interactive button
used in the application's graphical interface. Allows detection of
hover, clicks and maintains a visual selection state.
"""
import pygame
from typing import Optional, Tuple

class Button:
    """
    Represents a simple clickable button with text and selection state.

    Attributes:
        rect: Rectangle defining the button's position and size.
        text: Text displayed on the button.
        identifier: Unique identifier for the button (e.g., 'dda_line').
        font: Font used to render the text.
        base_color: Normal background color of the button.
        hover_color: Background color when mouse is over the button.
        selected_border_color: Border color when button is selected.
        current_color: Current background color (changes with hover).
        text_surf: Pre-rendered text surface.
        text_rect: Rectangle of the text surface, centered.
        is_hovered: True if mouse is currently over the button.
        is_selected: True if button is currently marked as selected.
    """
    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, identifier: str,
                 font: pygame.font.Font,
                 base_color: pygame.Color,
                 hover_color: Optional[pygame.Color] = None,
                 selected_border_color: pygame.Color = pygame.Color("gold")):
        """
        Initialize a new button.

        Args:
            x: X coordinate of the top-left corner.
            y: Y coordinate of the top-left corner.
            width: Width of the button.
            height: Height of the button.
            text: Text to display on the button.
            identifier: Unique identifier for this button.
            font: Font for the text.
            base_color: Base background color.
            hover_color: Background color when mouse hovers over.
                        If None, uses base_color. Defaults to None.
            selected_border_color: Border color when selected.
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

        self.text_surf: pygame.Surface = self.font.render(self.text, True, pygame.Color("black"))
        self.text_rect: pygame.Rect = self.text_surf.get_rect(center=self.rect.center)

        self.is_hovered: bool = False
        self.is_selected: bool = False

    def check_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """
        Check if mouse is over the button and update state and color.

        Args:
            mouse_pos: Current mouse cursor position (x, y).
        """
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.current_color = self.hover_color if self.is_hovered else self.base_color

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draw the button on the specified surface.

        Includes background, normal border, selection border (if applicable) and text.

        Args:
            surface: Pygame surface where to draw the button.
        """
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=5)

        pygame.draw.rect(surface, pygame.Color("darkgray"), self.rect, 1, border_radius=5)

        if self.is_selected:
            pygame.draw.rect(surface, self.selected_border_color, self.rect, 3, border_radius=5)

        if self.text:
            surface.blit(self.text_surf, self.text_rect)

    def handle_click(self) -> Optional[str]:
         """
         Process a click event. Returns the button identifier if it was clicked.

         Only returns the identifier if the cursor was over the button (`is_hovered` is True)
         at the time of calling this function (usually after a MOUSEBUTTONDOWN event).

         Returns:
             Button identifier if it was clicked while hovered, None otherwise.
         """
         if self.is_hovered:
             return self.identifier
         return None
