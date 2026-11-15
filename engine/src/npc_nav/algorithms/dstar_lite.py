"""D* Lite — búsqueda incremental hacia atrás que reutiliza su trabajo al cambiar el mapa.

Referencia: Koenig y Likhachev (2002). D* Lite. Proceedings of the AAAI
Conference on Artificial Intelligence, 476-483 (versión optimizada, figura 4).

La búsqueda va desde la meta hacia el NPC. `g[s]` y `rhs[s]` estiman el costo de
`s` a la meta: `g` es el valor aceptado y `rhs` el que se deduce de los vecinos
(«lookahead»: rhs[s] = mínimo de w(s, v) + g[v]). Una celda con `g == rhs` es
consistente; las inconsistentes esperan en la cola. Cuando aparece o desaparece
un obstáculo solo se corrigen las celdas afectadas, y la siguiente búsqueda parte
de los valores ya calculados.

Pseudocódigo
------------
 1. km = 0; rhs[meta] = 0; insertar meta en la cola con clave [h(inicio, meta); 0]
 2. clave(s) = [min(g[s], rhs[s]) + h(inicio, s) + km; min(g[s], rhs[s])]
 3. actualizar_vertice(u): quitar u de la cola; si g[u] != rhs[u]: insertar u con clave(u)
 4. calcular_ruta_minima():
 5.     mientras la menor clave < clave(inicio) o rhs[inicio] != g[inicio]:
 6.         u = extraer el nodo de menor clave; k_vieja = su clave
 7.         si k_vieja < clave(u): reinsertar u con clave(u)
 8.         si no, si g[u] > rhs[u]: g[u] = rhs[u]
 9.             para cada vecino v: rhs[v] = min(rhs[v], w(v, u) + g[u]); actualizar_vertice(v)
10.         si no: g_vieja = g[u]; g[u] = infinito; actualizar_vertice(u)
11.             para cada vecino v cuyo rhs venía de u (rhs[v] = w(v, u) + g_vieja):
12.                 rhs[v] = mínimo de w(v, s) + g[s] entre los vecinos s de v; actualizar_vertice(v)
13. al cambiar celdas: km = km + h(inicio_anterior, inicio); inicio_anterior = inicio
14.     para cada celda cambiada y sus 8 vecinas: recalcular rhs (línea 12); actualizar_vertice
15.     calcular_ruta_minima()
16. ruta: desde inicio, avanzar al vecino v de menor w(actual, v) + g[v] hasta la meta

En las líneas 9, 12 y 14 se omite la meta: su rhs siempre es 0.

Propiedades
-----------
- Óptimo: tras `calcular_ruta_minima`, g[inicio] es el costo mínimo al estado
  actual del mapa (heurística octil admisible y consistente).
- Primera búsqueda: O(E log V), equivalente a A* hacia atrás. Las replanificaciones
  solo procesan las celdas cuyo costo cambió, en lugar de recorrer el mapa como A*.
- Versión optimizada: cuando una celda mejora (línea 9), cada vecina se actualiza
  con un mínimo O(1). Solo cuando una celda empeora (líneas 11-12) se recalcula el
  rhs completo, y únicamente en las vecinas que dependían de ella.
- Parada (línea 5): se exige `rhs[inicio] == g[inicio]` (la figura 4 solo pide
  `rhs <= g`). Así el inicio queda consistente aunque esté primero en la cola, y
  seguir el mínimo de w + g (línea 16) recorre solo celdas consistentes.
- `km` evita reordenar la cola cuando el NPC avanza: suma cuánto bajó la
  heurística desde la última corrección.
- Memoria O(V): g, rhs y la cola se conservan entre búsquedas (por eso necesita
  una sesión con estado).
- Las aristas se consultan a `grafo.vecinos`, que ya refleja los obstáculos; la
  grilla es no dirigida, así que vecinos = sucesores = predecesores. Un bloqueo
  cambia las aristas de la celda y las diagonales entre sus vecinas, por eso la
  línea 14 corrige la celda y sus 8 vecinas.
- Aritmética exacta: en la grilla octil todo costo es a + b·raíz(2) con a, b
  enteros. g, rhs y km se guardan como pares (a, b) y la clave se calcula con una
  sola expresión, así dos caminos del mismo costo dan exactamente la misma clave y
  la comparación de la línea 11 es una igualdad exacta. Con sumas de punto
  flotante, un empate podía quedar 1e-14 por encima y la búsqueda se detenía antes
  de corregir una celda (ruta incoherente).
- Cola binaria con borrado perezoso: una entrada vale solo si coincide con la
  clave vigente del nodo. Empates: orden de inserción (determinista).
"""

from collections.abc import Iterable
from heapq import heappop, heappush
from math import inf

