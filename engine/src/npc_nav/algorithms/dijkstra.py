"""Dijkstra — camino de costo mínimo sin heurística.

Referencia: Dijkstra, E. W. (1959). A note on two problems in connexion with
graphs. Numerische Mathematik 1, 269-271.

Pseudocódigo
------------
 1. g[inicio] = 0; insertar inicio en la frontera con prioridad 0
 2. mientras la frontera no esté vacía:
 3.     actual = extraer el nodo de menor g
 4.     si actual es el destino: devolver la ruta reconstruida
 5.     marcar actual como cerrado
 6.     para cada vecino v de actual con peso w:
 7.         si g[actual] + w < g[v]:
 8.             g[v] = g[actual] + w; padre[v] = actual
 9.             insertar v en la frontera con prioridad g[v]
10. devolver SIN_RUTA

Propiedades
-----------
- Óptimo con pesos no negativos.
- Es A* con h = 0: explora en "círculos" de costo creciente alrededor del
  inicio, sin dirigirse al destino. Por eso expande muchos más nodos que A*.
- Tiempo O(E log V); memoria O(V).
"""

from heapq import heappop, heappush
from itertools import count
from math import inf

from .contrato import NULO, SIN_RUTA, ResultadoBusqueda, reconstruir_ruta


def dijkstra(grafo, inicio, destino, observador=NULO) -> ResultadoBusqueda:
    orden = count()

    g = {inicio: 0.0}                                          # 1.
    padre = {}
    cerrados = set()
    frontera = [(0.0, next(orden), inicio)]                    # (g, orden, nodo)
    observador.frontera(inicio, 0.0, 0.0, None, 1)

    while frontera:                                            # 2.
        _, _, actual = heappop(frontera)                       # 3. menor g
        if actual in cerrados:
            continue          # copia antigua en la cola
        observador.expandido(actual, g[actual], 0.0, padre.get(actual), 3)

        if actual == destino:                                  # 4.
            return ResultadoBusqueda(reconstruir_ruta(padre, inicio, destino), g[actual])
        cerrados.add(actual)                                   # 5.

        for vecino, peso in grafo.vecinos(actual):             # 6.
            if vecino in cerrados:
                continue
            nuevo_g = g[actual] + peso
            if nuevo_g < g.get(vecino, inf):                   # 7. relajación
                g[vecino] = nuevo_g                            # 8.
                padre[vecino] = actual
                heappush(frontera, (nuevo_g, next(orden), vecino))   # 9.
                observador.frontera(vecino, nuevo_g, 0.0, actual, 9)

    return SIN_RUTA                                            # 10.
