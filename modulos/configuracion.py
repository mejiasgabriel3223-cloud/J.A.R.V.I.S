import json
from pathlib import Path


def cargar_configuracion():
    ruta = Path(__file__).resolve().parent.parent / "config.json"
    try:
        with ruta.open(encoding="utf-8") as archivo:
            configuracion = json.load(archivo)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"No se pudo cargar la configuración desde {ruta}: {error}") from error

    if not isinstance(configuracion, dict):
        raise ValueError(f"La configuración en {ruta} debe ser un objeto JSON.")

    return configuracion
