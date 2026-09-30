"""Búsqueda voraz primero el mejor (Greedy Best-First Search).

Referencia: Russell y Norvig (2021). Artificial Intelligence: A Modern
Approach, 4.ª ed., sección 3.5.1.

Pseudocódigo
------------
1. marcar inicio como visitado; insertarlo en la frontera con prioridad h(inicio)
2. mientras la frontera no esté vacía:
3.     actual = extraer el nodo de menor h (el que PARECE más cercano al destino)
4.     si actual es el destino: devolver la ruta reconstruida
5.     para cada vecino v de actual no visitado:
6.         marcar v como visitado; padre[v] = actual
7.         insertar v en la frontera con prioridad h(v)
8. devolver SIN_RUTA

Propiedades
-----------
- Estrategia voraz: en cada paso toma la decisión localmente mejor según la
  heurística e ignora el costo ya recorrido (g). Suele expandir muy pocos nodos,
  pero NO garantiza la ruta óptima: frente a un muro puede entrar en un callejón
  y rodearlo por el lado largo.
- Tiempo O(E log V) en el peor caso; memoria O(V).
- `g` solo se acumula para informar el costo real de la ruta hallada.
"""

from heapq import heappop, heappush
from itertools import count

from ..domain.movimiento import distancia_octil
from .contrato import NULO, SIN_RUTA, ResultadoBusqueda, reconstruir_ruta


def voraz(grafo, inicio, destino, observador=NULO) -> ResultadoBusqueda:
    h = lambda posicion: distancia_octil(posicion, destino)
    orden = count()

    g = {inicio: 0.0}                                          # 1.
    padre = {}
    frontera = [(h(inicio), next(orden), inicio)]              # (h, orden, nodo)
    observador.frontera(inicio, 0.0, h(inicio), None)

    while frontera:                                            # 2.
        h_actual, _, actual = heappop(frontera)                # 3. menor h
        observador.expandido(actual, g[actual], h_actual, padre.get(actual))

        if actual == destino:                                  # 4.
            return ResultadoBusqueda(reconstruir_ruta(padre, inicio, destino), g[actual])

        for vecino, peso in grafo.vecinos(actual):             # 5.
            if vecino in g:
                continue      # ya visitado
            g[vecino] = g[actual] + peso                       # 6.
            padre[vecino] = actual
            h_vecino = h(vecino)
            heappush(frontera, (h_vecino, next(orden), vecino))     # 7.
            observador.frontera(vecino, g[vecino], h_vecino, actual)

    return SIN_RUTA                                            # 8.
