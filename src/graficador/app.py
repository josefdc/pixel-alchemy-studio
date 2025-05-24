"""
src/graficador/app.py
Main module for the Interactive Geometric Plotter application.

This module contains the `Application` class that manages the application
lifecycle, handles user events, coordinates drawing on the canvas and
interaction with controls. Integrates geometric drawing algorithms and
necessary data structures for interactive figure creation.
"""

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
    print("WARNING: 'google-genai' and/or 'Pillow' libraries not installed. AI functionality will not be available.")

class Application:
    """
    Main class that encapsulates the graphics application logic.

    Manages Pygame initialization, main window, drawing canvas, control panel,
    main event loop, state updates and interface rendering. Maintains current
    tool state and points needed to draw different geometric figures.

    Attributes:
        screen: Main Pygame surface window
        clock: Pygame clock for FPS control
        is_running: Flag indicating if main loop should continue
        canvas: Drawing canvas instance
        controls: Control panel instance
        current_tool: Active drawing tool identifier
        line_start_point: Start point for drawing lines
        circle_center: Center point for drawing circles
        bezier_points: List of control points for Bézier curves
        triangle_points: List of vertices for drawing triangles
        rectangle_points: List of opposite corners for drawing rectangles
        polygon_points: List of vertices for drawing polygons
        ellipse_points: List of points (center, edge) for drawing ellipses
        draw_color: Currently selected drawing color
        is_drawing: Flag to know if currently drawing
        last_mouse_pos_for_pixel_draw: Last mouse position for pixel drawing
        gemini_client: Gemini client instance
        is_typing_prompt: Flag for prompt input mode
        current_prompt_text: Current prompt text being typed
        generated_image_surface: Generated image surface
        gemini_status_message: Current Gemini status message
        is_veo_processing: Flag for Veo processing state
        veo_operation_name: Current Veo operation name
        current_veo_operation_object: Current Veo operation object
        VEO_POLLING_EVENT: Custom event for Veo polling
    """
    
    def __init__(self) -> None:
        """Initialize the application, Pygame, screen, canvas and controls."""
        pygame.init()
        
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

        self.canvas: Canvas = Canvas(
            config.CANVAS_X, config.CANVAS_Y,
            config.CANVAS_WIDTH, config.CANVAS_HEIGHT,
            config.CANVAS_BG_COLOR
        )

        self.controls: Controls = Controls(
            config.CONTROL_PANEL_X, config.CONTROL_PANEL_Y,
            config.CONTROL_PANEL_WIDTH, config.CONTROL_PANEL_HEIGHT,
            config.CONTROL_PANEL_BG_COLOR,
            self.ui_font_normal,
            self.ui_font_small
        )

        self.current_tool: str = "pixel"
        self.line_start_point: Optional[Point] = None
        self.circle_center: Optional[Point] = None
        self.bezier_points: List[Point] = []
        self.triangle_points: List[Point] = []
        self.rectangle_points: List[Point] = []
        self.polygon_points: List[Point] = []
        self.ellipse_points: List[Point] = []
        self.draw_color: pygame.Color = config.BLACK
        self.is_drawing: bool = False
        self.last_mouse_pos_for_pixel_draw: Optional[Point] = None
        
        self.gemini_client: Optional[genai.Client] = None
        self.is_typing_prompt: bool = False
        self.current_prompt_text: str = ""
        self.generated_image_surface: Optional[pygame.Surface] = None
        self.gemini_status_message: str = config.GEMINI_STATUS_DEFAULT
        self.is_exporting_image: bool = False
        self.export_filename_text: str = ""
        self.is_veo_processing: bool = False
        self.veo_operation_name: Optional[str] = None
        self.current_veo_operation_object: Optional[any] = None
        self.VEO_POLLING_EVENT = pygame.USEREVENT + 1
        
        self._initialize_gemini()

        print(f"Application initialized. Current tool: {self.current_tool}")
        
        if GEMINI_AVAILABLE and self.gemini_client:
            print(f"Gemini client ready to use with model: {config.GEMINI_MODEL_NAME}")
        else:
            print(f"Gemini status at initialization end: {self.gemini_status_message}")

    def _initialize_gemini(self) -> None:
        """Initialize Gemini client if libraries and API key are available."""
        if not GEMINI_AVAILABLE:
            self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            print(f"WARNING: {self.gemini_status_message} AI libraries not available.")
            return

        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                self.gemini_status_message = config.GEMINI_STATUS_ERROR_API_KEY
                print(f"WARNING: {self.gemini_status_message}")
                return

            self.gemini_client = genai.Client(api_key=api_key)
            self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
            print("Gemini client initialized successfully using 'google-genai' SDK.")

        except Exception as e:
            self.gemini_status_message = f"Error initializing Gemini: {str(e)[:150]}"
            print(f"GENERAL ERROR IN _initialize_gemini: {self.gemini_status_message}")
            traceback.print_exc()
            self.gemini_client = None

    def _draw_dda_line(self, p1: Point, p2: Point, color: pygame.Color) -> None:
        """
        Draw a line using the DDA algorithm.

        Args:
            p1: Line start point (canvas relative coordinates)
            p2: Line end point (canvas relative coordinates)
            color: Line color
        """
        dda_line(p1, p2, self.canvas.draw_pixel, color)

    def _draw_bresenham_line(self, p1: Point, p2: Point, color: pygame.Color) -> None:
        """
        Draw a line using Bresenham's algorithm.

        Args:
            p1: Line start point (canvas relative coordinates)
            p2: Line end point (canvas relative coordinates)
            color: Line color
        """
        bresenham_line(p1, p2, self.canvas.draw_pixel, color)

    def _draw_bresenham_circle(self, center: Point, radius: int) -> None:
        """
        Draw a circle using Bresenham's circle algorithm.

        Args:
            center: Circle center (canvas relative coordinates)
            radius: Circle radius in pixels
        """
        if radius >= 0:
            bresenham_circle(center, radius, self.canvas.draw_pixel, self.draw_color)
        else:
            print("Error: Circle radius cannot be negative.")

    def _draw_bezier_curve(self, points: List[Point]) -> None:
        """
        Draw a cubic Bézier curve using the corresponding algorithm.

        The curve is drawn by segmenting it and drawing straight lines
        (using Bresenham) between calculated points.

        Args:
            points: List of 4 control points (P0, P1, P2, P3) in canvas relative coordinates
        """
        if len(points) == 4:
            cubic_bezier(points[0], points[1], points[2], points[3],
                         self._draw_bresenham_line, self.draw_color)

    def _draw_triangle(self, points: List[Point]) -> None:
        """
        Draw a triangle connecting the 3 given vertices with lines (Bresenham).

        Args:
            points: List of 3 points (vertices) of the triangle in canvas relative coordinates
        """
        if len(points) == 3:
            print(f"Drawing Triangle: {points[0]}, {points[1]}, {points[2]}")
            self._draw_bresenham_line(points[0], points[1], self.draw_color)
            self._draw_bresenham_line(points[1], points[2], self.draw_color)
            self._draw_bresenham_line(points[2], points[0], self.draw_color)

    def _draw_rectangle(self, p_start: Point, p_end: Point) -> None:
        """
        Draw a rectangle defined by two opposite corners using lines (Bresenham).

        Args:
            p_start: First rectangle corner (canvas relative)
            p_end: Opposite rectangle corner (canvas relative)
        """
        x0, y0 = p_start.x, p_start.y
        x1, y1 = p_end.x, p_end.y
        
        p1 = Point(x1, y0)
        p3 = Point(x0, y1)
        print(f"Drawing Rectangle: P0={p_start}, P1={p1}, P2={p_end}, P3={p3}")
        
        self._draw_bresenham_line(p_start, p1, self.draw_color)
        self._draw_bresenham_line(p1, p_end, self.draw_color)
        self._draw_bresenham_line(p_end, p3, self.draw_color)
        self._draw_bresenham_line(p3, p_start, self.draw_color)

    def _draw_polygon(self, points: List[Point]) -> None:
        """
        Draw polygon segments connecting given vertices with lines (Bresenham).

        Note: This function draws segments as points are added.
        Polygon closure (last vertex to first) is handled in `_handle_events`.

        Args:
            points: List of polygon vertices so far (canvas relative coordinates)
        """
        if len(points) < 2:
            return
        
        start_point = points[-2]
        end_point = points[-1]
        print(f"  Drawing polygon side: {start_point} -> {end_point}")
        self._draw_bresenham_line(start_point, end_point, self.draw_color)

    def _draw_ellipse(self, center: Point, rx: int, ry: int) -> None:
        """
        Draw an ellipse using the midpoint algorithm.

        Args:
            center: Ellipse center (canvas relative coordinates)
            rx: Horizontal radius (major or minor semi-axis) in pixels
            ry: Vertical radius (major or minor semi-axis) in pixels
        """
        if rx >= 0 and ry >= 0:
            midpoint_ellipse(center, rx, ry, self.canvas.draw_pixel, self.draw_color)
        else:
            print("Error: Ellipse radii cannot be negative.")

    def _reset_drawing_states(self) -> None:
        """Reset only pending drawing states (points, etc.)."""
        print("Resetting only pending drawing states...")
        self.line_start_point = None
        self.circle_center = None
        self.bezier_points = []
        self.triangle_points = []
        self.rectangle_points = []
        self.polygon_points = []
        self.ellipse_points = []

    def _reset_all_states(self) -> None:
        """Reset all drawing AND AI states."""
        self._reset_drawing_states()
        self.is_typing_prompt = False
        self.current_prompt_text = ""
        self.is_exporting_image = False
        self.export_filename_text = ""
        
        self.current_veo_operation_object = None
        if self.is_veo_processing:
            pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
        self.is_veo_processing = False
        self.veo_operation_name = None

        if self.gemini_client:
            self.gemini_status_message = config.GEMINI_STATUS_DEFAULT
        elif self.is_exporting_image: # Keep status if exporting
            pass
        else:
            if not GEMINI_AVAILABLE:
                self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            elif not os.environ.get("GOOGLE_API_KEY"):
                self.gemini_status_message = config.GEMINI_STATUS_ERROR_API_KEY
        
        print(f"ALL states reset. Current AI status: {self.gemini_status_message}")

    def _capture_canvas_as_pil_image(self) -> Optional[PILImage.Image]:
        """
        Capture current canvas surface and convert it to a PIL.Image object.

        Returns:
            PIL Image of the canvas, or None if an error occurs
        """
        if not PILImage:
            self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
            print(f"Error: {self.gemini_status_message}")
            return None
        
        try:
            canvas_surface = self.canvas.surface
            image_bytes_io = io.BytesIO()
            pygame.image.save(canvas_surface, image_bytes_io, "PNG")
            image_bytes_io.seek(0)
            pil_image = PILImage.open(image_bytes_io)
            print("Canvas captured as PIL image.")
            return pil_image
        except Exception as e:
            self.gemini_status_message = f"Error capturing canvas: {str(e)[:100]}"
            print(f"Error: {self.gemini_status_message}")
            return None

    def _save_canvas_image(self, filename: str) -> None:
        """Save the current canvas content to a file."""
        exports_dir = "exports"
        try:
            os.makedirs(exports_dir, exist_ok=True)

            name, ext = os.path.splitext(filename)
            if not ext:
                ext = ".png"  # Default to PNG
                filename = name + ext
            
            ext = ext.lower()
            filepath = os.path.join(exports_dir, filename)

            print(f"Attempting to save image to: {filepath}")

            if ext in (".jpeg", ".jpg"):
                if not PILImage:
                    self.gemini_status_message = "Error: Pillow library (PIL) is required for JPEG export."
                    print(f"Error: {self.gemini_status_message}")
                    return

                pil_image = self._capture_canvas_as_pil_image()
                if pil_image:
                    rgb_pil_image = pil_image.convert('RGB')
                    rgb_pil_image.save(filepath, "JPEG", quality=90)
                    self.gemini_status_message = f"Image saved as {filepath}"
                    print(f"Image successfully saved as {filepath}")
                else:
                    self.gemini_status_message = "Error: Could not capture canvas for JPEG saving."
                    # _capture_canvas_as_pil_image already prints an error
            else:  # Default to PNG
                pygame.image.save(self.canvas.surface, filepath)
                self.gemini_status_message = f"Image saved as {filepath}"
                print(f"Image successfully saved as {filepath}")

        except Exception as e:
            self.gemini_status_message = f"Error saving image: {str(e)[:100]}" # Limit error length
            print(f"ERROR: Failed to save image to {filepath}. Exception: {e}")
            traceback.print_exc()

    def _handle_events(self) -> None:
        """
        Handle user input events (keyboard, mouse), including logic for
        starting and monitoring video generation with Veo.
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
                continue

            if event.type == self.VEO_POLLING_EVENT:
                self._poll_veo_status()
                continue

            if self.is_veo_processing:
                continue

            # Combined prompt/filename input handling
            if (self.is_typing_prompt or self.is_exporting_image) and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.is_typing_prompt:
                        self.is_typing_prompt = False
                        prompt_final = self.current_prompt_text.strip()
                        if not prompt_final:
                            self.gemini_status_message = "Empty prompt. Try again."
                            print("Attempt to generate with empty prompt.")
                        elif not self.gemini_client:
                            self.gemini_status_message = "Error: AI not initialized."
                            print("Attempt to generate without AI client.")
                        else:
                            print(f"Prompt finalized: '{prompt_final}'. Starting image generation...")
                            self.gemini_status_message = config.GEMINI_STATUS_LOADING
                            pil_image = self._capture_canvas_as_pil_image()
                            if pil_image:
                               self._call_gemini_api(pil_image, prompt_final)
                            else:
                                self.gemini_status_message = "Error: Could not capture canvas for Gemini."
                                print(self.gemini_status_message)
                    elif self.is_exporting_image:
                        filename = self.export_filename_text.strip()
                        if not filename:
                            self.gemini_status_message = "Filename cannot be empty. Please enter a filename."
                            # self.is_exporting_image remains True for user to try again
                            print("Export image: filename was empty.")
                        else:
                            self.is_exporting_image = False # Exit input mode
                            self.export_filename_text = ""  # Clear input field text
                            self._save_canvas_image(filename) # Call the new save method

                elif event.key == pygame.K_BACKSPACE:
                    if self.is_typing_prompt:
                        self.current_prompt_text = self.current_prompt_text[:-1]
                    elif self.is_exporting_image:
                        self.export_filename_text = self.export_filename_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    print("Input cancelled by ESC.")
                    self._reset_all_states() # Resets both typing and exporting states
                else:
                    if self.is_typing_prompt:
                        if len(self.current_prompt_text) < 200:
                            self.current_prompt_text += event.unicode
                    elif self.is_exporting_image:
                        if len(self.export_filename_text) < 200: # Max filename length
                            self.export_filename_text += event.unicode
                continue

            if self.is_typing_prompt and event.type == pygame.KEYDOWN: # This block is now part of the combined one above
                if event.key == pygame.K_RETURN:
                    self.is_typing_prompt = False
                    prompt_final = self.current_prompt_text.strip()
                    if not prompt_final:
                        self.gemini_status_message = "Empty prompt. Try again."
                        print("Attempt to generate with empty prompt.")
                    elif not self.gemini_client:
                        self.gemini_status_message = "Error: AI not initialized."
                        print("Attempt to generate without AI client.")
                    else:
                        print(f"Prompt finalized: '{prompt_final}'. Starting image generation...")
                        self.gemini_status_message = config.GEMINI_STATUS_LOADING
                        pil_image = self._capture_canvas_as_pil_image()
                        if pil_image:
                           self._call_gemini_api(pil_image, prompt_final)
                        else:
                            self.gemini_status_message = "Error: Could not capture canvas for Gemini."
                            print(self.gemini_status_message)

                elif event.key == pygame.K_BACKSPACE:
                    self.current_prompt_text = self.current_prompt_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    print("Prompt input cancelled.")
                    self._reset_all_states()
                else:
                    if len(self.current_prompt_text) < 200:
                        self.current_prompt_text += event.unicode
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if mouse_pos_on_controls:
                        click_result = self.controls.handle_click(mouse_pos_on_controls)
                        if click_result:
                            click_type, value = click_result
                            if click_type == "tool":
                                tool_id = cast(str, value)

                                if tool_id == "veo_generate":
                                    if not self.is_veo_processing and not self.is_typing_prompt:
                                        if self.gemini_client:
                                            self.current_tool = tool_id
                                            self._start_veo_generation()
                                        else:
                                            self.gemini_status_message = config.VEO_STATUS_ERROR_API
                                    else:
                                        self.gemini_status_message = config.VEO_STATUS_PROCESSING_ANOTHER_OP
                                    print(self.gemini_status_message)

                                elif tool_id == "gemini_generate":
                                    if GEMINI_AVAILABLE and self.gemini_client:
                                        if not self.is_typing_prompt:
                                            self.is_typing_prompt = True
                                            self.current_prompt_text = ""
                                            self.gemini_status_message = config.PROMPT_INPUT_PLACEHOLDER
                                            self.current_tool = "gemini_generate"
                                            self._reset_drawing_states()
                                            print("Gemini prompt writing mode activated.")
                                    else:
                                        self.gemini_status_message = "Error: AI not available/configured."
                                    print(self.gemini_status_message)
                                
                                elif tool_id == "export_image":
                                    if self.is_typing_prompt: # If coming from AI prompt
                                        self.is_typing_prompt = False
                                        self.current_prompt_text = ""
                                    self.is_exporting_image = True
                                    self.export_filename_text = ""
                                    self.gemini_status_message = "Enter filename (e.g., image.png):"
                                    self.current_tool = "export_image"
                                    self._reset_drawing_states() # Reset points, etc.
                                    print("Export image mode activated.")

                                elif tool_id == "clear":
                                    self.canvas.clear()
                                    self._reset_all_states()
                                    print("Canvas cleared and states reset.")
                                    
                                    if self.is_veo_processing:
                                        pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
                                        self.is_veo_processing = False
                                        self.veo_operation_name = None
                                        self.gemini_status_message = "Veo processing cancelled by cleanup."
                                        print(self.gemini_status_message)

                                elif self.current_tool != tool_id:
                                    if self.is_typing_prompt or self.is_exporting_image:
                                        self._reset_all_states() # Full reset if switching from input modes
                                    self.current_tool = tool_id
                                    self._reset_drawing_states()
                                    print(f"Tool changed to: {tool_id}")
                                else: # Clicked on the same tool again
                                    if not self.is_exporting_image: # Don't reset points if already in export mode and clicking export again
                                        self._reset_drawing_states()
                                        print(f"Tool {tool_id} points reset.")

                            elif click_type == "color":
                                color_value = cast(pygame.Color, value)
                                if self.draw_color != color_value:
                                    self.draw_color = color_value
                                    print(f"Drawing color changed to: {color_value}")
                    
                    elif self.canvas.rect.collidepoint(abs_mouse_pos):
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
                            self.ellipse_points.append(current_point)
                            if len(self.ellipse_points) == 2:
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
                                distance_to_first = math.sqrt(
                                    (current_point.x - first_point.x)**2 + 
                                    (current_point.y - first_point.y)**2
                                )
                                if distance_to_first < config.POLYGON_CLOSE_THRESHOLD:
                                    should_close = True
                            
                            if should_close:
                                if len(self.polygon_points) >= 2:
                                    self._draw_bresenham_line(self.polygon_points[-1], self.polygon_points[0], self.draw_color)
                                self.polygon_points = []
                            else:
                                self.polygon_points.append(current_point)
                                if len(self.polygon_points) >= 2:
                                    self._draw_polygon(self.polygon_points)

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
                if event.key == pygame.K_ESCAPE:
                    self._reset_drawing_states()
                    print("Pending drawing points reset by ESC.")
                
                elif event.key == pygame.K_c:
                    self.canvas.clear()
                    self._reset_all_states()
                    print("Canvas cleared and all states reset by 'C' shortcut.")

                elif event.key == pygame.K_g:
                    if GEMINI_AVAILABLE and self.gemini_client:
                        self.is_typing_prompt = True
                        self.current_prompt_text = ""
                        self.gemini_status_message = config.PROMPT_INPUT_PLACEHOLDER
                        self.current_tool = "gemini_generate"
                        self._reset_drawing_states()
                        print("Gemini prompt writing mode activated by 'G' shortcut.")
                    else:
                        self.gemini_status_message = "Error: AI not available/configured."
                        print(self.gemini_status_message)
                
                elif event.key == pygame.K_v:
                    if not self.is_veo_processing and not self.is_typing_prompt:
                        if self.gemini_client:
                            self.current_tool = "veo_generate"
                            self._start_veo_generation()
                        else:
                            self.gemini_status_message = config.VEO_STATUS_ERROR_API
                    else:
                        self.gemini_status_message = config.VEO_STATUS_PROCESSING_ANOTHER_OP
                    print(self.gemini_status_message)

    def _render(self) -> None:
        """
        Draw all visible elements on screen.

        Clears screen, draws canvas (which may now contain AI-generated image),
        control panel, prompt/status UI, and visual tool feedback.
        Finally updates the Pygame screen.
        """
        self.screen.fill(config.WINDOW_BG_COLOR)
        self.canvas.render(self.screen)
        self.controls.render(self.screen, self.current_tool, self.draw_color)

        status_area_rect = pygame.Rect(0, config.SCREEN_HEIGHT - 40, config.SCREEN_WIDTH, 40)
        if self.is_typing_prompt or self.is_exporting_image:
            cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            current_text_for_input = self.current_prompt_text if self.is_typing_prompt else self.export_filename_text
            input_prefix = config.PROMPT_ACTIVE_PREFIX if self.is_typing_prompt else "Filename: "
            
            input_text_render = f"{input_prefix}{current_text_for_input}{cursor}"
            prompt_surf = self.ui_font_normal.render(input_text_render, True, config.PROMPT_INPUT_TEXT_COLOR, config.PROMPT_INPUT_BG_COLOR)
            prompt_rect = prompt_surf.get_rect(centerx=self.screen.get_rect().centerx, bottom=config.SCREEN_HEIGHT - 10)
            prompt_rect.left = max(10, prompt_rect.left)
            prompt_rect.right = min(config.SCREEN_WIDTH - 10, prompt_rect.right)
            
            bg_rect = prompt_rect.inflate(10, 6)
            bg_rect.width = min(bg_rect.width, config.SCREEN_WIDTH - 20)
            bg_rect.centerx = self.screen.get_rect().centerx
            pygame.draw.rect(self.screen, config.PROMPT_INPUT_BG_COLOR, bg_rect, border_radius=3)
            pygame.draw.rect(self.screen, config.DARK_GRAY, bg_rect, 1, border_radius=3)
            self.screen.blit(prompt_surf, prompt_rect)
        elif self.gemini_status_message:
            status_surf = self.ui_font_normal.render(self.gemini_status_message, True, config.STATUS_MESSAGE_COLOR)
            status_rect = status_surf.get_rect(centerx=self.screen.get_rect().centerx, bottom=config.SCREEN_HEIGHT - 10)
            status_rect.left = max(10, status_rect.left)
            status_rect.right = min(config.SCREEN_WIDTH - 10, status_rect.right)
            
            bg_rect_status = status_rect.inflate(10, 6)
            # Ensure status message bg does not overlap with potential export filename input if too wide
            max_status_width = config.SCREEN_WIDTH - 20
            if self.is_exporting_image: # Potentially show filename input and status
                 # This logic might need adjustment if export filename input is also shown here
                pass # For now, allow overlap or assume export filename is primary if active

            bg_rect_status.width = min(bg_rect_status.width, max_status_width)
            bg_rect_status.centerx = self.screen.get_rect().centerx
            pygame.draw.rect(self.screen, config.LIGHT_GRAY, bg_rect_status, border_radius=3)
            self.screen.blit(status_surf, status_rect)

        mouse_pos_abs = pygame.mouse.get_pos()
        mouse_on_canvas = self.canvas.rect.collidepoint(mouse_pos_abs)

        if not self.is_typing_prompt and not self.is_exporting_image: # Don't draw tool previews if typing prompt or filename
            for i, p in enumerate(self.bezier_points):
                p_abs = self.canvas.to_absolute_pos(p)
                pygame.draw.circle(self.screen, config.RED, p_abs, 4)
                if i > 0:
                    prev_p_abs = self.canvas.to_absolute_pos(self.bezier_points[i-1])
                    pygame.draw.line(self.screen, config.LIGHT_GRAY, prev_p_abs, p_abs, 1)
            if self.bezier_points and mouse_on_canvas:
                last_p_abs = self.canvas.to_absolute_pos(self.bezier_points[-1])
                pygame.draw.line(self.screen, config.LIGHT_GRAY, last_p_abs, mouse_pos_abs, 1)

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

            for p in self.rectangle_points:
                pygame.draw.circle(self.screen, config.BLUE, self.canvas.to_absolute_pos(p), 4)
            if len(self.rectangle_points) == 1 and mouse_on_canvas:
                p_start_abs = self.canvas.to_absolute_pos(self.rectangle_points[0])
                x0, y0 = p_start_abs
                x1, y1 = mouse_pos_abs
                preview_rect = pygame.Rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
                pygame.draw.rect(self.screen, config.LIGHT_GRAY, preview_rect, 1)

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

            if len(self.ellipse_points) == 1:
                center_abs = self.canvas.to_absolute_pos(self.ellipse_points[0])
                pygame.draw.circle(self.screen, config.MAGENTA, center_abs, 4)
                if mouse_on_canvas:
                    rx = abs(mouse_pos_abs[0] - center_abs[0])
                    ry = abs(mouse_pos_abs[1] - center_abs[1])
                    if rx > 0 and ry > 0:
                        preview_rect = pygame.Rect(center_abs[0] - rx, center_abs[1] - ry, 2*rx, 2*ry)
                        pygame.draw.ellipse(self.screen, config.LIGHT_GRAY, preview_rect, 1)

            if self.line_start_point:
                start_p_abs = self.canvas.to_absolute_pos(self.line_start_point)
                pygame.draw.circle(self.screen, config.ORANGE, start_p_abs, 4)
                if mouse_on_canvas:
                    pygame.draw.line(self.screen, config.LIGHT_GRAY, start_p_abs, mouse_pos_abs, 1)

            if self.circle_center:
                center_abs = self.canvas.to_absolute_pos(self.circle_center)
                pygame.draw.circle(self.screen, config.CYAN, center_abs, 4)
                if mouse_on_canvas:
                    dx = mouse_pos_abs[0] - center_abs[0]
                    dy = mouse_pos_abs[1] - center_abs[1]
                    radius = int(math.sqrt(dx*dx + dy*dy))
                    if radius > 0:
                        pygame.draw.circle(self.screen, config.LIGHT_GRAY, center_abs, radius, 1)

        pygame.display.flip()

    def _update(self, dt: float) -> None:
        """
        Update application state each frame.

        Currently this function performs no specific actions, but is present
        for future expansions (e.g. animations, game logic).

        Args:
            dt: Delta time, elapsed time since last frame in seconds
        """
        pass

    def run(self) -> None:
        """
        Start and execute the main application loop.

        The loop continues while `self.is_running` is True. In each iteration,
        controls framerate, handles events, updates state and renders screen.
        """
        while self.is_running:
            dt: float = self.clock.tick(config.FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()

        print("Exiting application...")
    
    def _call_gemini_api(self, image_input: PILImage.Image, prompt_text: str) -> None:
        """
        Call Gemini API with canvas image and user prompt.
        
        Processes response to get generated image and/or text.
        If an image is received, replaces canvas content with it.
        Updates self.gemini_status_message.

        Args:
            image_input: PIL image from canvas
            prompt_text: User's prompt text
        """
        if not self.gemini_client:
            self.gemini_status_message = "Error: Gemini client not initialized."
            print(self.gemini_status_message)
            return
        
        if not PILImage:
             self.gemini_status_message = config.GEMINI_STATUS_ERROR_LIB
             print(f"Error: {self.gemini_status_message}")
             return

        self.gemini_status_message = config.GEMINI_STATUS_LOADING
        print(f"Calling Gemini API with original prompt: '{prompt_text}' and input image.")
        self._render()
        pygame.time.wait(10)

        try:
            enhanced_prompt_text = f"{prompt_text}. Keep the same minimal line doodle style."
            print(f"Enhanced prompt sent to Gemini: '{enhanced_prompt_text}'")

            contents = [ 
                enhanced_prompt_text,
                image_input 
            ]

            generation_config_dict = {
                "response_modalities": ['TEXT', 'IMAGE'], 
                "candidate_count": 1 
            }
            print(f"Using generation_config: {generation_config_dict}")

            generation_config = types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                candidate_count=1
            )
            print(f"Using generation_config: {generation_config}")

            response = self.gemini_client.models.generate_content(
                model=config.GEMINI_MODEL_NAME,
                contents=contents,
                config=generation_config,
            )

            generated_text_response = ""
            image_processed_and_applied = False

            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        generated_text_response += part.text + "\n"
                    
                    elif hasattr(part, 'inline_data') and part.inline_data and part.inline_data.mime_type.startswith('image/'):
                        try:
                            print(f"Received image part with mime_type: {part.inline_data.mime_type}")
                            image_data_bytes = part.inline_data.data
                            
                            generated_pil_image = PILImage.open(io.BytesIO(image_data_bytes))
                            
                            temp_pygame_surface = None
                            mode = generated_pil_image.mode
                            size = generated_pil_image.size
                            data_str = generated_pil_image.tobytes()
                            
                            if mode in ('RGB', 'RGBA'):
                                temp_pygame_surface = pygame.image.fromstring(data_str, size, mode)
                            else: 
                                print(f"Image mode not directly supported: {mode}. Trying to convert to RGBA.")
                                try:
                                     generated_pil_image_converted = generated_pil_image.convert('RGBA')
                                     mode = generated_pil_image_converted.mode
                                     size = generated_pil_image_converted.size
                                     data_str = generated_pil_image_converted.tobytes()
                                     temp_pygame_surface = pygame.image.fromstring(data_str, size, mode)
                                except Exception as convert_err:
                                     print(f"Error converting PIL image to RGBA: {convert_err}")

                            if temp_pygame_surface:
                                print("Replacing canvas content with generated image.")
                                canvas_w, canvas_h = self.canvas.rect.size
                                
                                try:
                                    scaled_generated_surface = pygame.transform.smoothscale(temp_pygame_surface, (canvas_w, canvas_h))
                                except ValueError:
                                    print("Warning: Could not smooth scale, using normal scale.")
                                    scaled_generated_surface = pygame.transform.scale(temp_pygame_surface, (canvas_w, canvas_h))

                                self.canvas.clear() 
                                self.canvas.surface.blit(scaled_generated_surface, (0, 0)) 

                                print("Canvas updated with generated image.")
                                image_processed_and_applied = True 
                        
                        except Exception as img_proc_err:
                            self.gemini_status_message = f"Error processing Gemini image: {str(img_proc_err)[:100]}"
                            print(f"Error: {self.gemini_status_message}")
            
            if image_processed_and_applied:
                self.gemini_status_message = "Canvas updated with AI!"
                if generated_text_response:
                     self.gemini_status_message += " (and text received)"
                     print(f"Additional text from Gemini:\n{generated_text_response.strip()}")
            elif generated_text_response:
                 self.gemini_status_message = f"AI responded with text: {generated_text_response.strip()[:100]}..."
                 print(f"Text-only response from Gemini:\n{generated_text_response.strip()}")
            else:
                block_reason = ""
                block_message = ""
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                     block_reason = f" Reason: {response.prompt_feedback.block_reason}"
                     block_message = f" Msg: {response.prompt_feedback.block_reason_message}" if response.prompt_feedback.block_reason_message else ""
                     self.gemini_status_message = f"Error: AI response blocked.{block_reason}{block_message}"
                else:
                     self.gemini_status_message = "Error: Empty or unexpected AI response."
                print(self.gemini_status_message)

        except Exception as e:
            self.gemini_status_message = f"Error in AI call: {type(e).__name__}"
            print(f"Critical error during Gemini API call: {self.gemini_status_message}")
            traceback.print_exc()

    def _start_veo_generation(self) -> None:
        """
        Start video generation with Veo, ALWAYS using current canvas image
        and a FIXED PROMPT to animate it while maintaining style.
        """
        print("Veo - Starting _start_veo_generation (with canvas image and fixed prompt)...")

        if not self.gemini_client:
            self.gemini_status_message = config.VEO_STATUS_ERROR_API
            print("Veo - Error: Gemini client (needed for Veo) not initialized.")
            return

        if self.is_veo_processing:
            self.gemini_status_message = config.VEO_STATUS_PROCESSING_ANOTHER_OP
            print(f"Veo - {self.gemini_status_message} (Veo already processing).")
            return
        if self.is_typing_prompt:
            self.gemini_status_message = config.VEO_STATUS_PROCESSING_ANOTHER_OP
            print(f"Veo - {self.gemini_status_message} (Gemini prompt writing mode active).")
            return

        pil_image: Optional[PILImage.Image] = self._capture_canvas_as_pil_image()

        if not pil_image:
            self.gemini_status_message = "Veo - Error: No image on canvas to animate."
            print(self.gemini_status_message)
            return

        print(f"Veo - Captured PIL image properties (original): Mode={pil_image.mode}, Size={pil_image.size}")
        try:
            debug_image_filename_png = "debug_veo_input_original.png"
            pil_image.save(debug_image_filename_png)
            print(f"Veo - Original image (PNG) for Veo saved as: {debug_image_filename_png}")
        except Exception as e_save_png:
            print(f"Veo - Error saving original debug image (PNG): {e_save_png}")

        fixed_veo_prompt = "animate keep the style Keep the same minimal line doodle style."
        print(f"Veo - Using fixed prompt for Veo: '{fixed_veo_prompt}'")

        self.is_veo_processing = True
        self.gemini_status_message = config.VEO_STATUS_STARTING
        print(f"Veo - Status updated to: {self.gemini_status_message}")
        self._render() 
        pygame.time.wait(10)

        try:
            veo_config = types.GenerateVideosConfig(
                aspect_ratio=config.VEO_DEFAULT_ASPECT_RATIO,
                duration_seconds=config.VEO_DEFAULT_DURATION_SECONDS,
                person_generation=config.VEO_DEFAULT_PERSON_GENERATION,
                number_of_videos=1
            )
            print(f"Veo - Configuration for generate_videos: {veo_config}")

            image_input_for_api = None
            print("Veo - Processing captured image to send as types.Image (PNG)...")
            try:
                image_bytes_io = io.BytesIO()
                pil_image.save(image_bytes_io, format="PNG") 
                image_bytes = image_bytes_io.getvalue()
                current_mime_type = "image/png"
                print(f"Veo - PNG bytes generated, size: {len(image_bytes)} bytes.")
                
                image_input_for_api = types.Image(image_bytes=image_bytes, mime_type=current_mime_type)
                print(f"Veo - Image successfully converted to types.Image (mime_type: {current_mime_type}).")

            except Exception as e_convert:
                print(f"Veo - CRITICAL: Error building types.Image: {e_convert}")
                traceback.print_exc()
                self.gemini_status_message = f"Error preparing image for Veo: {str(e_convert)[:100]}"
                self.is_veo_processing = False
                return
            
            print(f"Veo - Starting generate_videos call with prompt: '{fixed_veo_prompt}' and with image (types.Image).")
            
            operation = self.gemini_client.models.generate_videos(
                model=config.VEO_MODEL_NAME,
                prompt=fixed_veo_prompt,
                image=image_input_for_api,
                config=veo_config,
            )
            
            self.current_veo_operation_object = operation 
            if self.current_veo_operation_object and hasattr(self.current_veo_operation_object, 'name'):
                self.veo_operation_name_for_log = self.current_veo_operation_object.name 
                self.gemini_status_message = config.VEO_STATUS_GENERATING
                print(f"Veo - Veo operation started. Name: {self.veo_operation_name_for_log}. Status: {self.gemini_status_message}")
                pygame.time.set_timer(self.VEO_POLLING_EVENT, config.VEO_INITIAL_POLL_DELAY_MS, loops=1)
                print(f"Veo - Polling scheduled in {config.VEO_INITIAL_POLL_DELAY_MS / 1000} seconds.")
            else:
                self.gemini_status_message = "Error: generate_videos did not return valid operation object."
                print(f"Veo - {self.gemini_status_message}")
                self.is_veo_processing = False
                self.current_veo_operation_object = None

        except Exception as e: 
            self.gemini_status_message = f"Critical error starting Veo: {type(e).__name__}"
            print(f"Veo - {self.gemini_status_message}: {e}")
            traceback.print_exc()
            self.is_veo_processing = False 
            self.current_veo_operation_object = None
            
    def _poll_veo_status(self) -> None:
        """Query the status of an ongoing Veo operation."""
        
        if not self.current_veo_operation_object or not self.is_veo_processing or not self.gemini_client:
            print("Veo - Poll: No active Veo operation or client not available. Stopping polling.")
            pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
            self.is_veo_processing = False
            self.current_veo_operation_object = None
            return

        current_op_name_for_log = getattr(self.current_veo_operation_object, 'name', 'UNKNOWN_ID')
        
        print(f"Veo - Poll: Querying status of operation: {current_op_name_for_log}")
        self.gemini_status_message = config.VEO_STATUS_POLLING
        self._render()

        try:
            self.current_veo_operation_object = self.gemini_client.operations.get(self.current_veo_operation_object)
            print(f"Veo - Poll: Response from operations.get() received for {current_op_name_for_log}.")

            if self.current_veo_operation_object.done:
                print(f"Veo - Poll: Operation {current_op_name_for_log} marked as 'done'.")
                pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
                self.is_veo_processing = False
                
                operation_final_result = self.current_veo_operation_object
                self.current_veo_operation_object = None

                if hasattr(operation_final_result, 'error') and operation_final_result.error:
                    error_code = getattr(operation_final_result.error, 'code', 'N/A')
                    error_message = getattr(operation_final_result.error, 'message', 'Unknown error in Veo.')
                    self.gemini_status_message = f"Error in Veo (Code: {error_code}): {error_message}"
                    print(f"Veo - Poll: {self.gemini_status_message}")
                
                elif operation_final_result.response and hasattr(operation_final_result.response, 'generated_videos'):
                    generated_videos = operation_final_result.response.generated_videos
                    if generated_videos:
                        print(f"Veo - Poll: {len(generated_videos)} video(s) generated.")
                        saved_count = 0
                        for i, gen_video_metadata in enumerate(generated_videos):
                            video_metadata_name = getattr(gen_video_metadata.video, 'name', f'unnamed_video_{i}')
                            try:
                                timestamp = pygame.time.get_ticks()
                                video_filename = f"veo_video_{timestamp}_{i}.mp4"
                                print(f"Veo - Poll: Processing video {i+1} (ID from API: {video_metadata_name})...")

                                print(f"Veo - Poll: Calling client.files.download for {video_metadata_name}...")
                                video_bytes = self.gemini_client.files.download(file=gen_video_metadata.video) 

                                if video_bytes and isinstance(video_bytes, bytes):
                                    print(f"Veo - Poll: Download completed for {video_metadata_name}. Received {len(video_bytes)} bytes.")
                                    print(f"Veo - Poll: Attempting to save {video_filename}...")
                                    with open(video_filename, "wb") as f:
                                        f.write(video_bytes)
                                    print(f"Veo - Poll: Video {video_filename} saved successfully.")
                                    saved_count += 1
                                else:
                                    print(f"Veo - Poll: Download for {video_metadata_name} did not return valid bytes. Type received: {type(video_bytes)}")

                            except Exception as save_err:
                                print(f"Veo - Poll: Error downloading/saving video {i+1} ({video_filename}): {type(save_err).__name__} - {save_err}")
                                traceback.print_exc()
                        
                        if saved_count > 0:
                            self.gemini_status_message = config.VEO_STATUS_SUCCESS
                        else:
                            self.gemini_status_message = "Veo finished, but could not save videos."
                        print(f"Veo - Poll: Final save status: {self.gemini_status_message}")
                    else:
                        self.gemini_status_message = "Veo finished, but no videos were generated in response."
                        print(f"Veo - Poll: {self.gemini_status_message}")
                else:
                    self.gemini_status_message = "Veo completed operation unexpectedly (no error or valid videos)."
                    print(f"Veo - Poll: {self.gemini_status_message}")
            else:
                pygame.time.set_timer(self.VEO_POLLING_EVENT, config.VEO_POLLING_INTERVAL_MS, loops=1)
                print(f"Veo - Poll: Operation {current_op_name_for_log} still processing. Next query in {config.VEO_POLLING_INTERVAL_MS / 1000}s.")
                self.gemini_status_message = config.VEO_STATUS_GENERATING

        except Exception as e:
            self.gemini_status_message = f"Critical error querying Veo status: {type(e).__name__}"
            current_op_name_for_log_exc = getattr(self.current_veo_operation_object, 'name', 'UNKNOWN_ID_IN_EXCEPTION')
            print(f"Veo - Poll: {self.gemini_status_message} for {current_op_name_for_log_exc}: {e}")
            traceback.print_exc()
            pygame.time.set_timer(self.VEO_POLLING_EVENT, 0)
            self.is_veo_processing = False
            self.current_veo_operation_object = None