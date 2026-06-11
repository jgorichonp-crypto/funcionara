import asyncio
import logging
from config import settings
from agents import run_scout_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def test_scout():
    try:
        state = await run_scout_agent("CL")
        print("\n\n--- RUN COMPLETED ---")
        print(f"Ganador: {state.product_name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_scout())
