"""Rutas HTTP del motor: traducen la petición, llaman a `application/` y serializan.

No contienen lógica de búsqueda. Las posiciones viajan como [fila, columna].
"""

from dataclasses import asdict
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import __version__
from ..algorithms.catalogo import ALGORITMOS
from ..infrastructure.repositorio import RepositorioDataset

router = APIRouter()


@lru_cache(maxsize=1)
def obtener_repositorio() -> RepositorioDataset:
    """Un único repositorio para todo el proceso: comparte su caché de mapas."""
    return RepositorioDataset()


Repositorio = Depends(obtener_repositorio)


@router.get('/health')
def health():
    return {'estado': 'ok', 'version': __version__}


@router.get('/algoritmos')
def algoritmos():
    return [{'clave': info.clave, 'nombre': info.nombre,
             'garantiza_optimo': info.garantiza_optimo, 'tecnica': info.tecnica,
             'complejidad': info.complejidad, 'referencia': info.referencia}
            for info in ALGORITMOS.values()]
