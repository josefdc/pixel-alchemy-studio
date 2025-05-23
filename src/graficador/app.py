"""
src/graficador/app.py
Módulo principal de la aplicación Graficador Geométrico Interactivo.

Este módulo contiene la clase `Application` que gestiona el ciclo de vida
de la aplicación Pygame, maneja los eventos de usuario, coordina el dibujo
en el lienzo (`Canvas`) y la interacción con los controles (`Controls`).
Integra los algoritmos de dibujo geométrico y las estructuras de datos
necesarias para la creación interactiva de figuras.
"""
import pygame
# import sys # Unused import
import math
import os # Nuevo import para manejo de variables de entorno
from typing import List, Optional, Tuple, cast # Added Tuple and cast
import io  # Import for handling in-memory image buffers
import traceback

from . import config
from .ui.canvas import Canvas
from .ui.controls import Controls
from .geometry.point import Point
from .algorithms.dda import dda_line
from .algorithms.bresenham import bresenham_line, bresenham_circle
from .algorithms.bezier import cubic_bezier
from .algorithms.shapes import midpoint_ellipse

# --- Importaciones para Gemini (con manejo de errores) ---
try:
    import google.generativeai as genai  # CORRECCIÓN AQUÍ
    from google.generativeai import types as genai_types  # Necesario para GenerateContentConfig
    from PIL import Image as PILImage  # Necesario para manejar los datos de imagen
    GEMINI_AVAILABLE = True
