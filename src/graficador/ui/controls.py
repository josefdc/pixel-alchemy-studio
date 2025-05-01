# src/graficador/ui/controls.py
import pygame
from .. import config
from .button import Button # Asumiendo que creaste button.py

class Controls:
    """Representa el panel de control de la aplicación."""


    def __init__(self, x: int, y: int, width: int, height: int, bg_color: pygame.Color):
        self.rect = pygame.Rect(x, y, width, height)
        self.surface = pygame.Surface((width, height))
        self.bg_color = bg_color
        self._draw_background()
        self.buttons: list[Button] = []
        self.color_buttons: list[Button] = []
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 12)
        self._create_tool_buttons()
        self._create_color_buttons()
        print(f"Panel de Control inicializado en {self.rect} con color {bg_color}")

    def _create_tool_buttons(self):
        button_width = self.rect.width - 40
        button_height = 30
        button_x = 20
        current_y = 20
        spacing = 10
        tool_list = [
            ("pixel", "Píxel"), ("dda_line", "Línea DDA"),
            ("bresenham_line", "Línea Bresenham"), ("bresenham_circle", "Círculo Bresenham"),
            ("ellipse", "Elipse"), ("bezier_curve", "Curva Bézier"),
            ("triangle", "Triángulo"), ("rectangle", "Rectángulo"),
            ("polygon", "Polígono"), ("clear", "Limpiar (C)")
        ]
        for identifier, text in tool_list:
            button = Button(
                x=button_x, y=current_y,
                width=button_width, height=button_height,
                text=text, identifier=identifier,
                font=self.font, base_color=pygame.Color("lightblue"), hover_color=pygame.Color("dodgerblue")
            )
            self.buttons.append(button)
            current_y += button_height + spacing
        self.color_buttons_start_y = current_y + spacing

    def _create_color_buttons(self):
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
                text="", # Sin texto
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
        """Dibuja el fondo y borde del panel."""
        self.surface.fill(self.bg_color)
        # Dibujar un borde izquierdo para separarlo visualmente del lienzo
        pygame.draw.line(self.surface, config.DARK_GRAY, (0, 0), (0, self.rect.height), 2)

    # --- NUEVO: Método para actualizar estado hover ---
    def update(self, mouse_pos_relative: tuple[int, int] | None):
        """Actualiza el estado de los botones (hover)."""
        all_buttons = self.buttons + self.color_buttons # Combinar listas
        # Si el ratón está sobre el panel, calcula el hover de los botones
        if mouse_pos_relative:
            for button in all_buttons: # Iterar sobre todos
                button.check_hover(mouse_pos_relative)
        else: # Si el ratón no está sobre el panel, ningún botón está hover
             for button in all_buttons: # Iterar sobre todos
                 if button.is_hovered: # Solo actualiza si estaba hover antes
                    button.is_hovered = False
    # -------------------------------------------------

    # --- MODIFICADO: Método para manejar clics ---
    def handle_click(self, mouse_pos_relative: tuple[int, int]) -> tuple[str, str | pygame.Color] | None:
        """Maneja un clic dentro del panel.

        Retorna:
            - ('tool', identifier) si se hizo clic en un botón de herramienta.
            - ('color', color_value) si se hizo clic en un botón de color.
            - None si no se hizo clic en ningún botón.
        """
        # Primero, verificar botones de herramientas
        for button in self.buttons:
            clicked_id = button.handle_click() # handle_click de Button retorna identifier o None
            if clicked_id:
                return ("tool", clicked_id)

        # Si no se hizo clic en herramienta, verificar botones de color
        for button in self.color_buttons:
            clicked_name = button.handle_click() # handle_click de Button retorna identifier (nombre del color) o None
            if clicked_name:
                # Buscar el valor de color correspondiente al nombre (identificador)
                color_value = config.AVAILABLE_COLORS.get(clicked_name)
                if color_value:
                    return ("color", color_value)
                else:
                    # Esto no debería pasar si los identificadores son correctos
                    print(f"Advertencia: Color '{clicked_name}' no encontrado en config.AVAILABLE_COLORS")

        # Si no se hizo clic en ningún botón
        return None
    # ---------------------------------------

    def render(self, target_surface: pygame.Surface, current_tool: str, current_color: pygame.Color): # NUEVOS PARÁMETROS
        """Dibuja (blit) la superficie de este panel sobre la superficie destino."""
        # Redibuja el fondo por si acaso (importante si los botones cambian de color)
        self._draw_background()

        # --- NUEVO: Actualizar estado de selección antes de dibujar ---
        for btn in self.buttons:
            btn.is_selected = (btn.identifier == current_tool)
        for btn in self.color_buttons:
            # Comparamos por valor de color base, no por objeto pygame.Color directamente
            # ya que pueden ser instancias diferentes aunque representen el mismo color.
            btn.is_selected = (btn.base_color == current_color)
        # -----------------------------------------------------------

        # Dibuja cada botón sobre la superficie del panel
        all_buttons = self.buttons + self.color_buttons # Combinar listas
        for button in all_buttons: # Iterar sobre todos
            button.draw(self.surface)
        # Dibuja el panel completo (con botones) en la pantalla principal
        target_surface.blit(self.surface, self.rect.topleft)

    # Aquí añadiremos métodos para dibujar botones, texto, manejar clics, etc.