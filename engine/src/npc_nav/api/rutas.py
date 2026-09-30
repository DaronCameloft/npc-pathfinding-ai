"""Rutas HTTP del motor: traducen la petición, llaman a `application/` y serializan.

No contienen lógica de búsqueda. Las posiciones viajan como [fila, columna].
"""

from dataclasses import asdict
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import __version__
from ..algorithms.catalogo import ALGORITMOS
from ..application import comparar_algoritmos, ejecutar_busqueda
from ..domain.sesion import SesionNavegacion
from ..infrastructure.repositorio import RepositorioDataset
from .esquemas import ConsultaBase, PeticionBuscar, PeticionComparar

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


def _mapa_existente(repo: RepositorioDataset, nombre: str) -> str:
    if nombre not in repo.listar_mapas():
        raise HTTPException(404, f'Mapa inexistente: {nombre!r}. Disponibles: '
                                 f'{", ".join(repo.listar_mapas())}')
    return nombre


def _algoritmo_existente(clave: str) -> str:
    if clave not in ALGORITMOS:
        raise HTTPException(404, f'Algoritmo inexistente: {clave!r}. Disponibles: '
                                 f'{", ".join(ALGORITMOS)}')
    return clave


@lru_cache(maxsize=None)
def _vertices(repo: RepositorioDataset, nombre: str) -> int:
    return sum(1 for _ in repo.mapa(nombre).posiciones_transitables())


@router.get('/mapas')
def mapas(repo: RepositorioDataset = Repositorio):
    resultado = []
    for nombre in repo.listar_mapas():
        mapa = repo.mapa(nombre)
        resultado.append({'nombre': nombre, 'alto': mapa.alto, 'ancho': mapa.ancho,
                          'vertices': _vertices(repo, nombre),
                          'escenarios': len(repo.escenarios(nombre))})
    return resultado


@router.get('/mapas/{nombre}')
def mapa(nombre: str, repo: RepositorioDataset = Repositorio):
    datos = repo.mapa(_mapa_existente(repo, nombre))
    return {'nombre': nombre, 'alto': datos.alto, 'ancho': datos.ancho,
            'filas': list(datos.celdas)}


@router.get('/mapas/{nombre}/escenarios')
def escenarios(nombre: str, desde: int = Query(0, ge=0), limite: int = Query(100, ge=1, le=1000),
               repo: RepositorioDataset = Repositorio):
    casos = repo.escenarios(_mapa_existente(repo, nombre))
    return {'mapa': nombre, 'total': len(casos), 'desde': desde, 'limite': limite,
            'escenarios': [{'indice': indice, 'bucket': caso.bucket,
                            'inicio': caso.inicio, 'destino': caso.destino,
                            'optimo': caso.optimo}
                           for indice, caso in enumerate(casos[desde:desde + limite],
                                                         start=desde)]}


def _preparar(peticion: ConsultaBase, repo: RepositorioDataset):
    """Sesión nueva por petición (la API no guarda estado) y extremos de la consulta."""
    nombre = _mapa_existente(repo, peticion.mapa)
    if peticion.caso is not None:
        caso = repo.escenario(nombre, peticion.caso)
        inicio, destino = caso.inicio, caso.destino
    else:
        inicio, destino = peticion.inicio, peticion.destino
    sesion = SesionNavegacion(repo.mapa(nombre))
    if peticion.bloqueadas:
        sesion.actualizar_obstaculos(bloquear=peticion.bloqueadas)
    return sesion, inicio, destino


@router.post('/buscar')
def buscar(peticion: PeticionBuscar, repo: RepositorioDataset = Repositorio):
    _algoritmo_existente(peticion.algoritmo)
    sesion, inicio, destino = _preparar(peticion, repo)
    return asdict(ejecutar_busqueda(sesion, peticion.algoritmo, inicio, destino,
                                    con_traza=peticion.traza))


@router.post('/comparar')
def comparar(peticion: PeticionComparar, repo: RepositorioDataset = Repositorio):
    claves = [_algoritmo_existente(clave) for clave in peticion.algoritmos] or list(ALGORITMOS)
    sesion, inicio, destino = _preparar(peticion, repo)
    return [asdict(e) for e in comparar_algoritmos(sesion, claves, inicio, destino,
                                                   con_traza=peticion.traza)]
