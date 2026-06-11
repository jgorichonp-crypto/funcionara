import sys
import os
import asyncio
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Añadir directorio raíz a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.scout import run_scout_agent

async def test():
    # Asegurar codificación utf-8 en Windows
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
            
    try:
        state = await run_scout_agent(target_country="CL")
        print("\n=== PRUEBA COMPLETADA CON ÉXITO ===")
        print(f"Producto Ganador: {state.product_name}")
        print(f"Costo Sugerido: ${state.target_cost}")
        print(f"Precio Sugerido: ${state.suggested_price}")
        print(f"Margen: {state.profit_margin:.2f}X")
        print(f"Etapa del Pipeline: {state.pipeline_stage}")
    except Exception as e:
        print(f"\n❌ Error al ejecutar el scout: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
