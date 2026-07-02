import os
import sys
import logging

# Añadir el directorio padre al path de búsqueda de Python para importar config, utils, etc.
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger("AgenteOrquestador")

# Ruta del archivo de memoria en el directorio raíz del proyecto
HISTORIAL_FILE = os.path.join(PARENT_DIR, "historial_memoria.json")
