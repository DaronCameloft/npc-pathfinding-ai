"""Escritura de evidencia: JSON, CSV y huellas SHA-256."""

import csv
import hashlib
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path


def a_dict(objeto):
    return asdict(objeto) if is_dataclass(objeto) else objeto


def guardar_json(ruta: str | Path, contenido) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(a_dict(contenido), ensure_ascii=False, indent=2, allow_nan=False)
    ruta.write_text(texto + '\n', encoding='utf-8')
    return ruta


def guardar_csv(ruta: str | Path, filas: list[dict]) -> Path:
    if not filas:
        raise ValueError('No hay filas para exportar')
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open('w', newline='', encoding='utf-8') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    return ruta


def sha256(ruta: str | Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()
