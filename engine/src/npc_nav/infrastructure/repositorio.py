"""Acceso al dataset por nombre de mapa, con caché en memoria.

Estructura esperada de la carpeta de datos:

    data/maps/<nombre>.map
    data/scenarios/<nombre>.map.scen

La carpeta se toma de la variable de entorno NPC_DATA_DIR o, por defecto,
de engine/data.
"""

import os
from functools import lru_cache
from pathlib import Path

from ..domain.escenario import Escenario
from ..domain.mapa import Mapa
from .exportadores import sha256
from .movingai import leer_escenarios, leer_mapa

CARPETA_POR_DEFECTO = Path(__file__).resolve().parents[3] / 'data'


def carpeta_datos() -> Path:
    return Path(os.environ.get('NPC_DATA_DIR', CARPETA_POR_DEFECTO))


class RepositorioDataset:
    def __init__(self, carpeta: str | Path | None = None):
        self.carpeta = Path(carpeta) if carpeta else carpeta_datos()

    def ruta_mapa(self, nombre: str) -> Path:
        return self.carpeta / 'maps' / f'{self._normalizar(nombre)}.map'

    def ruta_escenarios(self, nombre: str) -> Path:
        return self.carpeta / 'scenarios' / f'{self._normalizar(nombre)}.map.scen'

    def listar_mapas(self) -> list[str]:
        """Nombres sin extensión, p. ej. ['brc100d', 'brc201d', 'den011d']."""
        return sorted(ruta.stem for ruta in (self.carpeta / 'maps').glob('*.map'))

    def listar_escenarios(self) -> list[str]:
        """Nombres de mapa que tienen archivo .map.scen."""
        return sorted(ruta.name[:-len('.map.scen')]
                      for ruta in (self.carpeta / 'scenarios').glob('*.map.scen'))

    def huellas(self, nombre: str) -> dict[str, str]:
        """SHA-256 del mapa y de sus escenarios, para identificar los datos usados."""
        return {'sha256_mapa': sha256(self.ruta_mapa(nombre)),
                'sha256_escenarios': sha256(self.ruta_escenarios(nombre))}

    def mapa(self, nombre: str) -> Mapa:
        return _leer_mapa_cacheado(self.ruta_mapa(nombre))

    def escenarios(self, nombre: str) -> tuple[Escenario, ...]:
        return _leer_escenarios_cacheado(self.ruta_escenarios(nombre))

    def escenario(self, nombre: str, indice: int) -> Escenario:
        casos = self.escenarios(nombre)
        if not 0 <= indice < len(casos):
            raise ValueError(f'Índice de caso fuera del rango 0..{len(casos) - 1}')
        return casos[indice]

    @staticmethod
    def _normalizar(nombre: str) -> str:
        nombre = Path(nombre).name
        for sufijo in ('.scen', '.map'):
            if nombre.endswith(sufijo):
                nombre = nombre[:-len(sufijo)]
        return nombre


@lru_cache(maxsize=16)
def _leer_mapa_cacheado(ruta: Path) -> Mapa:
    return leer_mapa(ruta)


@lru_cache(maxsize=16)
def _leer_escenarios_cacheado(ruta: Path) -> tuple[Escenario, ...]:
    return leer_escenarios(ruta)
