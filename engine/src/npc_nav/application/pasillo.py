"""Caso de uso: capacidad de un pasillo y sus celdas críticas (Edmonds-Karp).

Se analiza una zona rectangular del mapa. Los NPC entran por un borde y salen
por el opuesto (izquierda → derecha u arriba → abajo) moviéndose con las reglas
octiles del dominio, y dos NPC no pueden ocupar la misma celda.

Red de flujo (división de vértices):

- Cada celda transitable p de la zona es un par de nodos `('e', p) → ('s', p)`
  con capacidad 1: así la capacidad la limitan las celdas, no los movimientos.
- Cada movimiento p → q dentro de la zona es `('s', p) → ('e', q)` con capacidad
  «sin límite» (un número mayor que cualquier corte).
- La fuente alimenta las celdas del borde de entrada y las del borde de salida
  desaguan en el sumidero.

Resultado (teorema de Menger):

- `flujo_maximo`: cuántos NPC pueden cruzar a la vez por caminos sin celdas en común.
- `caminos`: esos caminos, obtenidos al descomponer el flujo.
- `corte`: celdas cuyo bloqueo cierra el paso; siempre son `flujo_maximo` celdas.
"""

from dataclasses import dataclass
from time import perf_counter_ns

from ..algorithms.edmonds_karp import edmonds_karp
from ..domain.mapa import Mapa, Posicion
from ..domain.sesion import SesionNavegacion

LADO_MAXIMO = 64
FUENTE, SUMIDERO = 'fuente', 'sumidero'
DIRECCIONES = ('horizontal', 'vertical')


@dataclass(frozen=True)
class Aumento:
    celdas: tuple[Posicion, ...]
    """Celdas del camino aumentante, en orden (puede deshacer flujo de otro camino)."""
    flujo: int
    """Flujo acumulado después de este aumento."""


@dataclass(frozen=True)
class AnalisisPasillo:
    mapa: str
    zona: tuple[int, int, int, int]
    """(fila0, columna0, fila1, columna1), ambas esquinas incluidas."""
    direccion: str
    entradas: tuple[Posicion, ...]
    salidas: tuple[Posicion, ...]
    celdas: int
    """Celdas transitables de la zona."""
    flujo_maximo: int
    caminos: tuple[tuple[Posicion, ...], ...]
    corte: tuple[Posicion, ...]
    aumentos: tuple[Aumento, ...]
    bloqueadas: tuple[Posicion, ...]
    tiempo_ms: float


class _Aumentos:
    def __init__(self):
        self.aumentos = []

    def paso(self, linea, **datos):
        if linea == 8:
            celdas = tuple(nodo[1] for nodo in datos['camino']
                           if isinstance(nodo, tuple) and nodo[0] == 'e')
            self.aumentos.append(Aumento(celdas, datos['flujo']))


def _validar_zona(mapa: Mapa, zona, direccion: str) -> tuple[int, int, int, int]:
    if direccion not in DIRECCIONES:
        raise ValueError(f'Dirección desconocida: {direccion!r}. Use horizontal o vertical')
    f0, c0, f1, c1 = zona
    f0, f1 = sorted((f0, f1))
    c0, c1 = sorted((c0, c1))
    if not (mapa.contiene((f0, c0)) and mapa.contiene((f1, c1))):
        raise ValueError('La zona debe estar dentro del mapa')
    if f1 - f0 + 1 > LADO_MAXIMO or c1 - c0 + 1 > LADO_MAXIMO:
        raise ValueError(f'La zona no puede pasar de {LADO_MAXIMO} celdas por lado')
    largo = c1 - c0 if direccion == 'horizontal' else f1 - f0
    if largo < 1:
        raise ValueError('La zona necesita al menos dos celdas en la dirección del paso')
    return f0, c0, f1, c1


def analizar_pasillo(mapa: Mapa, zona, direccion: str = 'horizontal',
                     bloqueadas=()) -> AnalisisPasillo:
    f0, c0, f1, c1 = _validar_zona(mapa, zona, direccion)
    sesion = SesionNavegacion(mapa)
    sesion.actualizar_obstaculos(bloquear=(tuple(p) for p in bloqueadas))
    dentro = lambda p: f0 <= p[0] <= f1 and c0 <= p[1] <= c1
    celdas = [(f, c) for f in range(f0, f1 + 1) for c in range(c0, c1 + 1)
              if sesion.transitable((f, c))]
    if direccion == 'horizontal':
        entradas = tuple(p for p in celdas if p[1] == c0)
        salidas = tuple(p for p in celdas if p[1] == c1)
    else:
        entradas = tuple(p for p in celdas if p[0] == f0)
        salidas = tuple(p for p in celdas if p[0] == f1)

    sin_limite = len(celdas) + 1
    red = {FUENTE: {('e', p): sin_limite for p in entradas}}
    for p in celdas:
        red[('e', p)] = {('s', p): 1}
        red[('s', p)] = {('e', q): sin_limite for q, _ in sesion.vecinos(p) if dentro(q)}
    for p in salidas:
        red[('s', p)][SUMIDERO] = sin_limite

    aumentos = _Aumentos()
    reloj = perf_counter_ns()
    resultado = edmonds_karp(red, FUENTE, SUMIDERO, aumentos)
    tiempo_ms = (perf_counter_ns() - reloj) / 1_000_000

    corte = tuple(p for p in celdas
                  if ('e', p) in resultado.lado_fuente and ('s', p) not in resultado.lado_fuente)
    return AnalisisPasillo(
        mapa=mapa.nombre, zona=(f0, c0, f1, c1), direccion=direccion,
        entradas=entradas, salidas=salidas, celdas=len(celdas),
        flujo_maximo=int(resultado.valor), caminos=_descomponer(resultado.flujo),
        corte=corte, aumentos=tuple(aumentos.aumentos),
        bloqueadas=tuple(sorted(sesion.bloqueadas)), tiempo_ms=tiempo_ms,
    )


def _descomponer(flujo: dict) -> tuple[tuple[Posicion, ...], ...]:
    """Convierte el flujo en caminos de celdas: cada unidad que sale de la fuente.

    Cada celda transporta a lo sumo una unidad, así que cada camino es simple y
    los ciclos de flujo que no tocan la fuente se ignoran.
    """
    salientes: dict = {}
    for (u, v), unidades in flujo.items():
        salientes.setdefault(u, []).extend([v] * unidades)
    caminos = []
    while salientes.get(FUENTE):
        nodo, camino = salientes[FUENTE].pop(), []
        while nodo != SUMIDERO:
            if nodo[0] == 'e':
                camino.append(nodo[1])
            nodo = salientes[nodo].pop()
        caminos.append(tuple(camino))
    return tuple(sorted(caminos))