from ..domain.mapa import Posicion
from ..domain.movimiento import CARDINALES, COSTO_CARDINAL, COSTO_DIAGONAL, DIAGONALES
from .contrato import NULO, SIN_RUTA, ResultadoBusqueda

_VECINDAD = CARDINALES + DIAGONALES

Costo = tuple[int, int]
"""(a, b) representa a + b·raíz(2): pasos cardinales y diagonales."""
_CERO: Costo = (0, 0)
_INFINITO = (inf, inf)
_CARDINAL: Costo = (1, 0)
_DIAGONAL: Costo = (0, 1)


def _paso(peso: float) -> Costo:
    if peso == COSTO_CARDINAL:
        return _CARDINAL
    if peso == COSTO_DIAGONAL:
        return _DIAGONAL
    raise ValueError(f'D* Lite usa costos exactos de la grilla octil (1 o raíz de 2): {peso}')


def _suma(x: Costo, y: Costo) -> Costo:
    return (x[0] + y[0], x[1] + y[1])


def _valor(x: Costo | None) -> float:
    return inf if x is None else x[0] + x[1] * COSTO_DIAGONAL


def _octil(a: Posicion, b: Posicion) -> Costo:
    """Distancia octil exacta: (max - min) pasos cardinales + min diagonales."""
    df, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
    return (df - dc, dc) if df > dc else (dc - df, df)


