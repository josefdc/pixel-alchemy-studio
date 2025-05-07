"""
src/graficador/main.py
Punto de entrada principal para la aplicación Graficador Geométrico.

Este script inicializa y ejecuta la clase principal de la aplicación (`Application`).
También asegura que Pygame se cierre correctamente al finalizar o en caso de error.
"""
import pygame
from .app import Application

def main() -> None:
    """
    Inicializa y ejecuta la aplicación principal.

    Crea una instancia de la clase `Application` y llama a su método `run()`.
    Incluye manejo de excepciones básico y asegura la limpieza de Pygame
    en un bloque `finally`.
    """
    try:
        app = Application()
        app.run()
    except Exception as e:
        print(f"ERROR: Ocurrió un error inesperado en la aplicación: {e}")
        # Considerar logging más robusto para producción
    finally:
        # Asegura que Pygame se cierre correctamente al salir del bucle principal
        # o si ocurre una excepción.
        if pygame.get_init():
            print("Cerrando Pygame...") # Mensaje de cierre
            pygame.quit()

# Llama directamente a la función main para iniciar la aplicación.
# Esto es adecuado para cuando el script se ejecuta como módulo principal
# (por ejemplo, usando `python -m graficador`).
main()