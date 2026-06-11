import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import logging
from config import settings
from google import genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestImagen4")

async def test_imagen4():
    api_key = settings.gemini_api_key
    logger.info(f"Using API Key: {api_key[:10]}...")
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt="A professional photo of a glowing galaxy projector on a nightstand, 8k, e-commerce",
            config=dict(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="1:1"
            )
        )
        logger.info(f"✅ Image generation success: {len(response.generated_images)} images.")
        
        # Save image
        os.makedirs("generated_assets", exist_ok=True)
        img_path = "generated_assets/test_galaxy.jpg"
        with open(img_path, "wb") as f:
            f.write(response.generated_images[0].image.image_bytes)
        logger.info(f"💾 Image saved at {img_path}")
        
    except Exception as e:
        logger.error(f"❌ Image generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_imagen4())
