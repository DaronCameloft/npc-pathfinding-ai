"""BFS — búsqueda en anchura (recorrido básico del grafo).

Referencia: Cormen, Leiserson, Rivest y Stein (2009). Introduction to
Algorithms, 3.ª ed., sección 22.2.

Pseudocódigo
------------
1. marcar inicio como visitado; encolar inicio
2. mientras la cola no esté vacía:
3.     actual = desencolar (el más antiguo, FIFO)
4.     si actual es el destino: devolver la ruta reconstruida
5.     para cada vecino v de actual no visitado:
6.         marcar v como visitado; padre[v] = actual
7.         encolar v
8. devolver SIN_RUTA

Propiedades
-----------
- Minimiza el número de PASOS, no el costo: ignora que una diagonal pesa
  raíz de 2. En este grafo ponderado su ruta puede costar más que la óptima.
  Sirve como línea base para mostrar por qué hacen falta los pesos.
- Tiempo O(V + E); memoria O(V).
- `g` acumula el costo real del camino encontrado solo para informarlo; no
  interviene en el orden de exploración.
"""

from collections import deque

from .contrato import NULO, SIN_RUTA, ResultadoBusqueda, reconstruir_ruta


def bfs(grafo, inicio, destino, observador=NULO) -> ResultadoBusqueda:
    g = {inicio: 0.0}                                          # 1.
    padre = {}
    cola = deque([inicio])
    observador.frontera(inicio, 0.0, 0.0, None, 1)

    while cola:                                                # 2.
        actual = cola.popleft()                                # 3. FIFO
        observador.expandido(actual, g[actual], 0.0, padre.get(actual), 3)

        if actual == destino:                                  # 4.
            return ResultadoBusqueda(reconstruir_ruta(padre, inicio, destino), g[actual])

        for vecino, peso in grafo.vecinos(actual):             # 5.
            if vecino in g:
                continue      # ya visitado
            g[vecino] = g[actual] + peso                       # 6.
            padre[vecino] = actual
            cola.append(vecino)                                # 7.
            observador.frontera(vecino, g[vecino], 0.0, actual, 7)

    return SIN_RUTA                                            # 8.