class DStarLite:
    """Planificador con estado para un NPC que va de `inicio` a `meta`.

    Uso: `planificar()` una vez; luego `replanificar(posicion, cambiadas)` cada
    vez que cambian obstáculos. Entre cambios, la ruta restante sigue siendo válida.
    """

    def __init__(self, grafo, inicio: Posicion, meta: Posicion):
        self.grafo = grafo
        self.inicio = inicio
        self.meta = meta
        self._ultimo = inicio
        self.km: Costo = _CERO
        self.g: dict[Posicion, Costo] = {}
        self.rhs: dict[Posicion, Costo] = {}
        self._cola: list = []                          # (k1, k2, orden, nodo)
        self._claves: dict[Posicion, tuple[float, float]] = {}
        self._orden = 0                                # desempate por inserción
        self._planificado = False

    # -- consultas -----------------------------------------------------------
    def _h(self, s: Posicion) -> float:
        return _valor(_octil(self.inicio, s))

    def _clave(self, s: Posicion) -> tuple[float, float]:            # 2.
        g, rhs = self.g.get(s), self.rhs.get(s)
        if g is None:
            minimo = rhs
        elif rhs is None:
            minimo = g
        else:
            minimo = g if _valor(g) <= _valor(rhs) else rhs
        if minimo is None:
            return _INFINITO
        h = _octil(self.inicio, s)
        return (_valor((minimo[0] + h[0] + self.km[0], minimo[1] + h[1] + self.km[1])),
                _valor(minimo))

    def _limpiar_tope(self) -> None:
        """Descarta entradas antiguas (borrado perezoso)."""
        while self._cola:
            k1, k2, _, s = self._cola[0]
            if self._claves.get(s) == (k1, k2):
                return
            heappop(self._cola)

    def _mejor_vecino(self, u: Posicion):
        """(vecino, costo exacto) que minimiza w(u, v) + g[v]; (None, None) si no hay."""
        mejor, costo_mejor, valor_mejor = None, None, inf
        for vecino, peso in self.grafo.vecinos(u):
            g = self.g.get(vecino)
            if g is None:
                continue
            costo = _suma(_paso(peso), g)
            valor = _valor(costo)
            if valor < valor_mejor:
                mejor, costo_mejor, valor_mejor = vecino, costo, valor
        return mejor, costo_mejor

    # -- pasos del pseudocódigo ---------------------------------------------
    def _actualizar_vertice(self, u: Posicion, observador, padre=None) -> None:  # 3.
        self._claves.pop(u, None)
        if self.g.get(u) != self.rhs.get(u):
            clave = self._clave(u)
            self._claves[u] = clave
            self._orden += 1
            heappush(self._cola, (clave[0], clave[1], self._orden, u))
            observador.frontera(u, _valor(self.rhs.get(u)), self._h(u), padre, 3)

    def _recalcular_rhs(self, u: Posicion) -> Posicion | None:       # 12.
        """rhs[u] = mínimo de w(u, v) + g[v]; devuelve el vecino que lo da."""
        mejor, rhs = self._mejor_vecino(u)
        if rhs is None:
            self.rhs.pop(u, None)
        else:
            self.rhs[u] = rhs
        return mejor

    def _calcular_ruta_minima(self, observador) -> None:             # 4.
        g, rhs, vecinos, meta = self.g, self.rhs, self.grafo.vecinos, self.meta
        while True:
            self._limpiar_tope()
            tope = (self._cola[0][0], self._cola[0][1]) if self._cola else _INFINITO
            if not (tope < self._clave(self.inicio)                  # 5.
                    or rhs.get(self.inicio) != g.get(self.inicio)):
                return
            if not self._cola:
                return
            k1, k2, _, u = heappop(self._cola)                       # 6.
            del self._claves[u]
            nueva = self._clave(u)
            if (k1, k2) < nueva:                                     # 7.
                self._claves[u] = nueva
                self._orden += 1
                heappush(self._cola, (nueva[0], nueva[1], self._orden, u))
                observador.frontera(u, _valor(rhs.get(u)), self._h(u), None, 7)
                continue
            if _valor(g.get(u)) > _valor(rhs.get(u)):                # 8. sobreconsistente
                g_u = g[u] = rhs[u]
                observador.expandido(u, _valor(g_u), self._h(u), None, 6)
                for v, peso in vecinos(u):                           # 9.
                    if v == meta:
                        continue
                    candidato = _suma(_paso(peso), g_u)
                    actual = rhs.get(v)
                    if actual is None or _valor(candidato) < _valor(actual):
                        rhs[v] = candidato
                        self._actualizar_vertice(v, observador, u)
            else:                                                    # 10. subconsistente
                g_vieja = g.pop(u)
                observador.expandido(u, inf, self._h(u), None, 6)
                self._actualizar_vertice(u, observador)
                for v, peso in vecinos(u):                           # 11.
                    if v != meta and rhs.get(v) == _suma(_paso(peso), g_vieja):
                        mejor = self._recalcular_rhs(v)              # 12.
                        self._actualizar_vertice(v, observador, mejor)

    def ruta(self) -> ResultadoBusqueda:                             # 16.
        """Ruta óptima desde `inicio` según los valores g vigentes."""
        if self.inicio not in self.g:
            return SIN_RUTA
        ruta, actual = [self.inicio], self.inicio
        limite = len(self.g) + 1
        while actual != self.meta:
            actual, _ = self._mejor_vecino(actual)
            if actual is None or len(ruta) > limite:
                raise RuntimeError('D* Lite: valores g incoherentes al extraer la ruta')
            ruta.append(actual)
        return ResultadoBusqueda(tuple(ruta), _valor(self.g[self.inicio]))

    # -- operaciones públicas -------------------------------------------------
    def planificar(self, observador=NULO) -> ResultadoBusqueda:
        """Primera búsqueda completa (líneas 1 y 4)."""
        if self._planificado:
            raise RuntimeError('D* Lite ya planificó; use replanificar()')
        self._planificado = True
        self.rhs[self.meta] = _CERO                                  # 1.
        clave = self._clave(self.meta)
        self._claves[self.meta] = clave
        heappush(self._cola, (clave[0], clave[1], 0, self.meta))
        observador.frontera(self.meta, 0.0, self._h(self.meta), None, 1)
        self._calcular_ruta_minima(observador)
        return self.ruta()

    def replanificar(self, inicio: Posicion, cambiadas: Iterable[Posicion],
                     observador=NULO) -> ResultadoBusqueda:
        """El NPC está en `inicio` y cambiaron las celdas `cambiadas` (líneas 13-15)."""
        if not self._planificado:
            raise RuntimeError('Llame a planificar() antes de replanificar()')
        self.km = _suma(self.km, _octil(self._ultimo, inicio))       # 13.
        self.inicio = self._ultimo = inicio
        afectadas = set()
        for fila, columna in cambiadas:                              # 14.
            afectadas.add((fila, columna))
            afectadas.update((fila + df, columna + dc) for df, dc in _VECINDAD)
        for celda in sorted(afectadas):
            mejor = None if celda == self.meta else self._recalcular_rhs(celda)
            self._actualizar_vertice(celda, observador, mejor)
        self._calcular_ruta_minima(observador)                       # 15.
        return self.ruta()

    def clonar(self) -> 'DStarLite':
        """Copia independiente del estado (comparte el grafo). Sirve para grabar trazas."""
        copia = DStarLite.__new__(DStarLite)
        copia.__dict__.update(self.__dict__)
        copia.g, copia.rhs = dict(self.g), dict(self.rhs)
        copia._cola, copia._claves = list(self._cola), dict(self._claves)
        return copia


def dstar_lite(grafo, inicio, destino, observador=NULO) -> ResultadoBusqueda:
    """Contrato común: una búsqueda sin cambios (la versión con estado es `DStarLite`)."""
    return DStarLite(grafo, inicio, destino).planificar(observador)
