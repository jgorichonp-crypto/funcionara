import json
import os

def analyze():
    filepath = "historial_memoria.json"
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return
        
    print("=== Analyzing historial_memoria.json ===")
    for key, val in data.items():
        if isinstance(val, list):
            print(f"Key: '{key}' - Type: list - Length: {len(val)} - Approx Str Size: {len(str(val))}")
            if len(val) > 0:
                print(f"  Sample item size: {len(str(val[0]))}")
        else:
            print(f"Key: '{key}' - Type: {type(val).__name__} - Approx Str Size: {len(str(val))}")

if __name__ == "__main__":
    analyze()
