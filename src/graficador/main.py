# src/graficador/main.py
import pygame
from .app import Application
from dotenv import load_dotenv
import os
import traceback

def main() -> None:
    """
    Initialize and run the main application.
    Loads environment variables from .env file at startup.
    """
    try:
        # Calculate project root path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dotenv_path = os.path.join(project_root, '.env')

        print(f"Looking for .env file in project root: {dotenv_path}")

        if os.path.exists(dotenv_path):
            loaded = load_dotenv(dotenv_path=dotenv_path, override=True) 
            if loaded:
                print(f".env file loaded from project root: {dotenv_path}")
            else:
                 print(f"WARNING: Found {dotenv_path}, but there was a problem loading it (empty, permissions?).")
        else:
            print(f"WARNING: .env file NOT found in project root ({dotenv_path}). "
                  "Make sure it exists and contains the GOOGLE_API_KEY variable.")

    except Exception as e:
        print(f"ERROR when trying to load .env file: {e}")

    try:
        app = Application()
        app.run()
    except Exception as e:
        print(f"ERROR: An unexpected error occurred in the application: {e}")
        traceback.print_exc()
    finally:
        if pygame.get_init():
            print("Closing Pygame...")
            pygame.quit()

if __name__ == '__main__':
    main()