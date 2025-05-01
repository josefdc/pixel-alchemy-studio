"""
Módulo de configuración para la aplicación Graficador Geométrico.

Define constantes utilizadas en toda la aplicación, como dimensiones de la pantalla,
colores predefinidos, configuraciones de la interfaz de usuario y parámetros
relacionados con el dibujo y el juego.
"""

import pygame
from typing import Dict  # Import Dict for type hinting

# --- Dimensiones ---
SCREEN_WIDTH: int = 1024
SCREEN_HEIGHT: int = 768

# Dimensiones del Panel de Control (a la derecha)
CONTROL_PANEL_WIDTH: int = 224  # Ancho del panel
CONTROL_PANEL_HEIGHT: int = SCREEN_HEIGHT
CONTROL_PANEL_X: int = SCREEN_WIDTH - CONTROL_PANEL_WIDTH  # Posición X
CONTROL_PANEL_Y: int = 0

# Dimensiones del Lienzo (a la izquierda)
CANVAS_WIDTH: int = SCREEN_WIDTH - CONTROL_PANEL_WIDTH  # Ancho calculado
CANVAS_HEIGHT: int = SCREEN_HEIGHT
CANVAS_X: int = 0
CANVAS_Y: int = 0

# --- Colores ---
# Define colores estándar utilizando pygame.Color para consistencia.
WHITE: pygame.Color = pygame.Color("white")
BLACK: pygame.Color = pygame.Color("black")
RED: pygame.Color = pygame.Color("red")
GREEN: pygame.Color = pygame.Color("green")
BLUE: pygame.Color = pygame.Color("blue")
MAGENTA: pygame.Color = pygame.Color("magenta")
CYAN: pygame.Color = pygame.Color("cyan")
YELLOW: pygame.Color = pygame.Color("yellow")
ORANGE: pygame.Color = pygame.Color("orange")  # Added for line start point feedback
LIGHT_GRAY: pygame.Color = pygame.Color("lightgray")
DARK_GRAY: pygame.Color = pygame.Color("darkgray")

# Colores de la interfaz
CANVAS_BG_COLOR: pygame.Color = WHITE
CONTROL_PANEL_BG_COLOR: pygame.Color = LIGHT_GRAY
WINDOW_BG_COLOR: pygame.Color = pygame.Color(200, 200, 200)  # Color de fondo para la ventana principal

# --- Juego ---
WINDOW_TITLE: str = "Graficador Geométrico Interactivo"
FPS: int = 60

# --- Dibujo ---
POLYGON_CLOSE_THRESHOLD: int = 10  # Píxeles de distancia para detectar clic cerca del inicio y cerrar el polígono

# --- Colores Disponibles para Selección en la UI ---
# Mapea nombres de colores legibles a objetos pygame.Color.
AVAILABLE_COLORS: Dict[str, pygame.Color] = {
    "Negro": BLACK,
    "Rojo": RED,
    "Verde": GREEN,
    "Azul": BLUE,
    "Gris": DARK_GRAY,
    "Blanco": WHITE,
    # Se pueden añadir más colores aquí si se desea ampliar la paleta.
}