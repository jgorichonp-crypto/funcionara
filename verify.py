"""
Script de verificación rápida del sistema.
Valida que todas las dependencias y módulos estén correctamente instalados.
"""
import sys
import importlib


def check_python_version():
    """Verifica que la versión de Python sea 3.11+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python {version.major}.{version.minor} detectado. Se requiere Python 3.11+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True


def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    required = [
        "pydantic",
        "pydantic_settings",
        "aiohttp",
        "dotenv"
    ]
    
    all_ok = True
    for package in required:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - Instalado")
        except ImportError:
            print(f"❌ {package} - NO INSTALADO")
            all_ok = False
    
    return all_ok


def check_modules():
    """Verifica que todos los módulos del proyecto estén accesibles"""
    modules = [
        "config",
        "models",
        "agents.scout",
        "agents.creative",
        "agents.devops",
        "agents.media_buyer"
    ]
    
    all_ok = True
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module} - OK")
        except ImportError as e:
            print(f"❌ {module} - ERROR: {e}")
            all_ok = False
    
    return all_ok


def main():
    print("="*60)
    print("🔍 VERIFICACIÓN DEL SISTEMA DE DROPSHIPPING")
    print("="*60)
    print()
    
    print("1. Verificando versión de Python...")
    python_ok = check_python_version()
    print()
    
    print("2. Verificando dependencias...")
    deps_ok = check_dependencies()
    print()
    
    print("3. Verificando módulos del proyecto...")
    modules_ok = check_modules()
    print()
    
    print("="*60)
    if python_ok and deps_ok and modules_ok:
        print("✅ SISTEMA LISTO PARA EJECUTAR")
        print("="*60)
        print()
        print("Ejecuta: python main.py")
        return 0
    else:
        print("❌ SISTEMA CON ERRORES")
        print("="*60)
        print()
        print("Soluciones:")
        if not python_ok:
            print("  - Instala Python 3.11 o superior")
        if not deps_ok:
            print("  - Ejecuta: pip install -r requirements.txt")
        if not modules_ok:
            print("  - Verifica que todos los archivos estén en su lugar")
        return 1


if __name__ == "__main__":
    sys.exit(main())