except ImportError:
    # Establecer placeholders si las librerías no están
    genai = None
    genai_types = None
    PILImage = None
    GEMINI_AVAILABLE = False
    # El mensaje de advertencia ya lo tienes en __init__ a través de _initialize_gemini

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
        self.gemini_model_instance = None  # Para la instancia del GenerativeModel
        self.is_typing_prompt: bool = False
        self.current_prompt_text: str = ""
        self.generated_image_surface: Optional[pygame.Surface] = None
        self.gemini_status_message: str = config.GEMINI_STATUS_DEFAULT

        self._initialize_gemini()

        print(f"Aplicación inicializada. Herramienta actual: {self.current_tool}")
        if GEMINI_AVAILABLE and self.gemini_model_instance:
            print(f"Modelo Gemini listo para usar: {config.GEMINI_MODEL_NAME}")
        else:
            print(f"Estado de Gemini al finalizar __init__: {self.gemini_status_message}")


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

    def _initialize_gemini(self) -> None:
        """Inicializa el cliente de Gemini si las librerías y la API key están disponibles."""
        if not GEMINI_AVAILABLE:
            self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            return

        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                self.gemini_status_message = config.GEMINI_STATUS_ERROR_API_KEY
                print(f"ADVERTENCIA: {self.gemini_status_message}")
                return

            # Configurar la API Key globalmente para el módulo genai
            genai.configure(api_key=api_key)
            
            # Instanciar el modelo específico que queremos usar
            self.gemini_model_instance = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
            
            self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
            print(f"Configuración de Gemini y modelo '{config.GEMINI_MODEL_NAME}' listos.")

        except Exception as e:
            self.gemini_status_message = f"Error inicializando Gemini: {str(e)[:150]}"
            print(f"ERROR GENERAL: {self.gemini_status_message}")
            self.gemini_model_instance = None

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

    def _initialize_gemini(self) -> None:
        """Inicializa el cliente de Gemini si las librerías y la API key están disponibles."""
        if not GEMINI_AVAILABLE:
            self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            return

        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                self.gemini_status_message = config.GEMINI_STATUS_ERROR_API_KEY
                print(f"ADVERTENCIA: {self.gemini_status_message}")
                return

            # Configurar la API Key globalmente para el módulo genai
            genai.configure(api_key=api_key)
            
            # Instanciar el modelo específico que queremos usar
            self.gemini_model_instance = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
            
            self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
            print(f"Configuración de Gemini y modelo '{config.GEMINI_MODEL_NAME}' listos.")

        except Exception as e:
            self.gemini_status_message = f"Error inicializando Gemini: {str(e)[:150]}"
            print(f"ERROR GENERAL: {self.gemini_status_message}")
            self.gemini_model_instance = None

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

    def _initialize_gemini(self) -> None:
        """Inicializa el cliente de Gemini si las librerías y la API key están disponibles."""
        if not GEMINI_AVAILABLE:
            self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            return

        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                self.gemini_status_message = config.GEMINI_STATUS_ERROR_API_KEY
                print(f"ADVERTENCIA: {self.gemini_status_message}")
                return

            # Configurar la API Key globalmente para el módulo genai
            genai.configure(api_key=api_key)
            
            # Instanciar el modelo específico que queremos usar
            self.gemini_model_instance = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
            
            self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
            print(f"Configuración de Gemini y modelo '{config.GEMINI_MODEL_NAME}' listos.")

        except Exception as e:
            self.gemini_status_message = f"Error inicializando Gemini: {str(e)[:150]}"
            print(f"ERROR GENERAL: {self.gemini_status_message}")
            self.gemini_model_instance = None

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
            Maneja los eventos de entrada del usuario (teclado, ratón).
            """
            mouse_pos_on_controls: Optional[Tuple[int, int]] = None
            abs_mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()
            if self.controls.rect.collidepoint(abs_mouse_pos):
                mouse_pos_on_controls = (abs_mouse_pos[0] - self.controls.rect.x,
                                        abs_mouse_pos[1] - self.controls.rect.y)

            self.controls.update(mouse_pos_on_controls)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False

                if self.is_typing_prompt and event.type == pygame.KEYDOWN:
                    # ... (lógica del prompt de IA sin cambios) ...
                    if event.key == pygame.K_RETURN:
                        self.is_typing_prompt = False
                        prompt_final = self.current_prompt_text.strip()
                        if not prompt_final:
                            self.gemini_status_message = "Prompt vacío. Intenta de nuevo."
                            print("Intento de generación con prompt vacío.")
                        elif not self.gemini_model_instance:
                            self.gemini_status_message = "Error: IA no inicializada."
                            print("Intento de generación sin modelo de IA.")
                        else:
                            print(f"Prompt finalizado: '{prompt_final}'. Iniciando generación...")
                            self.gemini_status_message = config.GEMINI_STATUS_LOADING
                            self.generated_image_surface = None 
                            pil_image = self._capture_canvas_as_pil_image()
                            if pil_image:
                                self._call_gemini_api(pil_image, prompt_final) 
                            else:
                                pass
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_prompt_text = self.current_prompt_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        print("Entrada de prompt cancelada.")
                        self._reset_all_states()
                    else:
                        if len(self.current_prompt_text) < 200:
                            self.current_prompt_text += event.unicode
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: 
                        if self.canvas.rect.collidepoint(abs_mouse_pos):
                            if not self.is_typing_prompt:
                                relative_x = abs_mouse_pos[0] - self.canvas.rect.x
                                relative_y = abs_mouse_pos[1] - self.canvas.rect.y
                                current_point = Point(relative_x, relative_y)
                                
                                if self.current_tool == "pixel":
                                    self.is_drawing = True
                                    # Dibuja el primer punto
                                    self.canvas.draw_pixel(current_point.x, current_point.y, self.draw_color)
                                    # --- MODIFICADO: Guarda la posición inicial ---
                                    self.last_mouse_pos_for_pixel_draw = current_point
                                    # --- FIN DE LA MODIFICACIÓN ---
                                
                                # (El resto de las herramientas de dibujo no cambian en MOUSEBUTTONDOWN)
                                elif self.current_tool in ["dda_line", "bresenham_line"]:
                                    if not self.line_start_point:
                                        self.line_start_point = current_point
                                    else:
                                        if self.current_tool == "dda_line":
                                            self._draw_dda_line(self.line_start_point, current_point, self.draw_color)
                                        else:
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
                                    if len(self.ellipse_points) == 0:
                                        self.ellipse_points.append(current_point)
                                    elif len(self.ellipse_points) == 1:
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
                                    if len(self.rectangle_points) == 2:
                                        self._draw_rectangle(self.rectangle_points[0], self.rectangle_points[1])
                                        self.rectangle_points = []
                                elif self.current_tool == "polygon":
                                    should_close = False
                                    if len(self.polygon_points) >= 2:
                                        first_point = self.polygon_points[0]
                                        distance = math.sqrt(
                                            (current_point.x - first_point.x)**2 + 
                                            (current_point.y - first_point.y)**2
                                        )
                                        if distance < config.POLYGON_CLOSE_THRESHOLD:
                                            should_close = True
                                    if should_close:
                                        if len(self.polygon_points) >= 2:
                                            self._draw_bresenham_line(self.polygon_points[-1], self.polygon_points[0], self.draw_color)
                                            self.polygon_points = []
                                        else: # No debería llegar aquí si should_close es True por la comprobación de len >=2
                                            self.polygon_points.append(current_point)
                                            if len(self.polygon_points) >=2: self._draw_polygon(self.polygon_points)
                                    else:
                                        self.polygon_points.append(current_point)
                                        if len(self.polygon_points) >=2: self._draw_polygon(self.polygon_points)
                            else:
                                print("Clic en lienzo ignorado (Modo Prompt IA activo)")

                        elif mouse_pos_on_controls:
                            # ... (lógica del panel de control sin cambios)
                            click_result = self.controls.handle_click(mouse_pos_on_controls)
                            if click_result:
                                click_type, value = click_result
                                if click_type == "tool":
                                    tool_id = cast(str, value)
                                    if tool_id == "gemini_generate":
                                        if GEMINI_AVAILABLE and self.gemini_model_instance:
                                            if not self.is_typing_prompt:
                                                self.is_typing_prompt = True
                                                self.current_prompt_text = ""
                                                self.generated_image_surface = None
                                                self.gemini_status_message = config.PROMPT_INPUT_PLACEHOLDER
                                                self.current_tool = "gemini_generate"
                                                self._reset_drawing_states()
                                                print("Modo escritura de prompt activado.")
                                        else:
                                            self.gemini_status_message = "Error: IA no disponible/configurada."
                                    elif tool_id == "clear":
                                        self.canvas.clear()
                                        self.generated_image_surface = None
                                        self._reset_all_states()
                                    elif self.current_tool != tool_id:
                                        if self.is_typing_prompt:
                                            self._reset_all_states()
                                        self.current_tool = tool_id
                                        self._reset_drawing_states()
                                    else:
                                        self._reset_drawing_states()
                                elif click_type == "color":
                                    color_value = cast(pygame.Color, value)
                                    if self.draw_color != color_value:
                                        self.draw_color = color_value
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.is_drawing and self.current_tool == "pixel":
                        if pygame.mouse.get_pressed()[0] and self.canvas.rect.collidepoint(abs_mouse_pos):
                            relative_x = abs_mouse_pos[0] - self.canvas.rect.x
                            relative_y = abs_mouse_pos[1] - self.canvas.rect.y
                            current_mouse_pos_relative = Point(relative_x, relative_y)

                            # --- MODIFICADO: Dibuja una línea desde la última posición ---
                            if self.last_mouse_pos_for_pixel_draw and self.last_mouse_pos_for_pixel_draw != current_mouse_pos_relative:
                                # Usamos Bresenham para dibujar la línea entre los puntos
                                self._draw_bresenham_line(self.last_mouse_pos_for_pixel_draw, current_mouse_pos_relative, self.draw_color)
                            
                            # Actualiza la última posición del ratón
                            self.last_mouse_pos_for_pixel_draw = current_mouse_pos_relative
                            # --- FIN DE LA MODIFICACIÓN ---
                            
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1: 
                        if self.is_drawing:
                            self.is_drawing = False
                            # --- MODIFICADO: Resetea la última posición ---
                            self.last_mouse_pos_for_pixel_draw = None
                            # --- FIN DE LA MODIFICACIÓN ---

                elif event.type == pygame.KEYDOWN:
                    # ... (Lógica de atajos de teclado sin cambios)
                    if not self.is_typing_prompt:
                        if event.key == pygame.K_ESCAPE:
                            self._reset_drawing_states()
                        elif event.key == pygame.K_c:
                            self.canvas.clear()
                            self.generated_image_surface = None
                            self._reset_all_states()
                        elif event.key == pygame.K_g:
                            if GEMINI_AVAILABLE and self.gemini_model_instance:
                                if not self.is_typing_prompt:
                                    self.is_typing_prompt = True
                                    self.current_prompt_text = ""
                                    self.generated_image_surface = None
                                    self.gemini_status_message = config.PROMPT_INPUT_PLACEHOLDER
                                    self.current_tool = "gemini_generate"
                                    self._reset_drawing_states()
                            else:
                                self.gemini_status_message = "Error: IA no disponible/configurada."

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
        if not self.gemini_model_instance:
            self.gemini_status_message = "Error: Modelo Gemini no inicializado."
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

            # Llamada a la API
            response = self.gemini_model_instance.generate_content(
                contents=contents,
                generation_config=generation_config_dict,
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