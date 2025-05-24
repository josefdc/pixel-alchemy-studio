"""
src/graficador/app.py
Módulo principal de la aplicación Graficador Geométrico Interactivo.

Este módulo contiene la clase `Application` que gestiona el ciclo de vida
de la aplicación Pygame, maneja los eventos de usuario, coordina el dibujo
en el lienzo (`Canvas`) y la interacción con los controles (`Controls`).
Integra los algoritmos de dibujo geométrico y las estructuras de datos
necesarias para la creación interactiva de figuras.
"""
# src/graficador/app.py (VERSIÓN FINAL CORREGIDA)

import pygame
import math
import os
from typing import List, Optional, Tuple, cast
import io
import traceback

from . import config
from .ui.canvas import Canvas
from .ui.controls import Controls
from .geometry.point import Point
from .algorithms.dda import dda_line
from .algorithms.bresenham import bresenham_line, bresenham_circle
from .algorithms.bezier import cubic_bezier
from .algorithms.shapes import midpoint_ellipse

# --- Importaciones para Gemini (CORREGIDAS) ---
try:
    from google import genai
    from google.genai import types
    from PIL import Image as PILImage
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    PILImage = None
    GEMINI_AVAILABLE = False
    print("ADVERTENCIA: Las librerías 'google-genai' y/o 'Pillow' no están instaladas. La funcionalidad de IA no estará disponible.")

