import sys
import os

# Agrega la carpeta root del proyecto al sys.path para que Pytest
# pueda importar schema, config, parsers, extractors etc.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
