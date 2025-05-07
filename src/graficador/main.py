# src/graficador/main.py
import pygame
from .app import Application
from dotenv import load_dotenv
import os
import traceback # Importar para mejor logging de errores

def main() -> None:
    """
    Inicializa y ejecuta la aplicación principal.
    Carga variables de entorno desde .env al inicio.
    """
    # --- Cargar variables de entorno desde .env ---
    try:
        # Calcular la ruta raíz del proyecto (asumiendo estructura estándar)
        # __file__ -> src/graficador/main.py
        # dirname -> src/graficador
        # dirname -> src
        # dirname -> raíz del proyecto (graficador_geometrico)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dotenv_path = os.path.join(project_root, '.env')

        print(f"Buscando archivo .env en la raíz del proyecto: {dotenv_path}")

        if os.path.exists(dotenv_path):
            # Cargar explícitamente desde la ruta calculada
            # override=True asegura que estas variables tengan precedencia si ya existieran en el entorno
            loaded = load_dotenv(dotenv_path=dotenv_path, override=True) 
            if loaded:
                print(f"Archivo .env cargado desde la raíz del proyecto: {dotenv_path}")
                # Opcional: Verificar si la variable específica se cargó
                # if os.getenv("GOOGLE_API_KEY"):
                #     print("Variable GOOGLE_API_KEY encontrada en el entorno.")
                # else:
                #     print("ADVERTENCIA: .env cargado, pero GOOGLE_API_KEY no parece estar definida.")
            else:
                 print(f"ADVERTENCIA: Se encontró {dotenv_path}, pero hubo un problema al cargarlo (¿vacío, permisos?).")
        else:
            # Si no se encuentra en la raíz, no intentar cargar desde el directorio actual para evitar confusiones.
            print(f"ADVERTENCIA: Archivo .env NO encontrado en la raíz del proyecto ({dotenv_path}). "
                  "Asegúrate de que exista y contenga la variable GOOGLE_API_KEY.")
            # Puedes decidir si continuar o salir si el .env es estrictamente necesario.
            # return # Descomentar para salir si el .env es obligatorio.

    except Exception as e:
        print(f"ERROR al intentar cargar el archivo .env: {e}")
        # Continuar de todas formas, Application manejará la falta de API key si es necesario

    # --- Fin de la carga de .env ---

    try:
        app = Application()
        app.run()
    except Exception as e:
        print(f"ERROR: Ocurrió un error inesperado en la aplicación: {e}")
        traceback.print_exc() # Imprimir traceback completo
    finally:
        if pygame.get_init():
            print("Cerrando Pygame...")
            pygame.quit()

if __name__ == '__main__':
    main()