class Application:
    """
    Clase principal que encapsula la lógica de la aplicación gráfica.

    Gestiona la inicialización de Pygame, la ventana principal, el lienzo de dibujo,
    el panel de controles, el bucle principal de eventos, la actualización del estado
    y el renderizado de la interfaz. Mantiene el estado de la herramienta actual
    y los puntos necesarios para dibujar las diferentes figuras geométricas.

    Attributes:
        screen (pygame.Surface): La superficie principal de la ventana de Pygame.
        clock (pygame.time.Clock): Reloj de Pygame para controlar los FPS.
        is_running (bool): Flag que indica si el bucle principal debe continuar.
        canvas (Canvas): Instancia del lienzo de dibujo.
        controls (Controls): Instancia del panel de controles.
        current_tool (str): Identificador de la herramienta de dibujo activa.
        line_start_point (Optional[Point]): Punto de inicio para dibujar líneas.
        circle_center (Optional[Point]): Punto central para dibujar círculos.
        bezier_points (List[Point]): Lista de puntos de control para curvas Bézier.
        triangle_points (List[Point]): Lista de vértices para dibujar triángulos.
        rectangle_points (List[Point]): Lista de esquinas opuestas para dibujar rectángulos.
        polygon_points (List[Point]): Lista de vértices para dibujar polígonos.
        ellipse_points (List[Point]): Lista de puntos (centro, borde) para dibujar elipses.
        draw_color (pygame.Color): Color de dibujo actualmente seleccionado.
    """
    def __init__(self) -> None:
        """Inicializa la aplicación, Pygame, la pantalla, el lienzo y los controles."""
        pygame.init()
        # --- Fuentes ---
        if not pygame.font.get_init():
            pygame.font.init()
        self.ui_font_small: pygame.font.Font = pygame.font.SysFont("Arial", 12)
        self.ui_font_normal: pygame.font.Font = pygame.font.SysFont("Arial", 16)

        self.screen: pygame.Surface = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.is_running: bool = True

        # Crear el lienzo
        self.canvas: Canvas = Canvas(
            config.CANVAS_X, config.CANVAS_Y,
            config.CANVAS_WIDTH, config.CANVAS_HEIGHT,
            config.CANVAS_BG_COLOR
        )

        self.controls: Controls = Controls(
            config.CONTROL_PANEL_X, config.CONTROL_PANEL_Y,
            config.CONTROL_PANEL_WIDTH, config.CONTROL_PANEL_HEIGHT,
            config.CONTROL_PANEL_BG_COLOR,
            self.ui_font_normal,  # Pasar la fuente normal
            self.ui_font_small   # Pasar la fuente pequeña
        )

        self.current_tool: str = "pixel" # Herramienta inicial por defecto
        # Estados para las diferentes herramientas
        self.line_start_point: Optional[Point] = None
        self.circle_center: Optional[Point] = None
        self.bezier_points: List[Point] = []
        self.triangle_points: List[Point] = []
        self.rectangle_points: List[Point] = [] # Usaremos 2 puntos para definirlo
        self.polygon_points: List[Point] = []
        self.ellipse_points: List[Point] = [] # Usaremos 2 puntos (centro y un punto en borde)
        self.draw_color: pygame.Color = config.BLACK # Color de dibujo por defecto
        self.is_drawing: bool = False  # Flag para saber si se está dibujando
        self.last_mouse_pos_for_pixel_draw: Optional[Point] = None
        # --- Nuevos atributos para la funcionalidad de IA ---
        # En __init__
        self.gemini_client: Optional[genai.Client] = None # Nuevo nombre y tipo  # Para la instancia del GenerativeModel
        self.is_typing_prompt: bool = False
        self.current_prompt_text: str = ""
        self.generated_image_surface: Optional[pygame.Surface] = None
        self.gemini_status_message: str = config.GEMINI_STATUS_DEFAULT
        self.is_veo_processing: bool = False
        self.veo_operation_name: Optional[str] = None
        self.current_veo_operation_object: Optional[any] = None
        self.VEO_POLLING_EVENT = pygame.USEREVENT + 1
        self._initialize_gemini()

        print(f"Aplicación inicializada. Herramienta actual: {self.current_tool}")
        # Después (Correcto)
        if GEMINI_AVAILABLE and self.gemini_client: # Usar self.gemini_client
            print(f"Cliente de Gemini listo para usar con el modelo: {config.GEMINI_MODEL_NAME}")
        else:
            print(f"Estado de Gemini al finalizar __init__: {self.gemini_status_message}")


    def _draw_bresenham_circle(self, center: Point, radius: int) -> None:
        """
        Dibuja un círculo utilizando el algoritmo de Bresenham para círculos.

        Args:
            center (Point): Centro del círculo (coordenadas relativas al lienzo).
            radius (int): Radio del círculo en píxeles.
        """
        if radius >= 0:
            bresenham_circle(center, radius, self.canvas.draw_pixel, self.draw_color)
        else:
            print("Error: Radio del círculo no puede ser negativo.")


    def _draw_bezier_curve(self, points: List[Point]) -> None:
        """
        Dibuja una curva Bézier cúbica utilizando el algoritmo correspondiente.

        La curva se dibuja segmentando la curva y dibujando líneas rectas
        (usando Bresenham) entre los puntos calculados.

        Args:
            points (List[Point]): Lista de 4 puntos de control (P0, P1, P2, P3)
                                  en coordenadas relativas al lienzo.
        """
        if len(points) == 4:
            # Usamos bresenham como función para dibujar los segmentos
            cubic_bezier(points[0], points[1], points[2], points[3],
                         self._draw_bresenham_line, # Pasar el método helper
                         self.draw_color)
        # else: # No es necesario dibujar puntos de control aquí, se hace en _render
        #     pass

    def _draw_triangle(self, points: List[Point]) -> None:
        """
        Dibuja un triángulo conectando los 3 vértices dados con líneas (Bresenham).

        Args:
            points (List[Point]): Lista de 3 puntos (vértices) del triángulo
                                  en coordenadas relativas al lienzo.
        """
        if len(points) == 3:
            print(f"Dibujando Triángulo: {points[0]}, {points[1]}, {points[2]}")
            self._draw_bresenham_line(points[0], points[1], self.draw_color)
            self._draw_bresenham_line(points[1], points[2], self.draw_color)
            self._draw_bresenham_line(points[2], points[0], self.draw_color) # Cerrar

    def _draw_rectangle(self, p_start: Point, p_end: Point) -> None:
        """
        Dibuja un rectángulo definido por dos esquinas opuestas usando líneas (Bresenham).

        Args:
            p_start (Point): Primera esquina del rectángulo (relativa al lienzo).
            p_end (Point): Esquina opuesta del rectángulo (relativa al lienzo).
        """
        x0, y0 = p_start.x, p_start.y
        x1, y1 = p_end.x, p_end.y
        # Crear los otros dos puntos
        p1 = Point(x1, y0)
        p3 = Point(x0, y1)
        print(f"Dibujando Rectángulo: P0={p_start}, P1={p1}, P2={p_end}, P3={p3}")
        # Dibujar los 4 lados usando Bresenham
        self._draw_bresenham_line(p_start, p1, self.draw_color)
        self._draw_bresenham_line(p1, p_end, self.draw_color)
        self._draw_bresenham_line(p_end, p3, self.draw_color)
        self._draw_bresenham_line(p3, p_start, self.draw_color) # Cerrar el rectángulo


    def _draw_polygon(self, points: List[Point]) -> None:
        """
        Dibuja los segmentos de un polígono conectando los vértices dados con líneas (Bresenham).

        Nota: Esta función dibuja los segmentos a medida que se añaden puntos.
        El cierre del polígono (último vértice al primero) se maneja en `_handle_events`.

        Args:
            points (List[Point]): Lista de vértices del polígono hasta el momento
                                  (coordenadas relativas al lienzo).
        """
        if len(points) < 2: # Necesitamos al menos 2 para empezar a dibujar lados
            return
        # Dibujar el último segmento añadido (entre el penúltimo y el último punto)
        # El bucle anterior en la versión original era redundante aquí,
        # ya que los segmentos anteriores ya se dibujaron en llamadas previas.
        start_point = points[-2]
        end_point = points[-1]
        print(f"  Dibujando lado Polígono: {start_point} -> {end_point}")
        self._draw_bresenham_line(start_point, end_point, self.draw_color)


    def _draw_ellipse(self, center: Point, rx: int, ry: int) -> None:
        """
        Dibuja una elipse utilizando el algoritmo del punto medio.

        Args:
            center (Point): Centro de la elipse (coordenadas relativas al lienzo).
            rx (int): Radio horizontal (semieje mayor o menor) en píxeles.
            ry (int): Radio vertical (semieje mayor o menor) en píxeles.
        """
        if rx >= 0 and ry >= 0:
            midpoint_ellipse(center, rx, ry, self.canvas.draw_pixel, self.draw_color)
        else:
            print("Error: Radios de la elipse no pueden ser negativos.")


    def _initialize_gemini(self) -> None:
        """Inicializa el cliente de Gemini si las librerías y la API key están disponibles."""
        if not GEMINI_AVAILABLE:
            self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            print(f"ADVERTENCIA: {self.gemini_status_message} Las librerías de IA no están disponibles.") # Añadido un print para claridad
            return

        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                self.gemini_status_message = config.GEMINI_STATUS_ERROR_API_KEY
                print(f"ADVERTENCIA: {self.gemini_status_message}")
                return

            # Crear el cliente de la nueva SDK google-genai
            self.gemini_client = genai.Client(api_key=api_key)
            self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
            print("Cliente de Gemini inicializado con éxito usando 'google-genai' SDK.")

        except Exception as e:
            self.gemini_status_message = f"Error inicializando Gemini: {str(e)[:150]}"
            print(f"ERROR GENERAL EN _initialize_gemini: {self.gemini_status_message}") # Mensaje de error más específico
            traceback.print_exc() # Imprimir el traceback completo para más detalles del error
            self.gemini_client = None # Asegurarse que gemini_client sea None en caso de error
            
    def _reset_drawing_states(self) -> None:
        """Resetea solo los estados de dibujo pendientes (puntos, etc.)."""
        print("Reseteando solo estados de dibujo pendientes...")
        self.line_start_point = None
        self.circle_center = None
        self.bezier_points = []
        self.triangle_points = []
        self.rectangle_points = []
        self.polygon_points = []
        self.ellipse_points = []
        # NO resetea is_typing_prompt, current_prompt_text ni gemini_status_message

    def _reset_all_states(self) -> None:
            """Resetea todos los estados de dibujo Y de IA."""
            self._reset_drawing_states()
            self.is_typing_prompt = False
            self.current_prompt_text = ""
            
            # --- AÑADIR RESETEO DE ESTADOS DE VEO ---
            self.current_veo_operation_object = None
            if self.is_veo_processing: # Si Veo estaba procesando, detener el polling
                pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
            self.is_veo_processing = False
            self.veo_operation_name = None
            # --- FIN RESETEO VEO ---

            if self.gemini_client:
                self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
            else: # Si el cliente no está inicializado, mostrar el mensaje de error de librería/API Key
                if not GEMINI_AVAILABLE:
                    self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
                elif not os.environ.get("GOOGLE_API_KEY"):
                    self.gemini_status_message = config.GEMINI_STATUS_ERROR_API_KEY
                else: # Otro error de inicialización
                    pass # gemini_status_message ya tendrá el error de _initialize_gemini
            
            print(f"Estados COMPLETOS reseteados. Estado actual de IA: {self.gemini_status_message}")

    def _draw_dda_line(self, p1: Point, p2: Point, color: pygame.Color) -> None:
        """
        Dibuja una línea utilizando el algoritmo DDA.

        Args:
            p1 (Point): Punto de inicio de la línea (coordenadas relativas al lienzo).
            p2 (Point): Punto final de la línea (coordenadas relativas al lienzo).
            color (pygame.Color): Color de la línea.
        """
        dda_line(p1, p2, self.canvas.draw_pixel, color)

    def _draw_bresenham_line(self, p1: Point, p2: Point, color: pygame.Color) -> None:
        """
        Dibuja una línea utilizando el algoritmo de Bresenham.

        Args:
            p1 (Point): Punto de inicio de la línea (coordenadas relativas al lienzo).
            p2 (Point): Punto final de la línea (coordenadas relativas al lienzo).
            color (pygame.Color): Color de la línea.
        """
        bresenham_line(p1, p2, self.canvas.draw_pixel, color)

    def _draw_bresenham_circle(self, center: Point, radius: int) -> None:
        """
        Dibuja un círculo utilizando el algoritmo de Bresenham para círculos.

        Args:
            center (Point): Centro del círculo (coordenadas relativas al lienzo).
            radius (int): Radio del círculo en píxeles.
        """
        if radius >= 0:
            bresenham_circle(center, radius, self.canvas.draw_pixel, self.draw_color)
        else:
            print("Error: Radio del círculo no puede ser negativo.")


    def _draw_bezier_curve(self, points: List[Point]) -> None:
        """
        Dibuja una curva Bézier cúbica utilizando el algoritmo correspondiente.

        La curva se dibuja segmentando la curva y dibujando líneas rectas
        (usando Bresenham) entre los puntos calculados.

        Args:
            points (List[Point]): Lista de 4 puntos de control (P0, P1, P2, P3)
                                  en coordenadas relativas al lienzo.
        """
        if len(points) == 4:
            # Usamos bresenham como función para dibujar los segmentos
            cubic_bezier(points[0], points[1], points[2], points[3],
                         self._draw_bresenham_line, # Pasar el método helper
                         self.draw_color)
        # else: # No es necesario dibujar puntos de control aquí, se hace en _render
        #     pass

    def _draw_triangle(self, points: List[Point]) -> None:
        """
        Dibuja un triángulo conectando los 3 vértices dados con líneas (Bresenham).

        Args:
            points (List[Point]): Lista de 3 puntos (vértices) del triángulo
                                  en coordenadas relativas al lienzo.
        """
        if len(points) == 3:
            print(f"Dibujando Triángulo: {points[0]}, {points[1]}, {points[2]}")
            self._draw_bresenham_line(points[0], points[1], self.draw_color)
            self._draw_bresenham_line(points[1], points[2], self.draw_color)
            self._draw_bresenham_line(points[2], points[0], self.draw_color) # Cerrar

    def _draw_rectangle(self, p_start: Point, p_end: Point) -> None:
        """
        Dibuja un rectángulo definido por dos esquinas opuestas usando líneas (Bresenham).

        Args:
            p_start (Point): Primera esquina del rectángulo (relativa al lienzo).
            p_end (Point): Esquina opuesta del rectángulo (relativa al lienzo).
        """
        x0, y0 = p_start.x, p_start.y
        x1, y1 = p_end.x, p_end.y
        # Crear los otros dos puntos
        p1 = Point(x1, y0)
        p3 = Point(x0, y1)
        print(f"Dibujando Rectángulo: P0={p_start}, P1={p1}, P2={p_end}, P3={p3}")
        # Dibujar los 4 lados usando Bresenham
        self._draw_bresenham_line(p_start, p1, self.draw_color)
        self._draw_bresenham_line(p1, p_end, self.draw_color)
        self._draw_bresenham_line(p_end, p3, self.draw_color)
        self._draw_bresenham_line(p3, p_start, self.draw_color) # Cerrar el rectángulo


    def _draw_polygon(self, points: List[Point]) -> None:
        """
        Dibuja los segmentos de un polígono conectando los vértices dados con líneas (Bresenham).

        Nota: Esta función dibuja los segmentos a medida que se añaden puntos.
        El cierre del polígono (último vértice al primero) se maneja en `_handle_events`.

        Args:
            points (List[Point]): Lista de vértices del polígono hasta el momento
                                  (coordenadas relativas al lienzo).
        """
        if len(points) < 2: # Necesitamos al menos 2 para empezar a dibujar lados
            return
        # Dibujar el último segmento añadido (entre el penúltimo y el último punto)
        # El bucle anterior en la versión original era redundante aquí,
        # ya que los segmentos anteriores ya se dibujaron en llamadas previas.
        start_point = points[-2]
        end_point = points[-1]
        print(f"  Dibujando lado Polígono: {start_point} -> {end_point}")
        self._draw_bresenham_line(start_point, end_point, self.draw_color)


    def _draw_ellipse(self, center: Point, rx: int, ry: int) -> None:
        """
        Dibuja una elipse utilizando el algoritmo del punto medio.

        Args:
            center (Point): Centro de la elipse (coordenadas relativas al lienzo).
            rx (int): Radio horizontal (semieje mayor o menor) en píxeles.
            ry (int): Radio vertical (semieje mayor o menor) en píxeles.
        """
        if rx >= 0 and ry >= 0:
            midpoint_ellipse(center, rx, ry, self.canvas.draw_pixel, self.draw_color)
        else:
            print("Error: Radios de la elipse no pueden ser negativos.")

    def _reset_drawing_states(self) -> None:
        """Resetea solo los estados de dibujo pendientes (puntos, etc.)."""
        print("Reseteando solo estados de dibujo pendientes...")
        self.line_start_point = None
        self.circle_center = None
        self.bezier_points = []
        self.triangle_points = []
        self.rectangle_points = []
        self.polygon_points = []
        self.ellipse_points = []
        # NO resetea is_typing_prompt, current_prompt_text ni gemini_status_message

    def _reset_all_states(self) -> None:
        """Resetea todos los estados de dibujo Y de IA."""
        self._reset_drawing_states()  # Llama al nuevo método para los puntos
        self.is_typing_prompt = False
        self.current_prompt_text = ""
        if self.gemini_model_instance:  # Restaurar mensaje solo si la IA está OK
            self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
        print(f"Estados COMPLETOS reseteados. Estado actual de Gemini: {self.gemini_status_message}")

    def _capture_canvas_as_pil_image(self) -> Optional[PILImage.Image]:
        """
        Captura la superficie actual del lienzo y la convierte en un objeto PIL.Image.

        Returns:
            Optional[PILImage.Image]: La imagen PIL del lienzo, o None si ocurre un error.
        """
        if not PILImage:  # Comprobar si Pillow está disponible
            self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            print(f"Error: {self.gemini_status_message}")
            return None
        try:
            canvas_surface = self.canvas.surface
            image_bytes_io = io.BytesIO()
            pygame.image.save(canvas_surface, image_bytes_io, "PNG")
            image_bytes_io.seek(0)
            pil_image = PILImage.open(image_bytes_io)
            print("Lienzo capturado como imagen PIL.")
            return pil_image
        except Exception as e:
            self.gemini_status_message = f"Error capturando canvas: {str(e)[:100]}"
            print(f"Error: {self.gemini_status_message}")
            return None

    def _draw_dda_line(self, p1: Point, p2: Point, color: pygame.Color) -> None:
        """
        Dibuja una línea utilizando el algoritmo DDA.

        Args:
            p1 (Point): Punto de inicio de la línea (coordenadas relativas al lienzo).
            p2 (Point): Punto final de la línea (coordenadas relativas al lienzo).
            color (pygame.Color): Color de la línea.
        """
        dda_line(p1, p2, self.canvas.draw_pixel, color)


    def _draw_bresenham_circle(self, center: Point, radius: int) -> None:
        """
        Dibuja un círculo utilizando el algoritmo de Bresenham para círculos.

        Args:
            center (Point): Centro del círculo (coordenadas relativas al lienzo).
            radius (int): Radio del círculo en píxeles.
        """
        if radius >= 0:
            bresenham_circle(center, radius, self.canvas.draw_pixel, self.draw_color)
        else:
            print("Error: Radio del círculo no puede ser negativo.")


    def _draw_bezier_curve(self, points: List[Point]) -> None:
        """
        Dibuja una curva Bézier cúbica utilizando el algoritmo correspondiente.

        La curva se dibuja segmentando la curva y dibujando líneas rectas
        (usando Bresenham) entre los puntos calculados.

        Args:
            points (List[Point]): Lista de 4 puntos de control (P0, P1, P2, P3)
                                  en coordenadas relativas al lienzo.
        """
        if len(points) == 4:
            # Usamos bresenham como función para dibujar los segmentos
            cubic_bezier(points[0], points[1], points[2], points[3],
                         self._draw_bresenham_line, # Pasar el método helper
                         self.draw_color)
        # else: # No es necesario dibujar puntos de control aquí, se hace en _render
        #     pass

    def _draw_triangle(self, points: List[Point]) -> None:
        """
        Dibuja un triángulo conectando los 3 vértices dados con líneas (Bresenham).

        Args:
            points (List[Point): Lista de 3 puntos (vértices) del triángulo
                                  en coordenadas relativas al lienzo.
        """
        if len(points) == 3:
            print(f"Dibujando Triángulo: {points[0]}, {points[1]}, {points[2]}")
            self._draw_bresenham_line(points[0], points[1], self.draw_color)
            self._draw_bresenham_line(points[1], points[2], self.draw_color)
            self._draw_bresenham_line(points[2], points[0], self.draw_color) # Cerrar

    def _draw_rectangle(self, p_start: Point, p_end: Point) -> None:
        """
        Dibuja un rectángulo definido por dos esquinas opuestas usando líneas (Bresenham).

        Args:
            p_start (Point): Primera esquina del rectángulo (relativa al lienzo).
            p_end (Point): Esquina opuesta del rectángulo (relativa al lienzo).
        """
        x0, y0 = p_start.x, p_start.y
        x1, y1 = p_end.x, p_end.y
        # Crear los otros dos puntos
        p1 = Point(x1, y0)
        p3 = Point(x0, y1)
        print(f"Dibujando Rectángulo: P0={p_start}, P1={p1}, P2={p_end}, P3={p3}")
        # Dibujar los 4 lados usando Bresenham
        self._draw_bresenham_line(p_start, p1, self.draw_color)
        self._draw_bresenham_line(p1, p_end, self.draw_color)
        self._draw_bresenham_line(p_end, p3, self.draw_color)
        self._draw_bresenham_line(p3, p_start, self.draw_color) # Cerrar el rectángulo


    def _draw_polygon(self, points: List[Point]) -> None:
        """
        Dibuja los segmentos de un polígono conectando los vértices dados con líneas (Bresenham).

        Nota: Esta función dibuja los segmentos a medida que se añaden puntos.
        El cierre del polígono (último vértice al primero) se maneja en `_handle_events`.

        Args:
            points (List[Point]): Lista de vértices del polígono hasta el momento
                                  (coordenadas relativas al lienzo).
        """
        if len(points) < 2: # Necesitamos al menos 2 para empezar a dibujar lados
            return
        # Dibujar el último segmento añadido (entre el penúltimo y el último punto)
        # El bucle anterior en la versión original era redundante aquí,
        # ya que los segmentos anteriores ya se dibujaron en llamadas previas.
        start_point = points[-2]
        end_point = points[-1]
        print(f"  Dibujando lado Polígono: {start_point} -> {end_point}")
        self._draw_bresenham_line(start_point, end_point, self.draw_color)


    def _draw_ellipse(self, center: Point, rx: int, ry: int) -> None:
        """
        Dibuja una elipse utilizando el algoritmo del punto medio.

        Args:
            center (Point): Centro de la elipse (coordenadas relativas al lienzo).
            rx (int): Radio horizontal (semieje mayor o menor) en píxeles.
            ry (int): Radio vertical (semieje mayor o menor) en píxeles.
        """
        if rx >= 0 and ry >= 0:
            midpoint_ellipse(center, rx, ry, self.canvas.draw_pixel, self.draw_color)
        else:
            print("Error: Radios de la elipse no pueden ser negativos.")

    def _reset_drawing_states(self) -> None:
        """Resetea solo los estados de dibujo pendientes (puntos, etc.)."""
        print("Reseteando solo estados de dibujo pendientes...")
        self.line_start_point = None
        self.circle_center = None
        self.bezier_points = []
        self.triangle_points = []
        self.rectangle_points = []
        self.polygon_points = []
        self.ellipse_points = []
        # NO resetea is_typing_prompt, current_prompt_text ni gemini_status_message

    def _reset_all_states(self) -> None:
        """Resetea todos los estados de dibujo Y de IA."""
        self._reset_drawing_states()  # Llama al nuevo método para los puntos
        self.is_typing_prompt = False
        self.current_prompt_text = ""
        if self.gemini_model_instance:  # Restaurar mensaje solo si la IA está OK
            self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
        print(f"Estados COMPLETOS reseteados. Estado actual de Gemini: {self.gemini_status_message}")

    def _capture_canvas_as_pil_image(self) -> Optional[PILImage.Image]:
        """
        Captura la superficie actual del lienzo y la convierte en un objeto PIL.Image.

        Returns:
            Optional[PILImage.Image]: La imagen PIL del lienzo, o None si ocurre un error.
        """
        if not PILImage:  # Comprobar si Pillow está disponible
            self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            print(f"Error: {self.gemini_status_message}")
            return None
        try:
            canvas_surface = self.canvas.surface
            image_bytes_io = io.BytesIO()
            pygame.image.save(canvas_surface, image_bytes_io, "PNG")
            image_bytes_io.seek(0)
            pil_image = PILImage.open(image_bytes_io)
            print("Lienzo capturado como imagen PIL.")
            return pil_image
        except Exception as e:
            self.gemini_status_message = f"Error capturando canvas: {str(e)[:100]}"
            print(f"Error: {self.gemini_status_message}")
            return None

    def _handle_events(self) -> None:
        """
        Maneja los eventos de entrada del usuario (teclado, ratón),
        incluyendo la lógica para iniciar y monitorear la generación de video con Veo.
        """
        mouse_pos_on_controls: Optional[Tuple[int, int]] = None
        abs_mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()
        if self.controls.rect.collidepoint(abs_mouse_pos):
            mouse_pos_on_controls = (abs_mouse_pos[0] - self.controls.rect.x,
                                     abs_mouse_pos[1] - self.controls.rect.y)

        # Actualizar estado hover de botones del panel de control
        # Hacemos esto antes del bucle de eventos para que los botones se dibujen correctamente
        # incluso si el bucle de eventos se salta por is_veo_processing
        self.controls.update(mouse_pos_on_controls)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                continue

            # Manejar el evento de polling de Veo primero y continuar
            if event.type == self.VEO_POLLING_EVENT: # Asegúrate que self.VEO_POLLING_EVENT esté definido en __init__
                self._poll_veo_status() # Asegúrate que _poll_veo_status esté implementado
                continue

            # Si Veo está procesando, la mayoría de los otros eventos se ignoran para evitar conflictos.
            # Se permite QUIT (manejado arriba) y quizás un futuro ESCAPE para cancelar Veo.
            if self.is_veo_processing:
                # Podrías añadir un manejo de K_ESCAPE aquí si quieres intentar cancelar Veo
                # if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                #     print("Intento de cancelar Veo...")
                #     pygame.time.set_timer(self.VEO_POLLING_EVENT, 0) # Detener polling
                #     self.is_veo_processing = False
                #     self.veo_operation_name = None
                #     self.gemini_status_message = "Generación de Veo cancelada por el usuario."
                #     self._reset_drawing_states() # Limpiar puntos de dibujo si es necesario
                continue # Ignorar otros eventos mientras Veo está ocupado

            # Manejo de entrada de prompt para Gemini (si está activo)
            if self.is_typing_prompt and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.is_typing_prompt = False
                    prompt_final = self.current_prompt_text.strip()
                    if not prompt_final:
                        self.gemini_status_message = "Prompt vacío. Intenta de nuevo."
                        print("Intento de generación con prompt vacío.")
                    elif not self.gemini_client: # Corregido: usar self.gemini_client
                        self.gemini_status_message = "Error: IA no inicializada."
                        print("Intento de generación sin cliente de IA.")
                    else:
                        print(f"Prompt finalizado: '{prompt_final}'. Iniciando generación de imagen...")
                        self.gemini_status_message = config.GEMINI_STATUS_LOADING
                        # self.generated_image_surface = None # Esta línea ya no es necesaria aquí
                        pil_image = self._capture_canvas_as_pil_image()
                        # Gemini siempre espera una imagen de entrada en tu flujo actual.
                        # Si no hay imagen, ¿debería enviar solo texto o mostrar error?
                        # Por ahora, si no hay pil_image, _call_gemini_api podría manejarlo o mostrar un error.
                        if pil_image:
                           self._call_gemini_api(pil_image, prompt_final)
                        else:
                            # Considera si quieres llamar a Gemini solo con texto si no hay imagen
                            # o mostrar un mensaje de que se necesita un dibujo.
                            # Por coherencia con tu lógica actual en _call_gemini_api, que espera una imagen:
                            self.gemini_status_message = "Error: No se pudo capturar el lienzo para Gemini."
                            print(self.gemini_status_message)

                elif event.key == pygame.K_BACKSPACE:
                    self.current_prompt_text = self.current_prompt_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    print("Entrada de prompt cancelada.")
                    self._reset_all_states() # Esto resetea is_typing_prompt
                else:
                    if len(self.current_prompt_text) < 200: # Límite de longitud del prompt
                        self.current_prompt_text += event.unicode
                continue # Importante: Saltar el resto del manejo de eventos si se procesó una tecla para el prompt

            # Manejo de clics del ratón
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic izquierdo
                    if mouse_pos_on_controls: # Clic en el panel de controles
                        click_result = self.controls.handle_click(mouse_pos_on_controls)
                        if click_result:
                            click_type, value = click_result
                            if click_type == "tool":
                                tool_id = cast(str, value)

                                if tool_id == "veo_generate": # NUEVO: Botón Veo
                                    if not self.is_veo_processing and not self.is_typing_prompt:
                                        if self.gemini_client:
                                            self.current_tool = tool_id # Actualizar herramienta seleccionada
                                            # El prompt se tomará de self.current_prompt_text si está disponible
                                            # La imagen del lienzo se capturará en _start_veo_generation
                                            self._start_veo_generation() # Implementar este método
                                        else:
                                            self.gemini_status_message = config.VEO_STATUS_ERROR_API
                                    else:
                                        self.gemini_status_message = config.VEO_STATUS_PROCESSING_ANOTHER_OP
                                    print(self.gemini_status_message)

                                elif tool_id == "gemini_generate":
                                    if GEMINI_AVAILABLE and self.gemini_client: # Corregido
                                        if not self.is_typing_prompt: # Solo si no estamos ya escribiendo
                                            self.is_typing_prompt = True
                                            self.current_prompt_text = ""
                                            # self.generated_image_surface = None # Ya no se usa esta variable así
                                            self.gemini_status_message = config.PROMPT_INPUT_PLACEHOLDER
                                            self.current_tool = "gemini_generate" # Seleccionar la herramienta
                                            self._reset_drawing_states()
                                            print("Modo escritura de prompt para Gemini activado.")
                                    else:
                                        self.gemini_status_message = "Error: IA no disponible/configurada."
                                    print(self.gemini_status_message)

                                elif tool_id == "clear":
                                    self.canvas.clear()
                                    # self.generated_image_surface = None # Ya no se usa esta variable así
                                    self._reset_all_states() # Esto ya debería manejar el reseteo de Veo
                                    print("Lienzo limpiado y estados reseteados.")
                                    # Adicional para Veo, aunque _reset_all_states debería cubrirlo:
                                    if self.is_veo_processing:
                                        pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
                                        self.is_veo_processing = False
                                        self.veo_operation_name = None
                                        self.gemini_status_message = "Procesamiento de Veo cancelado por limpieza."
                                        print(self.gemini_status_message)


                                elif self.current_tool != tool_id: # Cambio a otra herramienta de dibujo
                                    if self.is_typing_prompt: # Si estábamos escribiendo prompt, cancelar
                                        self._reset_all_states()
                                    self.current_tool = tool_id
                                    self._reset_drawing_states()
                                    print(f"Herramienta cambiada a: {tool_id}")
                                else: # Clic en la misma herramienta (generalmente para resetear puntos)
                                    self._reset_drawing_states()
                                    print(f"Puntos de la herramienta {tool_id} reseteados.")

                            elif click_type == "color":
                                color_value = cast(pygame.Color, value)
                                if self.draw_color != color_value:
                                    self.draw_color = color_value
                                    print(f"Color de dibujo cambiado a: {color_value}")
                    
                    elif self.canvas.rect.collidepoint(abs_mouse_pos): # Clic en el lienzo
                        # Esta sección solo se alcanza si no estamos en is_typing_prompt ni is_veo_processing
                        relative_x = abs_mouse_pos[0] - self.canvas.rect.x
                        relative_y = abs_mouse_pos[1] - self.canvas.rect.y
                        current_point = Point(relative_x, relative_y)
                        
                        if self.current_tool == "pixel":
                            self.is_drawing = True
                            self.canvas.draw_pixel(current_point.x, current_point.y, self.draw_color)
                            self.last_mouse_pos_for_pixel_draw = current_point
                        
                        elif self.current_tool in ["dda_line", "bresenham_line"]:
                            if not self.line_start_point:
                                self.line_start_point = current_point
                            else:
                                if self.current_tool == "dda_line":
                                    self._draw_dda_line(self.line_start_point, current_point, self.draw_color)
                                else: # bresenham_line
                                    self._draw_bresenham_line(self.line_start_point, current_point, self.draw_color)
                                self.line_start_point = None
                        
                        elif self.current_tool == "bresenham_circle":
                            if not self.circle_center:
                                self.circle_center = current_point
                            else:
                                dx = current_point.x - self.circle_center.x
                                dy = current_point.y - self.circle_center.y
                                radius = int(math.sqrt(dx*dx + dy*dy))
                                self._draw_bresenham_circle(self.circle_center, radius)
                                self.circle_center = None
                        
                        elif self.current_tool == "ellipse":
                            self.ellipse_points.append(current_point)
                            if len(self.ellipse_points) == 2: # Centro y punto en el borde
                                center = self.ellipse_points[0]
                                rx = abs(current_point.x - center.x)
                                ry = abs(current_point.y - center.y)
                                self._draw_ellipse(center, rx, ry)
                                self.ellipse_points = []
                        
                        elif self.current_tool == "bezier_curve":
                            self.bezier_points.append(current_point)
                            if len(self.bezier_points) == 4:
                                self._draw_bezier_curve(self.bezier_points)
                                self.bezier_points = []
                        
                        elif self.current_tool == "triangle":
                            self.triangle_points.append(current_point)
                            if len(self.triangle_points) == 3:
                                self._draw_triangle(self.triangle_points)
                                self.triangle_points = []
                        
                        elif self.current_tool == "rectangle":
                            self.rectangle_points.append(current_point)
                            if len(self.rectangle_points) == 2: # Esquina inicial y final
                                self._draw_rectangle(self.rectangle_points[0], self.rectangle_points[1])
                                self.rectangle_points = []
                        
                        elif self.current_tool == "polygon":
                            should_close = False
                            if len(self.polygon_points) >= 2: # Necesita al menos 2 puntos para considerar cerrar en el tercero
                                first_point = self.polygon_points[0]
                                distance_to_first = math.sqrt(
                                    (current_point.x - first_point.x)**2 + 
                                    (current_point.y - first_point.y)**2
                                )
                                if distance_to_first < config.POLYGON_CLOSE_THRESHOLD:
                                    should_close = True
                            
                            if should_close:
                                if len(self.polygon_points) >= 2: # Asegurar que hay al menos un segmento para cerrar
                                    self._draw_bresenham_line(self.polygon_points[-1], self.polygon_points[0], self.draw_color)
                                self.polygon_points = [] # Resetear polígono
                            else:
                                self.polygon_points.append(current_point)
                                if len(self.polygon_points) >= 2:
                                    self._draw_polygon(self.polygon_points) # Dibuja el último segmento añadido

            elif event.type == pygame.MOUSEMOTION:
                if self.is_drawing and self.current_tool == "pixel":
                    if pygame.mouse.get_pressed()[0] and self.canvas.rect.collidepoint(abs_mouse_pos):
                        current_mouse_pos_relative = self.canvas.to_relative_pos(Point(*abs_mouse_pos))
                        if self.last_mouse_pos_for_pixel_draw and self.last_mouse_pos_for_pixel_draw != current_mouse_pos_relative:
                            self._draw_bresenham_line(self.last_mouse_pos_for_pixel_draw, current_mouse_pos_relative, self.draw_color)
                        self.last_mouse_pos_for_pixel_draw = current_mouse_pos_relative
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: 
                    if self.is_drawing:
                        self.is_drawing = False
                        self.last_mouse_pos_for_pixel_draw = None

            elif event.type == pygame.KEYDOWN:
                # Esta sección solo se alcanza si no estamos en is_typing_prompt ni is_veo_processing
                if event.key == pygame.K_ESCAPE: # Escape general para resetear puntos de dibujo
                    self._reset_drawing_states()
                    print("Puntos de dibujo pendientes reseteados por ESC.")
                
                elif event.key == pygame.K_c: # Atajo para Limpiar
                    self.canvas.clear()
                    self._reset_all_states() # Resetea todo, incluyendo Veo si estaba activo
                    print("Lienzo limpiado y todos los estados reseteados por atajo 'C'.")

                elif event.key == pygame.K_g: # Atajo para Gemini
                    if GEMINI_AVAILABLE and self.gemini_client:
                        self.is_typing_prompt = True
                        self.current_prompt_text = ""
                        self.gemini_status_message = config.PROMPT_INPUT_PLACEHOLDER
                        self.current_tool = "gemini_generate" # Seleccionar la herramienta
                        self._reset_drawing_states()
                        print("Modo escritura de prompt para Gemini activado por atajo 'G'.")
                    else:
                        self.gemini_status_message = "Error: IA no disponible/configurada."
                        print(self.gemini_status_message)
                
                elif event.key == pygame.K_v: # NUEVO: Atajo para Veo
                    if not self.is_veo_processing and not self.is_typing_prompt:
                        if self.gemini_client:
                            self.current_tool = "veo_generate" # Seleccionar la herramienta
                            self._start_veo_generation()
                        else:
                            self.gemini_status_message = config.VEO_STATUS_ERROR_API
                    else:
                        self.gemini_status_message = config.VEO_STATUS_PROCESSING_ANOTHER_OP
                    print(self.gemini_status_message)

    def _render(self) -> None:
            """
            Dibuja todos los elementos visibles en la pantalla.

            Limpia la pantalla, dibuja el lienzo (que ahora puede contener la imagen generada por IA),
            el panel de controles, la UI del prompt/estado, y el feedback visual de las herramientas.
            Finalmente, actualiza la pantalla de Pygame.
            """
            # 1. Limpiar la pantalla principal
            self.screen.fill(config.WINDOW_BG_COLOR)

            # 2. Dibujar el lienzo (que ahora puede contener la imagen generada por IA)
            #    La llamada a _call_gemini_api ya habrá actualizado self.canvas.surface si se generó una imagen.
            self.canvas.render(self.screen) 

            # 3. --- BLOQUE ELIMINADO ---
            # Ya no dibujamos self.generated_image_surface aquí, porque ahora es parte del canvas.
            # if self.generated_image_surface:
                # ... (código anterior para escalar y blitear self.generated_image_surface) ...
            # --- FIN BLOQUE ELIMINADO ---

            # 4. Dibujar el panel de controles
            self.controls.render(self.screen, self.current_tool, self.draw_color)

            # 5. Renderizar UI para prompt de Gemini y mensajes de estado (parte inferior)
            #    (Esta lógica no necesita cambios)
            status_area_rect = pygame.Rect(0, config.SCREEN_HEIGHT - 40, config.SCREEN_WIDTH, 40)
            if self.is_typing_prompt:
                cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
                prompt_text_render = f"{config.PROMPT_ACTIVE_PREFIX}{self.current_prompt_text}{cursor}"
                prompt_surf = self.ui_font_normal.render(prompt_text_render, True, config.PROMPT_INPUT_TEXT_COLOR, config.PROMPT_INPUT_BG_COLOR)
                prompt_rect = prompt_surf.get_rect(centerx=self.screen.get_rect().centerx, bottom=config.SCREEN_HEIGHT - 10)
                prompt_rect.left = max(10, prompt_rect.left) # Evitar que se salga por la izquierda
                prompt_rect.right = min(config.SCREEN_WIDTH - 10, prompt_rect.right) # Evitar que se salga por la derecha
                # Dibujar fondo para el prompt
                bg_rect = prompt_rect.inflate(10, 6)
                bg_rect.width = min(bg_rect.width, config.SCREEN_WIDTH - 20) # Limitar ancho del fondo
                bg_rect.centerx = self.screen.get_rect().centerx
                pygame.draw.rect(self.screen, config.PROMPT_INPUT_BG_COLOR, bg_rect, border_radius=3)
                pygame.draw.rect(self.screen, config.DARK_GRAY, bg_rect, 1, border_radius=3)
                self.screen.blit(prompt_surf, prompt_rect) # Dibujar texto encima
            elif self.gemini_status_message:
                # Dibujar mensaje de estado si no estamos escribiendo prompt
                status_surf = self.ui_font_normal.render(self.gemini_status_message, True, config.STATUS_MESSAGE_COLOR)
                status_rect = status_surf.get_rect(centerx=self.screen.get_rect().centerx, bottom=config.SCREEN_HEIGHT - 10)
                status_rect.left = max(10, status_rect.left)
                status_rect.right = min(config.SCREEN_WIDTH - 10, status_rect.right)
                # Dibujar fondo opcional para el estado
                bg_rect_status = status_rect.inflate(10, 6)
                bg_rect_status.width = min(bg_rect_status.width, config.SCREEN_WIDTH - 20)
                bg_rect_status.centerx = self.screen.get_rect().centerx
                pygame.draw.rect(self.screen, config.LIGHT_GRAY, bg_rect_status, border_radius=3) # Fondo gris claro
                self.screen.blit(status_surf, status_rect)

            # 6. Dibujar feedback visual para herramientas multi-punto (Previsualizaciones)
            #    (Esta lógica no necesita cambios)
            mouse_pos_abs = pygame.mouse.get_pos()
            mouse_on_canvas = self.canvas.rect.collidepoint(mouse_pos_abs)

            if not self.is_typing_prompt: # Solo mostrar previsualizaciones si no estamos dibujando
                # Previsualización Bézier
                for i, p in enumerate(self.bezier_points):
                    p_abs = self.canvas.to_absolute_pos(p)
                    pygame.draw.circle(self.screen, config.RED, p_abs, 4)
                    if i > 0:
                        prev_p_abs = self.canvas.to_absolute_pos(self.bezier_points[i-1])
                        pygame.draw.line(self.screen, config.LIGHT_GRAY, prev_p_abs, p_abs, 1)
                if self.bezier_points and mouse_on_canvas:
                    last_p_abs = self.canvas.to_absolute_pos(self.bezier_points[-1])
                    pygame.draw.line(self.screen, config.LIGHT_GRAY, last_p_abs, mouse_pos_abs, 1)

                # Previsualización Triángulo
                for i, p in enumerate(self.triangle_points):
                    p_abs = self.canvas.to_absolute_pos(p)
                    pygame.draw.circle(self.screen, config.GREEN, p_abs, 4)
                    if i > 0:
                        prev_p_abs = self.canvas.to_absolute_pos(self.triangle_points[i-1])
                        pygame.draw.line(self.screen, config.LIGHT_GRAY, prev_p_abs, p_abs, 1)
                if self.triangle_points and mouse_on_canvas:
                    last_p_abs = self.canvas.to_absolute_pos(self.triangle_points[-1])
                    pygame.draw.line(self.screen, config.LIGHT_GRAY, last_p_abs, mouse_pos_abs, 1)
                    if len(self.triangle_points) == 2:
                        first_p_abs = self.canvas.to_absolute_pos(self.triangle_points[0])
                        pygame.draw.line(self.screen, config.LIGHT_GRAY, mouse_pos_abs, first_p_abs, 1)

                # Previsualización Rectángulo
                for p in self.rectangle_points:
                    pygame.draw.circle(self.screen, config.BLUE, self.canvas.to_absolute_pos(p), 4)
                if len(self.rectangle_points) == 1 and mouse_on_canvas:
                    p_start_abs = self.canvas.to_absolute_pos(self.rectangle_points[0])
                    x0, y0 = p_start_abs
                    x1, y1 = mouse_pos_abs
                    preview_rect = pygame.Rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
                    pygame.draw.rect(self.screen, config.LIGHT_GRAY, preview_rect, 1)

                # Previsualización Polígono
                for i, p in enumerate(self.polygon_points):
                    p_abs = self.canvas.to_absolute_pos(p)
                    pygame.draw.circle(self.screen, config.DARK_GRAY, p_abs, 4)
                if self.polygon_points and mouse_on_canvas:
                    last_p_abs = self.canvas.to_absolute_pos(self.polygon_points[-1])
                    pygame.draw.line(self.screen, config.LIGHT_GRAY, last_p_abs, mouse_pos_abs, 1)
                    if len(self.polygon_points) >= 2:
                        first_p_abs = self.canvas.to_absolute_pos(self.polygon_points[0])
                        dx = mouse_pos_abs[0] - first_p_abs[0]
                        dy = mouse_pos_abs[1] - first_p_abs[1]
                        dist_sq = dx*dx + dy*dy 
                        close_color = config.YELLOW if dist_sq < config.POLYGON_CLOSE_THRESHOLD**2 else config.LIGHT_GRAY
                        pygame.draw.line(self.screen, close_color, mouse_pos_abs, first_p_abs, 1)

                # Previsualización Elipse
                if len(self.ellipse_points) == 1:
                    center_abs = self.canvas.to_absolute_pos(self.ellipse_points[0])
                    pygame.draw.circle(self.screen, config.MAGENTA, center_abs, 4)
                    if mouse_on_canvas:
                        rx = abs(mouse_pos_abs[0] - center_abs[0])
                        ry = abs(mouse_pos_abs[1] - center_abs[1])
                        if rx > 0 and ry > 0:
                            preview_rect = pygame.Rect(center_abs[0] - rx, center_abs[1] - ry, 2*rx, 2*ry)
                            pygame.draw.ellipse(self.screen, config.LIGHT_GRAY, preview_rect, 1)

                # Previsualización Línea
                if self.line_start_point:
                    start_p_abs = self.canvas.to_absolute_pos(self.line_start_point)
                    pygame.draw.circle(self.screen, config.ORANGE, start_p_abs, 4)
                    if mouse_on_canvas:
                        pygame.draw.line(self.screen, config.LIGHT_GRAY, start_p_abs, mouse_pos_abs, 1)

                # Previsualización Círculo
                if self.circle_center:
                    center_abs = self.canvas.to_absolute_pos(self.circle_center)
                    pygame.draw.circle(self.screen, config.CYAN, center_abs, 4)
                    if mouse_on_canvas:
                        dx = mouse_pos_abs[0] - center_abs[0]
                        dy = mouse_pos_abs[1] - center_abs[1]
                        radius = int(math.sqrt(dx*dx + dy*dy))
                        if radius > 0:
                            pygame.draw.circle(self.screen, config.LIGHT_GRAY, center_abs, radius, 1)

            # 7. Actualizar la pantalla completa
            pygame.display.flip()

    def _update(self, dt: float) -> None:
        """
        Actualiza el estado de la aplicación en cada frame.

        Actualmente, esta función no realiza ninguna acción específica, pero
        está presente para futuras expansiones (ej: animaciones, lógica de juego).

        Args:
            dt (float): Delta time, tiempo transcurrido desde el último frame en segundos.
        """
        pass

    def run(self) -> None:
        """
        Inicia y ejecuta el bucle principal de la aplicación.

        El bucle continúa mientras `self.is_running` sea True. En cada iteración,
        controla el framerate, maneja eventos, actualiza el estado y renderiza
        la pantalla.
        """
        while self.is_running:
            # Delta time en segundos
            dt: float = self.clock.tick(config.FPS) / 1000.0

            self._handle_events()
            self._update(dt)
            self._render()

        print("Saliendo de la aplicación...")
        
    
    def _call_gemini_api(self, image_input: PILImage.Image, prompt_text: str) -> None:
        """
        Llama a la API de Gemini con la imagen del lienzo y el prompt del usuario.
        Procesa la respuesta para obtener la imagen generada y/o texto.
        Si se recibe una imagen, reemplaza el contenido del canvas con ella.
        Actualiza self.gemini_status_message.
        """
        if not self.gemini_client: # Usar self.gemini_client
            self.gemini_status_message = "Error: Cliente de Gemini no inicializado."
            print(self.gemini_status_message)
            return
        
        # Verificar si Pillow está disponible (PILImage se establece en None si falla el import)
        if not PILImage:
             self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
             print(f"Error: {self.gemini_status_message}")
             return

        self.gemini_status_message = config.GEMINI_STATUS_LOADING # "IA pensando..."
        print(f"Llamando a Gemini API con prompt original: '{prompt_text}' y una imagen de entrada.")
        self._render() # Forzar redibujado para mostrar mensaje de "pensando"
        pygame.time.wait(10) # Pequeña pausa para que se vea

        try:
            # --- MODIFICACIÓN AQUÍ ---
            # Añadir la instrucción de estilo al prompt del usuario.
            enhanced_prompt_text = f"{prompt_text}. Keep the same minimal line doodle style."
            print(f"Prompt mejorado enviado a Gemini: '{enhanced_prompt_text}'")
            # --- FIN DE LA MODIFICACIÓN ---

            # Construir el contenido para la API usando el prompt mejorado
            contents = [ 
                enhanced_prompt_text, # Usar el prompt mejorado
                image_input 
            ]

            # Configuración para solicitar imagen y texto en la respuesta
            generation_config_dict = {
                "response_modalities": ['TEXT', 'IMAGE'], 
                "candidate_count": 1 
            }
            print(f"Usando generation_config: {generation_config_dict}")

            generation_config = types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                candidate_count=1
            )
            print(f"Usando generation_config: {generation_config}")

            # Llamada a la API a través del cliente
            response = self.gemini_client.models.generate_content(
                model=config.GEMINI_MODEL_NAME, # El nombre del modelo se pasa aquí
                contents=contents,
                config=generation_config,      # El parámetro ahora se llama 'config'
)

            # Procesar la respuesta
            # self.generated_image_surface = None # Ya no almacenamos aquí, reemplazamos canvas
            generated_text_response = ""
            image_processed_and_applied = False # Flag para saber si se actualizó el canvas

            # print(f"Respuesta cruda de Gemini: {response}") # Descomentar para depuración

            if response.candidates:
                # Iterar sobre las partes de la respuesta del primer candidato
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        generated_text_response += part.text + "\n" # Acumular texto
                    
                    # Procesar si es una imagen
                    elif hasattr(part, 'inline_data') and part.inline_data and part.inline_data.mime_type.startswith('image/'):
                        try:
                            print(f"Recibida parte de imagen con mime_type: {part.inline_data.mime_type}")
                            image_data_bytes = part.inline_data.data
                            
                            # Convertir bytes a PIL Image
                            generated_pil_image = PILImage.open(io.BytesIO(image_data_bytes))
                            
                            # Convertir PIL Image a Pygame Surface temporalmente
                            temp_pygame_surface = None
                            mode = generated_pil_image.mode
                            size = generated_pil_image.size
                            data_str = generated_pil_image.tobytes()
                            
                            if mode in ('RGB', 'RGBA'):
                                temp_pygame_surface = pygame.image.fromstring(data_str, size, mode)
                            else: 
                                print(f"Modo de imagen no directamente soportado: {mode}. Intentando convertir a RGBA.")
                                try:
                                     generated_pil_image_converted = generated_pil_image.convert('RGBA')
                                     mode = generated_pil_image_converted.mode
                                     size = generated_pil_image_converted.size
                                     data_str = generated_pil_image_converted.tobytes()
                                     temp_pygame_surface = pygame.image.fromstring(data_str, size, mode)
                                except Exception as convert_err:
                                     print(f"Error al convertir imagen PIL a RGBA: {convert_err}")

                            # --- Reemplazar contenido del canvas ---
                            if temp_pygame_surface:
                                print("Reemplazando contenido del lienzo con la imagen generada.")
                                canvas_w, canvas_h = self.canvas.rect.size
                                
                                # Reescalar la imagen generada para que llene exactamente el canvas
                                try:
                                    scaled_generated_surface = pygame.transform.smoothscale(temp_pygame_surface, (canvas_w, canvas_h))
                                except ValueError:
                                    print("Advertencia: No se pudo escalar suavemente, usando scale normal.")
                                    scaled_generated_surface = pygame.transform.scale(temp_pygame_surface, (canvas_w, canvas_h))

                                # Limpiar el canvas actual (fondo blanco por defecto)
                                self.canvas.clear() 
                                # Dibujar la nueva imagen (reescalada) sobre la superficie del canvas
                                self.canvas.surface.blit(scaled_generated_surface, (0, 0)) 

                                print("Lienzo actualizado con la imagen generada.")
                                image_processed_and_applied = True 
                                # break # Descomentar si solo quieres procesar la primera imagen encontrada
                            # --- Fin Reemplazar contenido del canvas ---
                        
                        except Exception as img_proc_err:
                            # Error procesando la imagen, pero puede haber texto
                            self.gemini_status_message = f"Error procesando imagen de Gemini: {str(img_proc_err)[:100]}"
                            print(f"Error: {self.gemini_status_message}")
            
            # --- Determinar el mensaje final ---
            if image_processed_and_applied:
                self.gemini_status_message = "¡Lienzo actualizado con IA!"
                if generated_text_response:
                     self.gemini_status_message += " (y texto recibido)"
                     print(f"Texto adicional de Gemini:\n{generated_text_response.strip()}")
            elif generated_text_response:
                 self.gemini_status_message = f"IA respondió con texto: {generated_text_response.strip()[:100]}..."
                 print(f"Respuesta solo de texto de Gemini:\n{generated_text_response.strip()}")
            else:
                # Revisar si fue bloqueado o respuesta vacía
                block_reason = ""
                block_message = ""
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                     block_reason = f" Razón: {response.prompt_feedback.block_reason}"
                     block_message = f" Msj: {response.prompt_feedback.block_reason_message}" if response.prompt_feedback.block_reason_message else ""
                     self.gemini_status_message = f"Error: Respuesta de IA bloqueada.{block_reason}{block_message}"
                else:
                     self.gemini_status_message = "Error: Respuesta de IA vacía o inesperada."
                print(self.gemini_status_message)


        except Exception as e:
            self.gemini_status_message = f"Error en llamada a IA: {type(e).__name__}"
            print(f"Error crítico durante la llamada a Gemini API: {self.gemini_status_message}")
            traceback.print_exc() # Imprimir traceback para depuración
            
   # En src/graficador/app.py, dentro de la clase Application

    def _start_veo_generation(self) -> None:
        """
        Inicia la generación de video con Veo, utilizando SIEMPRE la imagen actual del lienzo
        y un PROMPT FIJO para animarla manteniendo el estilo.
        """
        print("Veo - Iniciando _start_veo_generation (con imagen del lienzo y prompt fijo)...")

        if not self.gemini_client:
            self.gemini_status_message = config.VEO_STATUS_ERROR_API
            print("Veo - Error: Cliente de Gemini (necesario para Veo) no inicializado.")
            return

        # Prevenir operaciones simultáneas
        if self.is_veo_processing:
            self.gemini_status_message = config.VEO_STATUS_PROCESSING_ANOTHER_OP
            print(f"Veo - {self.gemini_status_message} (Veo ya está procesando).")
            return
        if self.is_typing_prompt: # No iniciar Veo si se está escribiendo para Gemini
            self.gemini_status_message = config.VEO_STATUS_PROCESSING_ANOTHER_OP
            print(f"Veo - {self.gemini_status_message} (Modo de escritura de prompt para Gemini activo).")
            return

        # Capturar la imagen del lienzo. Esencial para Veo con esta nueva lógica.
        pil_image: Optional[PILImage.Image] = self._capture_canvas_as_pil_image()

        if not pil_image:
            self.gemini_status_message = "Veo - Error: No hay imagen en el lienzo para animar."
            print(self.gemini_status_message)
            return # Salir si no hay imagen

        print(f"Veo - Propiedades de la imagen PIL capturada (original): Modo={pil_image.mode}, Tamaño={pil_image.size}")
        try:
            debug_image_filename_png = "debug_veo_input_original.png"
            pil_image.save(debug_image_filename_png)
            print(f"Veo - Imagen original (PNG) para Veo guardada como: {debug_image_filename_png}")
        except Exception as e_save_png:
            print(f"Veo - Error al guardar imagen de depuración original (PNG): {e_save_png}")

        # Definir el prompt fijo para Veo
        prompt_fijo_para_veo = "animate keep the style Keep the same minimal line doodle style."
        print(f"Veo - Usando prompt fijo para Veo: '{prompt_fijo_para_veo}'")

        self.is_veo_processing = True
        self.gemini_status_message = config.VEO_STATUS_STARTING
        print(f"Veo - Estado actualizado a: {self.gemini_status_message}")
        self._render() 
        pygame.time.wait(10)

        try:
            veo_config = types.GenerateVideosConfig(
                aspect_ratio=config.VEO_DEFAULT_ASPECT_RATIO,
                duration_seconds=config.VEO_DEFAULT_DURATION_SECONDS,
                person_generation=config.VEO_DEFAULT_PERSON_GENERATION,
                number_of_videos=1
            )
            print(f"Veo - Configuración para generate_videos: {veo_config}")

            image_input_for_api = None
            # Procesar la imagen capturada para enviarla (siguiendo el patrón del Colab de Veo)
            print("Veo - Procesando imagen capturada para enviarla como types.Image (PNG)...")
            try:
                image_bytes_io = io.BytesIO()
                pil_image.save(image_bytes_io, format="PNG") 
                image_bytes = image_bytes_io.getvalue()
                current_mime_type = "image/png"
                print(f"Veo - Bytes PNG generados, tamaño: {len(image_bytes)} bytes.")
                
                # Construir como types.Image (basado en el ejemplo del Colab de Veo)
                image_input_for_api = types.Image(image_bytes=image_bytes, mime_type=current_mime_type)
                print(f"Veo - Imagen convertida exitosamente a types.Image (mime_type: {current_mime_type}).")

            except Exception as e_convert:
                print(f"Veo - CRÍTICO: Error al construir types.Image: {e_convert}")
                traceback.print_exc()
                self.gemini_status_message = f"Error preparando imagen para Veo: {str(e_convert)[:100]}"
                self.is_veo_processing = False
                return
            
            print(f"Veo - Iniciando llamada a generate_videos con prompt: '{prompt_fijo_para_veo}' y con imagen (types.Image).")
            
            operation = self.gemini_client.models.generate_videos(
                model=config.VEO_MODEL_NAME,
                prompt=prompt_fijo_para_veo,    # Usar siempre el prompt fijo
                image=image_input_for_api,  # Enviar la imagen procesada
                config=veo_config,
            )
            
            self.current_veo_operation_object = operation 
            if self.current_veo_operation_object and hasattr(self.current_veo_operation_object, 'name'):
                self.veo_operation_name_for_log = self.current_veo_operation_object.name 
                self.gemini_status_message = config.VEO_STATUS_GENERATING
                print(f"Veo - Operación de Veo iniciada. Nombre: {self.veo_operation_name_for_log}. Estado: {self.gemini_status_message}")
                pygame.time.set_timer(self.VEO_POLLING_EVENT, config.VEO_INITIAL_POLL_DELAY_MS, loops=1)
                print(f"Veo - Polling programado en {config.VEO_INITIAL_POLL_DELAY_MS / 1000} segundos.")
            else:
                self.gemini_status_message = "Error: generate_videos no devolvió un objeto de operación válido."
                print(f"Veo - {self.gemini_status_message}")
                self.is_veo_processing = False
                self.current_veo_operation_object = None

        except Exception as e: 
            self.gemini_status_message = f"Error crítico al iniciar Veo: {type(e).__name__}"
            print(f"Veo - {self.gemini_status_message}: {e}")
            traceback.print_exc()
            self.is_veo_processing = False 
            self.current_veo_operation_object = None
            
    def _poll_veo_status(self) -> None:
        """Consulta el estado de una operación de Veo en curso."""
        
        if not self.current_veo_operation_object or not self.is_veo_processing or not self.gemini_client:
            print("Veo - Poll: No hay operación de Veo activa o cliente no disponible. Deteniendo polling.")
            pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
            self.is_veo_processing = False
            self.current_veo_operation_object = None
            return

        current_op_name_for_log = getattr(self.current_veo_operation_object, 'name', 'ID_DESCONOCIDO')
        
        print(f"Veo - Poll: Consultando estado de la operación: {current_op_name_for_log}")
        self.gemini_status_message = config.VEO_STATUS_POLLING
        self._render()

        try:
            self.current_veo_operation_object = self.gemini_client.operations.get(self.current_veo_operation_object)
            print(f"Veo - Poll: Respuesta de operations.get() recibida para {current_op_name_for_log}.")

            if self.current_veo_operation_object.done:
                print(f"Veo - Poll: Operación {current_op_name_for_log} marcada como 'done'.")
                pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
                self.is_veo_processing = False
                
                operation_final_result = self.current_veo_operation_object
                self.current_veo_operation_object = None

                if hasattr(operation_final_result, 'error') and operation_final_result.error:
                    error_code = getattr(operation_final_result.error, 'code', 'N/A')
                    error_message = getattr(operation_final_result.error, 'message', 'Error desconocido en Veo.')
                    self.gemini_status_message = f"Error en Veo (Code: {error_code}): {error_message}"
                    print(f"Veo - Poll: {self.gemini_status_message}")
                
                elif operation_final_result.response and hasattr(operation_final_result.response, 'generated_videos'):
                    videos_generados = operation_final_result.response.generated_videos
                    if videos_generados:
                        print(f"Veo - Poll: Se generaron {len(videos_generados)} video(s).")
                        saved_count = 0
                        for i, gen_video_metadata in enumerate(videos_generados):
                            video_metadata_name = getattr(gen_video_metadata.video, 'name', f'video_sin_nombre_{i}')
                            try:
                                timestamp = pygame.time.get_ticks()
                                video_filename = f"veo_video_{timestamp}_{i}.mp4"
                                print(f"Veo - Poll: Procesando video {i+1} (ID desde API: {video_metadata_name})...")

                                print(f"Veo - Poll: Llamando a client.files.download para {video_metadata_name}...")
                                # self.gemini_client.files.download() devuelve los bytes del video directamente.
                                video_bytes = self.gemini_client.files.download(file=gen_video_metadata.video) 

                                if video_bytes and isinstance(video_bytes, bytes):
                                    print(f"Veo - Poll: Descarga completada para {video_metadata_name}. Recibidos {len(video_bytes)} bytes.")
                                    print(f"Veo - Poll: Intentando guardar {video_filename}...")
                                    with open(video_filename, "wb") as f:
                                        f.write(video_bytes)
                                    print(f"Veo - Poll: Video {video_filename} guardado exitosamente.")
                                    saved_count += 1
                                else:
                                    print(f"Veo - Poll: La descarga para {video_metadata_name} no devolvió bytes válidos. Tipo recibido: {type(video_bytes)}")

                            except Exception as save_err:
                                print(f"Veo - Poll: Error al descargar/guardar video {i+1} ({video_filename}): {type(save_err).__name__} - {save_err}")
                                traceback.print_exc()
                        
                        if saved_count > 0:
                            self.gemini_status_message = config.VEO_STATUS_SUCCESS
                        else:
                            self.gemini_status_message = "Veo terminó, pero no se pudieron guardar videos."
                        print(f"Veo - Poll: Estado final de guardado: {self.gemini_status_message}")
                    else:
                        self.gemini_status_message = "Veo terminó, pero no se generaron videos en la respuesta."
                        print(f"Veo - Poll: {self.gemini_status_message}")
                else:
                    self.gemini_status_message = "Veo completó la operación de forma inesperada (sin error ni videos válidos)."
                    print(f"Veo - Poll: {self.gemini_status_message}")
            else:
                pygame.time.set_timer(self.VEO_POLLING_EVENT, config.VEO_POLLING_INTERVAL_MS, loops=1)
                print(f"Veo - Poll: Operación {current_op_name_for_log} sigue procesando. Nueva consulta en {config.VEO_POLLING_INTERVAL_MS / 1000}s.")
                self.gemini_status_message = config.VEO_STATUS_GENERATING

        except Exception as e:
            self.gemini_status_message = f"Error crítico al consultar estado de Veo: {type(e).__name__}"
            current_op_name_for_log_exc = getattr(self.current_veo_operation_object, 'name', 'ID_DESCONOCIDO_EN_EXCEPCION')
            print(f"Veo - Poll: {self.gemini_status_message} para {current_op_name_for_log_exc}: {e}")
            traceback.print_exc()
            pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
            self.is_veo_processing = False
            self.current_veo_operation_object = None   