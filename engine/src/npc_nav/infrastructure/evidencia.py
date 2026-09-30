"""Lectura de la evidencia reproducible que deja `npc-nav verificar` en results/<algoritmo>/.

    results/<algoritmo>/resumen.json   resultado global y por mapa, entorno y huellas del código
    results/<algoritmo>/casos.csv      una fila por escenario

La carpeta se toma de la variable de entorno NPC_RESULTS_DIR o, por defecto, de engine/results.
"""

import csv
import json
import os
from pathlib import Path

CARPETA_POR_DEFECTO = Path(__file__).resolve().parents[3] / 'results'

_ENTEROS = ('indice_caso', 'bucket', 'inicio_fila', 'inicio_columna', 'destino_fila',
            'destino_columna', 'pasos_ruta', 'nodos_expandidos', 'nodos_descubiertos',
            'max_frontera')
_REALES = ('costo_referencia', 'costo_obtenido', 'error_absoluto', 'tiempo_ms')


def carpeta_resultados() -> Path:
    return Path(os.environ.get('NPC_RESULTS_DIR', CARPETA_POR_DEFECTO))


class RepositorioEvidencia:
    def __init__(self, carpeta: str | Path | None = None):
        self.carpeta = Path(carpeta) if carpeta else carpeta_resultados()

    def algoritmos(self) -> list[str]:
        """Claves de los algoritmos que tienen un resumen de verificación."""
        if not self.carpeta.is_dir():
            return []
        return sorted(ruta.name for ruta in self.carpeta.iterdir()
                      if (ruta / 'resumen.json').is_file())

    def _archivo(self, clave: str, nombre: str) -> Path:
        ruta = self.carpeta / Path(clave).name / nombre
        if not ruta.is_file():
            raise FileNotFoundError(f'No hay evidencia de verificación para {clave!r}')
        return ruta

    def resumen(self, clave: str) -> dict:
        return json.loads(self._archivo(clave, 'resumen.json').read_text(encoding='utf-8'))

    def casos(self, clave: str) -> list[dict]:
        with self._archivo(clave, 'casos.csv').open(newline='', encoding='utf-8') as archivo:
            filas = list(csv.DictReader(archivo))
        for fila in filas:
            for campo in _ENTEROS:
                fila[campo] = int(fila[campo])
            for campo in _REALES:
                fila[campo] = float(fila[campo]) if fila[campo] != '' else None
        return filas
