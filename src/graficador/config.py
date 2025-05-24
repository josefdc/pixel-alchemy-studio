"""
Configuration module for the Geometric Plotter application.

Defines constants used throughout the application, including screen dimensions,
predefined colors, user interface settings, and parameters related to drawing
and game functionality.
"""

import pygame
from typing import Dict

# Screen dimensions
SCREEN_WIDTH: int = 1024
SCREEN_HEIGHT: int = 768

# Control Panel dimensions (right side)
CONTROL_PANEL_WIDTH: int = 224
CONTROL_PANEL_HEIGHT: int = SCREEN_HEIGHT
CONTROL_PANEL_X: int = SCREEN_WIDTH - CONTROL_PANEL_WIDTH
CONTROL_PANEL_Y: int = 0

# Canvas dimensions (left side)
CANVAS_WIDTH: int = SCREEN_WIDTH - CONTROL_PANEL_WIDTH
CANVAS_HEIGHT: int = SCREEN_HEIGHT
CANVAS_X: int = 0
CANVAS_Y: int = 0

# Standard colors
WHITE: pygame.Color = pygame.Color("white")
BLACK: pygame.Color = pygame.Color("black")
RED: pygame.Color = pygame.Color("red")
GREEN: pygame.Color = pygame.Color("green")
BLUE: pygame.Color = pygame.Color("blue")
MAGENTA: pygame.Color = pygame.Color("magenta")
CYAN: pygame.Color = pygame.Color("cyan")
YELLOW: pygame.Color = pygame.Color("yellow")
ORANGE: pygame.Color = pygame.Color("orange")
LIGHT_GRAY: pygame.Color = pygame.Color("lightgray")
DARK_GRAY: pygame.Color = pygame.Color("darkgray")

# Interface colors
CANVAS_BG_COLOR: pygame.Color = WHITE
CONTROL_PANEL_BG_COLOR: pygame.Color = LIGHT_GRAY
WINDOW_BG_COLOR: pygame.Color = pygame.Color(200, 200, 200)

# Game settings
WINDOW_TITLE: str = "Interactive Geometric Plotter"
FPS: int = 60

# Drawing settings
POLYGON_CLOSE_THRESHOLD: int = 10

# Available colors for UI selection
AVAILABLE_COLORS: Dict[str, pygame.Color] = {
    "Black": BLACK,
    "Red": RED,
    "Green": GREEN,
    "Blue": BLUE,
    "Gray": DARK_GRAY,
    "White": WHITE,
}

# Gemini configuration
GEMINI_MODEL_NAME: str = "gemini-2.0-flash-exp"
GEMINI_BUTTON_TEXT: str = "Generate with AI (G)"
PROMPT_INPUT_PLACEHOLDER: str = "Type your idea here and press Enter..."
PROMPT_ACTIVE_PREFIX: str = "AI Prompt: "
GEMINI_STATUS_DEFAULT: str = "AI ready. Draw something and press 'G'."
GEMINI_STATUS_LOADING: str = "AI thinking..."
GEMINI_STATUS_ERROR_API_KEY: str = "Error: Gemini API Key not configured."
GEMINI_STATUS_ERROR_LIB: str = "Error: AI libraries not found."
GEMINI_STATUS_ERROR_GENERAL: str = "AI error. Try again."

# Veo configuration
VEO_BUTTON_TEXT: str = "Video with Veo (V)"
VEO_MODEL_NAME: str = "veo-2.0-generate-001"

# Veo polling times (in milliseconds)
VEO_INITIAL_POLL_DELAY_MS: int = 10000
VEO_POLLING_INTERVAL_MS: int = 15000

# Veo status messages
VEO_STATUS_STARTING: str = "Starting video generation with Veo..."
VEO_STATUS_GENERATING: str = "Veo is generating video (may take minutes)..."
VEO_STATUS_POLLING: str = "Checking Veo generation status..."
VEO_STATUS_SUCCESS: str = "Veo video(s) saved to project directory!"
VEO_STATUS_ERROR_API: str = "Error with Veo API. Check configuration or API Key."
VEO_STATUS_ERROR_NO_PROMPT_OR_IMAGE: str = "Veo needs a prompt or drawing on canvas."
VEO_STATUS_PROCESSING_ANOTHER_OP: str = "AI is already processing a request. Please wait."

# Veo default parameters
VEO_DEFAULT_ASPECT_RATIO: str = "16:9"
VEO_DEFAULT_DURATION_SECONDS: int = 5
VEO_DEFAULT_PERSON_GENERATION: str = "allow_adult"

# Additional UI colors for AI
PROMPT_INPUT_BG_COLOR: pygame.Color = pygame.Color("whitesmoke")
PROMPT_INPUT_TEXT_COLOR: pygame.Color = BLACK
STATUS_MESSAGE_COLOR: pygame.Color = pygame.Color(50, 50, 50)