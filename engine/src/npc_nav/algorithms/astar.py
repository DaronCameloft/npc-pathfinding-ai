"""A* — búsqueda informada con heurística octil.

Referencia: Hart, Nilsson y Raphael (1968). A formal basis for the heuristic
determination of minimum cost paths. IEEE TSSC 4(2), 100-107.

Pseudocódigo
------------
 1. g[inicio] = 0; insertar inicio en la frontera con f = h(inicio)
 2. mientras la frontera no esté vacía:
 3.     actual = extraer el nodo de menor f = g + h
 4.     si actual es el destino: devolver la ruta reconstruida
 5.     marcar actual como cerrado
 6.     para cada vecino v de actual con peso w:
 7.         si g[actual] + w < g[v]:
 8.             g[v] = g[actual] + w; padre[v] = actual
 9.             insertar v en la frontera con f = g[v] + h(v)
10. devolver SIN_RUTA

Propiedades
-----------
- Óptimo: la distancia octil nunca sobreestima el costo real (admisible) y
  cumple h(u) <= w(u, v) + h(v) (consistente), así que un nodo cerrado no se
  reabre.
- Tiempo O(E log V) con cola binaria; en esta grilla E <= 8V, es decir O(V log V).
- Memoria O(V).
- Empates de f: se prefiere menor h (el más cercano al destino) y luego el orden
  de inserción, para que la búsqueda sea determinista.
"""

from heapq import heappop, heappush
from itertools import count
from math import inf

from ..domain.movimiento import distancia_octil
from .contrato import NULO, SIN_RUTA, ResultadoBusqueda, reconstruir_ruta


def astar(grafo, inicio, destino, observador=NULO) -> ResultadoBusqueda:
    h = lambda posicion: distancia_octil(posicion, destino)
    orden = count()

    # 1. el inicio entra a la frontera con g = 0
    g = {inicio: 0.0}
    padre = {}
    cerrados = set()
    frontera = [(h(inicio), h(inicio), next(orden), inicio)]   # (f, h, orden, nodo)
    observador.frontera(inicio, 0.0, h(inicio), None)

    while frontera:                                            # 2.
        _, h_actual, _, actual = heappop(frontera)             # 3. menor f
        if actual in cerrados:
            continue          # copia antigua en la cola: ya se procesó con mejor g
        observador.expandido(actual, g[actual], h_actual, padre.get(actual))

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
                h_vecino = h(vecino)
                heappush(frontera, (nuevo_g + h_vecino, h_vecino, next(orden), vecino))  # 9.
                observador.frontera(vecino, nuevo_g, h_vecino, actual)

    return SIN_RUTA                                            # 10.
