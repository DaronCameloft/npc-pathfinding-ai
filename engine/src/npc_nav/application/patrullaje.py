"""Caso de uso: red de patrullaje entre puntos de interés (Kruskal).

Un NPC guardián debe poder ir de cualquier punto de interés a cualquier otro
usando solo caminos de la red. La red más corta que los conecta a todos es el
árbol de expansión mínima del grafo completo de puntos, donde el peso de cada
par es su costo óptimo en el mapa.

1. Se eligen los puntos (los da el cliente o se sortean con semilla en la
   región conectada más grande, separados entre sí).
2. A* calcula el costo óptimo y la ruta de cada par de puntos: son las aristas
   candidatas. Un par sin ruta no genera arista.
3. Kruskal elige las aristas del árbol; si algún punto no se alcanza, el
   resultado es un bosque.

Medición: `tiempo_rutas_ms` (las búsquedas A*) y `tiempo_kruskal_ms` (solo el
algoritmo, con un observador que graba sus decisiones, que son pocas).
"""

from dataclasses import dataclass
from itertools import combinations
from random import Random
from time import perf_counter_ns

from ..algorithms.astar import astar
from ..algorithms.kruskal import kruskal
from ..algorithms.ufds import regiones_conectadas
from ..domain.mapa import Mapa, Posicion
from ..domain.movimiento import distancia_octil
from ..domain.sesion import SesionNavegacion
from .analisis import construir_grafo

MIN_PUNTOS = 2
MAX_PUNTOS = 10


@dataclass(frozen=True)
class Tramo:
    desde: int
    """Índice del punto en `puntos`."""
    hasta: int
    costo: float
    ruta: tuple[Posicion, ...]


@dataclass(frozen=True)
class DecisionKruskal:
    desde: int
    hasta: int
    costo: float
    aceptada: bool
    linea: int
    """Línea del pseudocódigo de Kruskal (5 = entra al árbol, 7 = cerraría un ciclo)."""


@dataclass(frozen=True)
class RedPatrullaje:
    mapa: str
    puntos: tuple[Posicion, ...]
    candidatas: tuple[Tramo, ...]
    """Todos los pares con ruta, de menor a mayor costo (el orden de Kruskal)."""
    sin_ruta: tuple[tuple[int, int], ...]
    decisiones: tuple[DecisionKruskal, ...]
    arbol: tuple[Tramo, ...]
    costo_arbol: float
    costo_candidatas: float
    """Suma de todas las candidatas: lo que costaría unir cada par directamente."""
    componentes: int
    tiempo_rutas_ms: float
    tiempo_kruskal_ms: float


class _Decisiones:
    def __init__(self):
        self.pasos = []

    def paso(self, linea, **datos):
        self.pasos.append((linea, datos))


def puntos_de_interes(mapa: Mapa, cantidad: int, semilla: int = 2026) -> tuple[Posicion, ...]:
    """Sortea `cantidad` celdas de la región más grande, lo más separadas posible.

    Determinista: la misma semilla da los mismos puntos.
    """
    if not MIN_PUNTOS <= cantidad <= MAX_PUNTOS:
        raise ValueError(f'La cantidad de puntos debe estar entre {MIN_PUNTOS} y {MAX_PUNTOS}')
    grafo = construir_grafo(mapa)
    ufds, _ = regiones_conectadas(grafo)
    raiz = max(grafo, key=lambda celda: ufds.tamano[ufds.encontrar(celda)])
    region = sorted(celda for celda in grafo if ufds.mismo_conjunto(celda, raiz))
    if len(region) < cantidad:
        raise ValueError('El mapa no tiene suficientes celdas conectadas')
    candidatos = Random(semilla).sample(region, min(len(region), 400))
    separacion = max(mapa.alto, mapa.ancho) / cantidad ** 0.5
    while True:
        elegidos = []
        for celda in candidatos:
            if all(distancia_octil(celda, otro) >= separacion for otro in elegidos):
                elegidos.append(celda)
                if len(elegidos) == cantidad:
                    return tuple(elegidos)
        separacion *= 0.8


def red_de_patrullaje(mapa: Mapa, puntos: list[Posicion] | None = None, *,
                      cantidad: int = 7, semilla: int = 2026) -> RedPatrullaje:
    sesion = SesionNavegacion(mapa)
    puntos = (tuple(map(tuple, puntos)) if puntos is not None              # 1.
              else puntos_de_interes(mapa, cantidad, semilla))
    if not MIN_PUNTOS <= len(puntos) <= MAX_PUNTOS:
        raise ValueError(f'Indique entre {MIN_PUNTOS} y {MAX_PUNTOS} puntos de interés')
    if len(set(puntos)) != len(puntos):
        raise ValueError('Los puntos de interés no pueden repetirse')
    for punto in puntos:
        if not sesion.transitable(punto):
            raise ValueError(f'Punto de interés no transitable: {punto}')

    reloj = perf_counter_ns()                                              # 2.
    candidatas, sin_ruta = [], []
    for i, j in combinations(range(len(puntos)), 2):
        resultado = astar(sesion, puntos[i], puntos[j])
        if resultado.encontrada:
            candidatas.append(Tramo(i, j, resultado.costo, resultado.ruta))
        else:
            sin_ruta.append((i, j))
    tiempo_rutas = (perf_counter_ns() - reloj) / 1_000_000

    por_par = {(t.desde, t.hasta): t for t in candidatas}                  # 3.
    decisiones = _Decisiones()
    reloj = perf_counter_ns()
    resultado = kruskal(range(len(puntos)),
                        [(t.desde, t.hasta, t.costo) for t in candidatas], decisiones)
    tiempo_kruskal = (perf_counter_ns() - reloj) / 1_000_000

    return RedPatrullaje(
        mapa=mapa.nombre, puntos=puntos,
        candidatas=tuple(sorted(candidatas, key=lambda t: t.costo)),
        sin_ruta=tuple(sin_ruta),
        decisiones=tuple(DecisionKruskal(d['u'], d['v'], d['peso'], d['aceptada'], linea)
                         for linea, d in decisiones.pasos),
        arbol=tuple(por_par[(u, v)] for u, v, _ in resultado.arbol),
        costo_arbol=resultado.costo,
        costo_candidatas=sum(t.costo for t in candidatas),
        componentes=resultado.componentes,
        tiempo_rutas_ms=tiempo_rutas, tiempo_kruskal_ms=tiempo_kruskal,
    )
