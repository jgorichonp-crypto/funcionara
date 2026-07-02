import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure document root is in Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from utils.smartcommerce_helper_gt import search_smartcommerce_product, get_smartcommerce_product_by_id

async def test():
    print("Testing search_smartcommerce_product...")
    res = await search_smartcommerce_product("JOIN HEALTH")
    print("Search Result:", res)
    
    if res and res["id"] != "123456":
        print("\nTesting get_smartcommerce_product_by_id...")
        details = await get_smartcommerce_product_by_id(res["id"])
        print("Details:")
        import json
        print(json.dumps(details, indent=2))
    else:
        print("Product not found or returned fallback ID.")

if __name__ == "__main__":
    asyncio.run(test())
