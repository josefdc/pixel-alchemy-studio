"""
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
from typing import List, Optional, Tuple, cast # Added Tuple and cast

from . import config
from .ui.canvas import Canvas
from .ui.controls import Controls
from .geometry.point import Point
from .algorithms.dda import dda_line
from .algorithms.bresenham import bresenham_line, bresenham_circle
from .algorithms.bezier import cubic_bezier
from .algorithms.shapes import midpoint_ellipse


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

        # Crear el panel de controles
        self.controls: Controls = Controls(
            config.CONTROL_PANEL_X, config.CONTROL_PANEL_Y,
            config.CONTROL_PANEL_WIDTH, config.CONTROL_PANEL_HEIGHT,
            config.CONTROL_PANEL_BG_COLOR
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

        print(f"Aplicación inicializada. Herramienta actual: {self.current_tool}")


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

    def _reset_all_states(self) -> None:
        """
        Resetea todos los estados de dibujo pendientes.

        Pone a None o vacía las listas de puntos temporales utilizados por las
        diferentes herramientas de dibujo (línea, círculo, Bézier, etc.).
        Se llama al cambiar de herramienta, limpiar el lienzo o cancelar una acción.
        """
        print("Reseteando estados de dibujo pendientes...")
        self.line_start_point = None
        self.circle_center = None
        self.bezier_points = []
        self.triangle_points = []
        self.rectangle_points = []
        self.polygon_points = []
        self.ellipse_points = []

    def _handle_events(self) -> None:
        """
        Maneja los eventos de entrada del usuario (teclado, ratón).

        Procesa eventos como clics del ratón sobre el lienzo o los controles,
        y pulsaciones de teclas (ESC para cancelar, 'c' para limpiar).
        Actualiza el estado de la aplicación según la interacción del usuario
        y la herramienta seleccionada.
        """
        # Obtener posición relativa del ratón respecto al panel de controles
        # Necesario para detectar hover y clics en botones.
        mouse_pos_on_controls: Optional[Tuple[int, int]] = None
        abs_mouse_pos: Tuple[int, int] = pygame.mouse.get_pos() # Posición absoluta actual
        if self.controls.rect.collidepoint(abs_mouse_pos):
            # Calcular posición relativa al panel de control
            mouse_pos_on_controls = (abs_mouse_pos[0] - self.controls.rect.x,
                                     abs_mouse_pos[1] - self.controls.rect.y)

        # Actualizar estado hover de los botones ANTES de procesar eventos de clic
        self.controls.update(mouse_pos_on_controls)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Clic izquierdo
                    # Usamos abs_mouse_pos que obtuvimos antes del bucle

                    # Verificar clic en el lienzo
                    if self.canvas.rect.collidepoint(abs_mouse_pos):
                        # Calcular posición relativa al lienzo
                        relative_x = abs_mouse_pos[0] - self.canvas.rect.x
                        relative_y = abs_mouse_pos[1] - self.canvas.rect.y
                        current_point = Point(relative_x, relative_y)
                        print(f"Clic en Lienzo en ({relative_x}, {relative_y}). Herramienta: {self.current_tool}")

                        # --- Lógica según herramienta ---
                        if self.current_tool == "pixel":
                            self.canvas.draw_pixel(current_point.x, current_point.y, self.draw_color)

                        elif self.current_tool in ["dda_line", "bresenham_line"]:
                            if not self.line_start_point:
                                self.line_start_point = current_point
                                print(f"  Inicio línea en {current_point}")
                            else:
                                print(f"  Fin línea en {current_point}")
                                if self.current_tool == "dda_line":
                                    self._draw_dda_line(self.line_start_point, current_point, self.draw_color)
                                else: # bresenham_line
                                    self._draw_bresenham_line(self.line_start_point, current_point, self.draw_color)
                                self.line_start_point = None # Resetear para la próxima línea

                        elif self.current_tool == "bresenham_circle":
                            if not self.circle_center:
                                self.circle_center = current_point
                                print(f"  Centro círculo en {current_point}")
                            else:
                                # Calcular radio como distancia euclidiana
                                dx = current_point.x - self.circle_center.x
                                dy = current_point.y - self.circle_center.y
                                radius = int(math.sqrt(dx*dx + dy*dy))
                                print(f"  Punto borde en {current_point}, Radio calculado: {radius}")
                                self._draw_bresenham_circle(self.circle_center, radius)
                                self.circle_center = None # Resetear

                        elif self.current_tool == "ellipse":
                             if len(self.ellipse_points) == 0:
                                 self.ellipse_points.append(current_point) # Centro
                                 print(f"  Centro elipse en {current_point}")
                             elif len(self.ellipse_points) == 1:
                                 # Segundo punto define los radios
                                 center = self.ellipse_points[0]
                                 rx = abs(current_point.x - center.x)
                                 ry = abs(current_point.y - center.y)
                                 print(f"  Punto borde en {current_point}, Rx={rx}, Ry={ry}")
                                 self._draw_ellipse(center, rx, ry)
                                 self.ellipse_points = [] # Resetear

                        elif self.current_tool == "bezier_curve":
                            self.bezier_points.append(current_point)
                            print(f"  Añadido punto Bézier {len(self.bezier_points)}/4: {current_point}")
                            # Dibujar punto actual para feedback (se hace en _render)
                            # self.canvas.draw_pixel(current_point.x, current_point.y, config.RED)
                            if len(self.bezier_points) == 4:
                                print("  Dibujando curva Bézier...")
                                self._draw_bezier_curve(self.bezier_points)
                                self.bezier_points = [] # Resetear

                        elif self.current_tool == "triangle":
                            self.triangle_points.append(current_point)
                            print(f"  Añadido punto Triángulo {len(self.triangle_points)}/3: {current_point}")
                            # self.canvas.draw_pixel(current_point.x, current_point.y, config.GREEN) # Feedback en _render
                            if len(self.triangle_points) == 3:
                                print("  Dibujando triángulo...")
                                self._draw_triangle(self.triangle_points)
                                self.triangle_points = [] # Resetear

                        elif self.current_tool == "rectangle":
                            self.rectangle_points.append(current_point)
                            print(f"  Añadido punto Rectángulo {len(self.rectangle_points)}/2: {current_point}")
                            # self.canvas.draw_pixel(current_point.x, current_point.y, config.BLUE) # Feedback en _render
                            if len(self.rectangle_points) == 2:
                                print("  Dibujando rectángulo...")
                                self._draw_rectangle(self.rectangle_points[0], self.rectangle_points[1])
                                self.rectangle_points = [] # Resetear

                        elif self.current_tool == "polygon":
                            # Comprobar si se hace clic cerca del primer punto para cerrar
                            should_close = False
                            # Necesitamos al menos 2 puntos existentes para poder cerrar al hacer el tercer clic (o posterior)
                            if len(self.polygon_points) >= 2:
                                first_point = self.polygon_points[0]
                                dx = current_point.x - first_point.x
                                dy = current_point.y - first_point.y
                                distance = math.sqrt(dx*dx + dy*dy)
                                # Solo se considera cierre si hay al menos 3 vértices en total (2 existentes + el clic actual cerca del primero)
                                if distance < config.POLYGON_CLOSE_THRESHOLD and len(self.polygon_points) >= 2:
                                    should_close = True
                                    print(f"  Detectado cierre de polígono (distancia: {distance:.1f})")

                            if should_close:
                                # Solo cerrar si hay al menos 3 vértices (2 ya puestos + el clic actual que cierra)
                                print(f"  Cerrando polígono. Último lado: {self.polygon_points[-1]} -> {self.polygon_points[0]}")
                                self._draw_bresenham_line(self.polygon_points[-1], self.polygon_points[0], self.draw_color)
                                self.polygon_points = [] # Resetear
                                # else: # Ya no es necesario este else, la condición de cierre implica >= 2 puntos
                                #    print("  No se puede cerrar polígono con menos de 3 vértices.")
                                # No añadir el punto si la intención era cerrar
                            else:
                                self.polygon_points.append(current_point)
                                print(f"  Añadido punto Polígono {len(self.polygon_points)}: {current_point}")
                                # self.canvas.draw_pixel(current_point.x, current_point.y, config.DARK_GRAY) # Feedback en _render
                                # Dibujar el último segmento añadido (si hay al menos 2 puntos)
                                if len(self.polygon_points) >= 2:
                                    # Llamamos a _draw_polygon que ahora solo dibuja el último segmento
                                    self._draw_polygon(self.polygon_points)


                    # Verificar clic en el panel de control
                    elif mouse_pos_on_controls: # Si el clic fue sobre el panel (y no sobre el lienzo)
                        print(f"Clic en Panel en ({mouse_pos_on_controls[0]}, {mouse_pos_on_controls[1]})")
                        # Llamar a handle_click y obtener el resultado
                        click_result: Optional[Tuple[str, object]] = self.controls.handle_click(mouse_pos_on_controls)

                        if click_result:
                            click_type, value = click_result # Desempaquetar la tupla

                            if click_type == "tool":
                                tool_id = cast(str, value) # Asegurar tipo
                                print(f"  Botón de Herramienta clickeado: {tool_id}")
                                if tool_id == "clear":
                                    print("  Acción: Limpiar lienzo y resetear estados.")
                                    self.canvas.clear()
                                    self._reset_all_states()
                                    # No cambiamos la herramienta actual al limpiar
                                elif self.current_tool != tool_id: # Si se seleccionó una herramienta diferente
                                    print(f"  Cambiando herramienta a: {tool_id}")
                                    self.current_tool = tool_id
                                    # Resetear estados al cambiar de herramienta
                                    self._reset_all_states()
                                else:
                                     print(f"  Herramienta {tool_id} ya estaba seleccionada.")
                                     # Opcional: resetear estado si se vuelve a clickear la misma herramienta
                                     # self._reset_all_states()

                            elif click_type == "color":
                                color_value = cast(pygame.Color, value) # Asegurar tipo
                                if self.draw_color != color_value:
                                    print(f"  Cambiando color de dibujo a: {color_value}")
                                    self.draw_color = color_value
                                else:
                                    print(f"  Color {color_value} ya estaba seleccionado.")
                        else:
                            print("  Clic en panel, pero no sobre un botón.")

            elif event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_ESCAPE: # Tecla ESC para cancelar acción actual
                     print("Tecla ESC presionada - Cancelando acción actual.")
                     self._reset_all_states()
                 elif event.key == pygame.K_c: # Tecla 'C' para limpiar
                    print("Tecla 'c' presionada - Limpiando lienzo.")
                    self.canvas.clear()
                    self._reset_all_states() # Usar función helper


    def _update(self, dt: float) -> None:
        """
        Actualiza el estado de la aplicación en cada frame.

        Actualmente, esta función no realiza ninguna acción específica, pero
        está presente para futuras expansiones (ej: animaciones, lógica de juego).
        La actualización del estado 'hover' de los botones se realiza en `_handle_events`.

        Args:
            dt (float): Delta time, tiempo transcurrido desde el último frame en segundos.
        """
        pass

    def _render(self) -> None:
        """
        Dibuja todos los elementos visibles en la pantalla.

        Limpia la pantalla, dibuja el lienzo, el panel de controles, y cualquier
        feedback visual temporal para las herramientas de dibujo activas (puntos
        de control, líneas de previsualización, etc.). Finalmente, actualiza
        la pantalla de Pygame.
        """
        self.screen.fill(config.WINDOW_BG_COLOR) # Limpiar pantalla con color de fondo

        # Dibujar el lienzo sobre la pantalla
        self.canvas.render(self.screen)

        # Dibujar el panel de controles pasando el estado actual
        self.controls.render(self.screen, self.current_tool, self.draw_color)

        # --- Dibujar feedback visual para herramientas multi-punto ---
        # Obtener posición absoluta del ratón si está sobre el lienzo para previsualizaciones
        mouse_pos_abs = pygame.mouse.get_pos()
        mouse_on_canvas = self.canvas.rect.collidepoint(mouse_pos_abs)

        # Dibujar puntos temporales y previsualización para Bézier
        for i, p in enumerate(self.bezier_points):
            p_abs = self.canvas.to_absolute_pos(p)
            pygame.draw.circle(self.screen, config.RED, p_abs, 4) # Círculo rojo pequeño
            if i > 0:
                prev_p_abs = self.canvas.to_absolute_pos(self.bezier_points[i-1])
                pygame.draw.line(self.screen, config.LIGHT_GRAY, prev_p_abs, p_abs, 1)
        # Previsualizar siguiente segmento si hay puntos y el ratón está en el lienzo
        if self.bezier_points and mouse_on_canvas:
             last_p_abs = self.canvas.to_absolute_pos(self.bezier_points[-1])
             pygame.draw.line(self.screen, config.LIGHT_GRAY, last_p_abs, mouse_pos_abs, 1)


        # Dibujar puntos temporales y previsualización para Triángulo
        for i, p in enumerate(self.triangle_points):
            p_abs = self.canvas.to_absolute_pos(p)
            pygame.draw.circle(self.screen, config.GREEN, p_abs, 4)
            if i > 0:
                prev_p_abs = self.canvas.to_absolute_pos(self.triangle_points[i-1])
                pygame.draw.line(self.screen, config.LIGHT_GRAY, prev_p_abs, p_abs, 1)
        # Previsualizar siguiente segmento y cierre
        if self.triangle_points and mouse_on_canvas:
            last_p_abs = self.canvas.to_absolute_pos(self.triangle_points[-1])
            pygame.draw.line(self.screen, config.LIGHT_GRAY, last_p_abs, mouse_pos_abs, 1)
            if len(self.triangle_points) == 2: # Si estamos por poner el tercer punto
                first_p_abs = self.canvas.to_absolute_pos(self.triangle_points[0])
                pygame.draw.line(self.screen, config.LIGHT_GRAY, mouse_pos_abs, first_p_abs, 1)


        # Dibujar puntos temporales y previsualización para Rectángulo
        for p in self.rectangle_points:
            pygame.draw.circle(self.screen, config.BLUE, self.canvas.to_absolute_pos(p), 4)
        # Previsualizar rectángulo
        if len(self.rectangle_points) == 1 and mouse_on_canvas:
            p_start_abs = self.canvas.to_absolute_pos(self.rectangle_points[0])
            x0, y0 = p_start_abs
            x1, y1 = mouse_pos_abs
            preview_rect = pygame.Rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
            pygame.draw.rect(self.screen, config.LIGHT_GRAY, preview_rect, 1)


        # Dibujar puntos y líneas temporales para Polígono
        for i, p in enumerate(self.polygon_points):
            p_abs = self.canvas.to_absolute_pos(p)
            pygame.draw.circle(self.screen, config.DARK_GRAY, p_abs, 4)
            # Las líneas entre puntos ya existentes se dibujan al hacer clic
            # if i > 0:
            #     prev_p_abs = self.canvas.to_absolute_pos(self.polygon_points[i-1])
            #     pygame.draw.line(self.screen, config.DARK_GRAY, prev_p_abs, p_abs, 1) # Dibujado por _draw_polygon
        # Previsualizar siguiente segmento y línea de cierre potencial
        if self.polygon_points and mouse_on_canvas:
            last_p_abs = self.canvas.to_absolute_pos(self.polygon_points[-1])
            # Línea desde el último punto al ratón
            pygame.draw.line(self.screen, config.LIGHT_GRAY, last_p_abs, mouse_pos_abs, 1)
            # Línea desde el ratón al primer punto si hay al menos 2 puntos (para cerrar el tercero o más)
            if len(self.polygon_points) >= 2:
                 first_p_abs = self.canvas.to_absolute_pos(self.polygon_points[0])
                 pygame.draw.line(self.screen, config.LIGHT_GRAY, mouse_pos_abs, first_p_abs, 1)


        # Dibujar puntos temporales y previsualización para Elipse
        if len(self.ellipse_points) == 1:
            center_abs = self.canvas.to_absolute_pos(self.ellipse_points[0])
            pygame.draw.circle(self.screen, config.MAGENTA, center_abs, 4)
            # Dibujar previsualización de la elipse
            if mouse_on_canvas:
                rx = abs(mouse_pos_abs[0] - center_abs[0])
                ry = abs(mouse_pos_abs[1] - center_abs[1])
                # Evitar dibujar elipse con radio 0
                if rx > 0 and ry > 0:
                    preview_rect = pygame.Rect(center_abs[0] - rx, center_abs[1] - ry, 2*rx, 2*ry)
                    pygame.draw.ellipse(self.screen, config.LIGHT_GRAY, preview_rect, 1)

        # Dibujar punto inicial y previsualización de línea
        if self.line_start_point:
            start_p_abs = self.canvas.to_absolute_pos(self.line_start_point)
            pygame.draw.circle(self.screen, config.ORANGE, start_p_abs, 4)
            if mouse_on_canvas:
                 pygame.draw.line(self.screen, config.LIGHT_GRAY, start_p_abs, mouse_pos_abs, 1)

        # Dibujar centro y previsualización de círculo
        if self.circle_center:
            center_abs = self.canvas.to_absolute_pos(self.circle_center)
            pygame.draw.circle(self.screen, config.CYAN, center_abs, 4)
            if mouse_on_canvas:
                dx = mouse_pos_abs[0] - center_abs[0]
                dy = mouse_pos_abs[1] - center_abs[1]
                radius = int(math.sqrt(dx*dx + dy*dy))
                if radius > 0:
                    pygame.draw.circle(self.screen, config.LIGHT_GRAY, center_abs, radius, 1)

        pygame.display.flip() # Actualizar la pantalla completa


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
        # Pygame se cierra en main.py's finally block

    # El método __del__ fue eliminado ya que el cierre de Pygame
    # se gestiona de forma más fiable en el bloque finally de main.py.