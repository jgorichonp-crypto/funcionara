import sys
import io
import asyncio
import os

# Configurar stdout y stderr para usar UTF-8 y evitar errores de encoding con emojis en Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    # Fallback si reconfigure no está disponible en la versión de Python o entorno
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Asegurar que el path del proyecto esté configurado para ejecutar como script directo
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentes.system import ejecutar_orquestador_agentes

if __name__ == "__main__":
    nicho = None
    if len(sys.argv) > 1:
        nicho = sys.argv[1]
        
    try:
        asyncio.run(ejecutar_orquestador_agentes(nicho))
    except KeyboardInterrupt:
        print("\n⏳ Proceso detenido por el usuario.")
    except Exception as e:
        print(f"\n❌ Error fatal al ejecutar el orquestador: {e}")
