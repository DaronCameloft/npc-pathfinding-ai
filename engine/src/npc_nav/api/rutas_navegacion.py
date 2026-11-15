"""Rutas HTTP de la navegación dinámica: obstáculos en tiempo real y A* frente a D* Lite.

- `POST /simular`: recorrido completo y sin estado (mismo resultado siempre). Es
  lo que usa el dashboard; no depende de que el servidor conserve nada.
- `/sesiones`: navegación con estado para clientes en tiempo real (Unity). El
  cliente mueve al NPC y cambia obstáculos; D* Lite conserva su estado entre
  llamadas. Ver `sesiones.py` sobre su duración.
"""

from dataclasses import asdict
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from ..application import CambioProgramado, NavegacionDinamica, simular_navegacion
from ..infrastructure.repositorio import RepositorioDataset
from .esquemas import PeticionAvanzar, PeticionObstaculos, PeticionSesion, PeticionSimular
from .rutas import Repositorio, _algoritmo_existente, _mapa_existente
from .sesiones import RegistroSesiones, SesionAbierta

router = APIRouter()


@lru_cache(maxsize=1)
def obtener_registro() -> RegistroSesiones:
    return RegistroSesiones()


Registro = Depends(obtener_registro)


def _extremos(peticion: PeticionSesion, repo: RepositorioDataset):
    nombre = _mapa_existente(repo, peticion.mapa)
    for clave in peticion.algoritmos:
        _algoritmo_existente(clave)
    if peticion.caso is not None:
        caso = repo.escenario(nombre, peticion.caso)
        return nombre, caso.inicio, caso.destino
    return nombre, tuple(peticion.inicio), tuple(peticion.destino)


def _estado(sesion: SesionAbierta, nuevas=()) -> dict:
    nav = sesion.navegacion
    return {
        'id': sesion.id, 'mapa': sesion.mapa, 'algoritmos': list(nav.algoritmos),
        'guia': nav.guia, 'inicio': nav.inicio, 'destino': nav.destino,
        'posicion': nav.posicion, 'llegado': nav.llegado,
        'distancia_recorrida': nav.distancia_recorrida, 'recorrido': nav.recorrido,
        'bloqueadas': sorted(nav.sesion.bloqueadas), 'version_mapa': nav.sesion.version,
        'ruta_restante': nav.ruta_restante(),
        'vigentes': {clave: asdict(plan) for clave, plan in nav.vigentes.items()},
        'nuevas': [asdict(plan) for plan in nuevas],
    }


def _sesion(registro: RegistroSesiones, id: str) -> SesionAbierta:
    sesion = registro.obtener(id)
    if sesion is None:
        raise HTTPException(404, f'Sesión inexistente o expirada: {id!r}. Cree otra con POST /sesiones')
    return sesion


@router.post('/simular')
def simular(peticion: PeticionSimular, repo: RepositorioDataset = Repositorio):
    nombre, inicio, destino = _extremos(peticion, repo)
    cambios = [CambioProgramado(c.paso, tuple(map(tuple, c.bloquear)), tuple(map(tuple, c.liberar)))
               for c in peticion.cambios]
    resultado = simular_navegacion(repo.mapa(nombre), inicio, destino, cambios,
                                   algoritmos=peticion.algoritmos,
                                   bloqueadas=map(tuple, peticion.bloqueadas),
                                   con_traza=peticion.traza)
    return {'mapa': nombre, **asdict(resultado)}


@router.post('/sesiones', status_code=201)
def abrir_sesion(peticion: PeticionSesion, repo: RepositorioDataset = Repositorio,
                 registro: RegistroSesiones = Registro):
    nombre, inicio, destino = _extremos(peticion, repo)
    navegacion = NavegacionDinamica(repo.mapa(nombre), inicio, destino,
                                    algoritmos=peticion.algoritmos,
                                    bloqueadas=map(tuple, peticion.bloqueadas),
                                    con_traza=peticion.traza)
    with registro.candado:
        sesion = registro.abrir(nombre, navegacion)
        return _estado(sesion, navegacion.historial)


@router.get('/sesiones/{id}')
def ver_sesion(id: str, registro: RegistroSesiones = Registro):
    with registro.candado:
        return _estado(_sesion(registro, id))


@router.post('/sesiones/{id}/avanzar')
def avanzar(id: str, peticion: PeticionAvanzar, registro: RegistroSesiones = Registro):
    with registro.candado:
        sesion = _sesion(registro, id)
        sesion.navegacion.avanzar(peticion.pasos)
        return _estado(sesion)


@router.post('/sesiones/{id}/obstaculos')
def cambiar_obstaculos(id: str, peticion: PeticionObstaculos,
                       registro: RegistroSesiones = Registro):
    with registro.candado:
        sesion = _sesion(registro, id)
        nuevas = sesion.navegacion.cambiar_obstaculos(
            bloquear=map(tuple, peticion.bloquear), liberar=map(tuple, peticion.liberar),
            con_traza=peticion.traza)
        return _estado(sesion, nuevas)


@router.delete('/sesiones/{id}', status_code=204)
def cerrar_sesion(id: str, registro: RegistroSesiones = Registro):
    with registro.candado:
        if not registro.cerrar(id):
            raise HTTPException(404, f'Sesión inexistente o expirada: {id!r}')
