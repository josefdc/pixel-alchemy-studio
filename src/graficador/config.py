"""
src/graficador/config.py
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

# --- Configuración de Gemini ---
GEMINI_MODEL_NAME: str = "gemini-2.0-flash-exp"  # Modelo para generación de imagen nativa
# Textos para la UI relacionados con IA
GEMINI_BUTTON_TEXT: str = "Generar con IA (G)"
PROMPT_INPUT_PLACEHOLDER: str = "Escribe tu idea aquí y presiona Enter..."
PROMPT_ACTIVE_PREFIX: str = "Prompt IA: "
GEMINI_STATUS_DEFAULT: str = "IA lista. Dibuja algo y presiona 'G'."
GEMINI_STATUS_LOADING: str = "IA pensando..."
GEMINI_STATUS_ERROR_API_KEY: str = "Error: API Key de Gemini no configurada."
GEMINI_STATUS_ERROR_LIB: str = "Error: Librerías de IA no encontradas."
GEMINI_STATUS_ERROR_GENERAL: str = "Error de IA. Intenta de nuevo."

# --- NUEVA CONFIGURACIÓN PARA VEO ---
VEO_BUTTON_TEXT: str = "Video con Veo (V)"  # Texto para el botón
VEO_MODEL_NAME: str = "veo-2.0-generate-001"  # Modelo Veo
VEO_SIMULATED_POLL_INTERVAL_MS: int = 3000  # Milisegundos para simular espera de Veo
VEO_STATUS_GENERATING: str = "Generando video con Veo... (simulado)"
VEO_STATUS_SUCCESS: str = "¡Video generado con Veo con éxito! (simulado)"
VEO_STATUS_ERROR_API: str = "Error: API de Veo no disponible o problema."
# --- FIN DE NUEVA CONFIGURACIÓN ---

# --- NUEVA CONFIGURACIÓN PARA VEO (AMPLIADA) ---
VEO_BUTTON_TEXT: str = "Video con Veo (V)"  # Texto para el botón (ya lo tienes)
VEO_MODEL_NAME: str = "veo-2.0-generate-001" # Modelo Veo (ya lo tienes)

# Tiempos para el polling de Veo (en milisegundos)
VEO_INITIAL_POLL_DELAY_MS: int = 10000  # 10 segundos antes de la primera verificación
VEO_POLLING_INTERVAL_MS: int = 15000    # Verificar cada 15 segundos después

# Mensajes de estado para Veo
VEO_STATUS_STARTING: str = "Iniciando generación de video con Veo..."
VEO_STATUS_GENERATING: str = "Veo está generando video (puede tardar minutos)..."
VEO_STATUS_POLLING: str = "Consultando estado de generación de Veo..."
VEO_STATUS_SUCCESS: str = "¡Video(s) de Veo guardado(s) en el directorio del proyecto!"
VEO_STATUS_ERROR_API: str = "Error con la API de Veo. Verifica la configuración o la API Key."
VEO_STATUS_ERROR_NO_PROMPT_OR_IMAGE: str = "Veo necesita un prompt o un dibujo en el lienzo."
VEO_STATUS_PROCESSING_ANOTHER_OP: str = "IA ya está procesando una solicitud. Espera por favor."

# Parámetros por defecto para la generación de Veo (puedes ajustarlos)
VEO_DEFAULT_ASPECT_RATIO: str = "16:9" # "16:9" o "9:16"
VEO_DEFAULT_DURATION_SECONDS: int = 5   # entre 5 y 8
VEO_DEFAULT_PERSON_GENERATION: str = "allow_adult" # "dont_allow" o "allow_adult"

# Colores adicionales para la UI de IA
PROMPT_INPUT_BG_COLOR: pygame.Color = pygame.Color("whitesmoke")
PROMPT_INPUT_TEXT_COLOR: pygame.Color = BLACK
STATUS_MESSAGE_COLOR: pygame.Color = pygame.Color(50, 50, 50)  # Gris oscuro para texto de estado