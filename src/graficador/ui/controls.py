"""
Controls module for the application interface.

Defines the Controls class that represents the control panel where users can select
tools, colors, and other application options.
"""

import pygame
from .. import config
from .button import Button

class Controls:
    """
    Application control panel interface.
    
    Manages tool buttons, color selection buttons, and handles user interactions
    within the control panel area.
    
    Attributes:
        rect (pygame.Rect): Rectangle defining panel position and size.
        surface (pygame.Surface): Pygame surface where the panel is drawn.
        bg_color (pygame.Color): Panel background color.
        font (pygame.font.Font): Normal font for buttons.
        font_small (pygame.font.Font): Small font for color buttons.
        buttons (list[Button]): List of tool buttons.
        color_buttons (list[Button]): List of color selection buttons.
    """

    def __init__(self, x: int, y: int, width: int, height: int, 
                 bg_color: pygame.Color, 
                 font_normal: pygame.font.Font,
                 font_small: pygame.font.Font):
        """
        Initialize the control panel.

        Args:
            x: X position of panel top-left corner.
            y: Y position of panel top-left corner.
            width: Panel width in pixels.
            height: Panel height in pixels.
            bg_color: Panel background color.
            font_normal: Normal font for tool buttons.
            font_small: Small font for color buttons.
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.surface = pygame.Surface((width, height))
        self.bg_color = bg_color
        
        self.font = font_normal
        self.font_small = font_small

        self._draw_background()
        self.buttons: list[Button] = []
        self.color_buttons: list[Button] = []
        
        self._create_tool_buttons()
        self._create_color_buttons()

    def _create_tool_buttons(self):
        """Create and configure tool selection buttons."""
        button_width = self.rect.width - 40
        button_height = 30
        button_x = 20
        current_y = 20
        spacing = 10
        
        tool_list = [
            ("pixel", "Pixel (P)"), 
            ("dda_line", "DDA Line (L)"),
            ("bresenham_line", "Bresenham Line (B)"), 
            ("bresenham_circle", "Circle (O)"), 
            ("ellipse", "Ellipse (E)"), 
            ("bezier_curve", "Bezier Curve (Z)"),
            ("triangle", "Triangle (T)"), 
            ("rectangle", "Rectangle (R)"),
            ("polygon", "Polygon (Y)"), 
            ("clear", "Clear (C)"),
            ("gemini_generate", config.GEMINI_BUTTON_TEXT),
            ("veo_generate", config.VEO_BUTTON_TEXT)
        ]
        
        for identifier, text in tool_list:
            button = Button(
                x=button_x, y=current_y,
                width=button_width, height=button_height,
                text=text, identifier=identifier,
                font=self.font,
                base_color=pygame.Color("lightblue"), 
                hover_color=pygame.Color("dodgerblue")
            )
            self.buttons.append(button)
            current_y += button_height + spacing
        
        self.color_buttons_start_y = current_y + spacing

    def _create_color_buttons(self):
        """Create and configure color selection buttons."""
        button_size = 25
        button_x = 20
        current_y = self.color_buttons_start_y
        spacing = 8
        max_width = self.rect.width - 2 * button_x
        num_cols = max(1, max_width // (button_size + spacing))
        col_count = 0
        
        for name, color_value in config.AVAILABLE_COLORS.items():
            button = Button(
                x=button_x + col_count * (button_size + spacing),
                y=current_y,
                width=button_size, height=button_size,
                text="",
                identifier=name,
                font=self.font_small,
                base_color=color_value,
                hover_color=color_value
            )
            self.color_buttons.append(button)
            col_count += 1
            if col_count >= num_cols:
                col_count = 0
                current_y += button_size + spacing

    def _draw_background(self):
        """Draw panel background and border."""
        self.surface.fill(self.bg_color)
        pygame.draw.line(self.surface, config.DARK_GRAY, (0, 0), (0, self.rect.height), 2)

    def update(self, mouse_pos_relative: tuple[int, int] | None):
        """
        Update button states based on mouse position.
        
        Args:
            mouse_pos_relative: Mouse position relative to panel, or None if outside.
        """
        all_buttons = self.buttons + self.color_buttons
        
        if mouse_pos_relative:
            for button in all_buttons:
                button.check_hover(mouse_pos_relative)
        else:
            for button in all_buttons:
                if button.is_hovered:
                    button.is_hovered = False

    def handle_click(self, mouse_pos_relative: tuple[int, int]) -> tuple[str, str | pygame.Color] | None:
        """
        Handle mouse clicks within the panel.

        Args:
            mouse_pos_relative: Mouse position relative to panel.

        Returns:
            Tuple containing ('tool', identifier) for tool buttons,
            ('color', color_value) for color buttons, or None if no button clicked.
        """
        for button in self.buttons:
            clicked_id = button.handle_click()
            if clicked_id:
                return ("tool", clicked_id)

        for button in self.color_buttons:
            clicked_name = button.handle_click()
            if clicked_name:
                color_value = config.AVAILABLE_COLORS.get(clicked_name)
                if color_value:
                    return ("color", color_value)
                else:
                    print(f"Warning: Color '{clicked_name}' not found in config.AVAILABLE_COLORS")

        return None

    def render(self, target_surface: pygame.Surface, current_tool: str, current_color: pygame.Color):
        """
        Render the control panel to target surface.
        
        Args:
            target_surface: Surface where panel will be rendered.
            current_tool: Currently selected tool identifier.
            current_color: Currently selected color.
        """
        self._draw_background()

        for btn in self.buttons:
            btn.is_selected = (btn.identifier == current_tool)
        for btn in self.color_buttons:
            btn.is_selected = (btn.base_color == current_color)

        all_buttons = self.buttons + self.color_buttons
        for button in all_buttons:
            button.draw(self.surface)
        
        target_surface.blit(self.surface, self.rect.topleft)