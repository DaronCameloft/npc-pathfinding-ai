"""Rutas HTTP de los algoritmos complementarios: Kruskal, Edmonds-Karp y mochila 0/1.

No son búsquedas origen→destino: cada uno tiene su caso de uso en `application/`
y su propio endpoint. Las posiciones viajan como [fila, columna].
"""

from dataclasses import asdict

from fastapi import APIRouter

from ..algorithms.catalogo import COMPLEMENTARIOS
from ..application.botin import Objeto, elegir_botin
from ..application.pasillo import analizar_pasillo
from ..application.patrullaje import red_de_patrullaje
from ..infrastructure.repositorio import RepositorioDataset
from .esquemas import PeticionBotin, PeticionPasillo, PeticionPatrullaje
from .rutas import Repositorio, _mapa_existente

router = APIRouter()


@router.get('/complementarios')
def complementarios():
    return [{'clave': info.clave, 'nombre': info.nombre, 'tecnica': info.tecnica,
             'complejidad': info.complejidad, 'referencia': info.referencia,
             'caso_de_uso': info.caso_de_uso,
             'pseudocodigo': [asdict(linea) for linea in info.pseudocodigo]}
            for info in COMPLEMENTARIOS.values()]


@router.post('/patrullaje')
def patrullaje(peticion: PeticionPatrullaje, repo: RepositorioDataset = Repositorio):
    """Kruskal sobre los costos A* entre puntos de interés."""
    mapa = repo.mapa(_mapa_existente(repo, peticion.mapa))
    puntos = [tuple(p) for p in peticion.puntos] if peticion.puntos is not None else None
    return asdict(red_de_patrullaje(mapa, puntos, cantidad=peticion.cantidad,
                                    semilla=peticion.semilla))


@router.post('/pasillo')
def pasillo(peticion: PeticionPasillo, repo: RepositorioDataset = Repositorio):
    """Edmonds-Karp: flujo máximo (NPC simultáneos) y corte mínimo (celdas críticas)."""
    mapa = repo.mapa(_mapa_existente(repo, peticion.mapa))
    return asdict(analizar_pasillo(mapa, peticion.zona, peticion.direccion,
                                   [tuple(p) for p in peticion.bloqueadas]))


@router.post('/botin')
def botin(peticion: PeticionBotin):
    """Mochila 0/1 por programación dinámica, con el voraz por densidad como contraste."""
    if peticion.objetos is None:
        return asdict(elegir_botin(capacidad=peticion.capacidad))
    objetos = [Objeto(o.nombre, o.peso, o.valor) for o in peticion.objetos]
    return asdict(elegir_botin(objetos, peticion.capacidad))
