import json
import os

HISTORIAL_FILE = "historial_memoria.json"

def main():
    if not os.path.exists(HISTORIAL_FILE):
        print("❌ historial_memoria.json not found.")
        return

    with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
        mem = json.load(f)

    # Initialize sections if missing
    if "descartados_detalle" not in mem:
        mem["descartados_detalle"] = []
    if "ganadores_detalle" not in mem:
        mem["ganadores_detalle"] = []

    # Prepare the winner item details
    winner_item = {
        "tiktok_ingles": "Bell+Howell Screw-In Socket Fan - The Original Remote Controlled Socket Ceiling Fan & Light - 1000 Lumens, 3 Speeds, 2-in-1 LED & Fan, Durable Double-Layer Blades, Wireless Installation",
        "producto_espanol": "Ventilador ampolleta LED",
        "dropi_id": 65391,
        "meta_search_query": "Ventilador ampolleta LED",
        "meta_anuncios_activos": 0,
        "estado_meta": "OCEANO AZUL",
        "ventas_reales_usa": 24641,
        "precio_usd": None,
        "url_tiktok_shop": "https://www.tiktok.com/shop/pdp/1729439168050926319"
    }

    # Avoid duplicate
    if not any(g["tiktok_ingles"] == winner_item["tiktok_ingles"] for g in mem["ganadores_detalle"]):
        mem["ganadores_detalle"].append(winner_item)
        print("Success registered successfully!")
    else:
        print("Product already registered.")

    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
