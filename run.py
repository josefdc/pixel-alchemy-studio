#!/usr/bin/env python3
"""
Script de entrada para ejecutar el Graficador Geométrico.
Permite ejecutar la aplicación sin problemas de imports relativos.
"""
import sys
import os

# Añadir la carpeta src al path de Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importar y ejecutar la aplicación
from graficador.main import main

if __name__ == "__main__":
    main()
