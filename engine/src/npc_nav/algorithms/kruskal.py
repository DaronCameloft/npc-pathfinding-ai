"""Kruskal — árbol de expansión mínima con UFDS.

Referencia: Kruskal, J. B. (1956). On the shortest spanning subtree of a graph
and the traveling salesman problem. Proceedings of the American Mathematical
Society 7(1), 48-50.

Pseudocódigo
------------
 1. ordenar las aristas por peso, de menor a mayor
 2. crear un conjunto UFDS por cada vértice
 3. para cada arista (u, v, w) en ese orden:
 4.     si encontrar(u) != encontrar(v):
 5.         agregar (u, v, w) al árbol y unir(u, v)
 6.     si no:
 7.         descartarla: cerraría un ciclo
 8.     si el árbol ya tiene V - 1 aristas: terminar
 9. devolver el árbol (un bosque si el grafo no es conexo)

Propiedades
-----------
- Voraz y óptimo: por la propiedad del corte, la arista más liviana que une dos
  componentes distintas siempre pertenece a algún árbol de expansión mínima.
- Tiempo O(E log E) por el ordenamiento; las consultas UFDS cuestan O(α(V)).
- Si el grafo no es conexo devuelve un bosque: un árbol por componente.
- En el proyecto, los vértices son puntos de interés del mapa y el peso de cada
  arista es el costo óptimo (A*) entre ellos: el árbol es la red de patrullaje
  más corta que conecta todos los puntos.
"""

from dataclasses import dataclass

from .contrato import PASOS_NULOS
from .ufds import UFDS


@dataclass(frozen=True)
class ResultadoKruskal:
    arbol: tuple[tuple[object, object, float], ...]
    """Aristas elegidas (u, v, peso), en el orden en que entraron."""
    costo: float
    componentes: int
    """1 si el grafo es conexo; si no, cantidad de árboles del bosque."""


def kruskal(vertices, aristas, observador=PASOS_NULOS) -> ResultadoKruskal:
    ordenadas = sorted(aristas, key=lambda arista: arista[2])  # 1.
    conjuntos = UFDS()                                         # 2.
    for vertice in vertices:
        conjuntos.agregar(vertice)

    arbol, costo = [], 0.0
    necesarias = len(conjuntos.padre) - 1
    for u, v, peso in ordenadas:                               # 3.
        if len(arbol) == necesarias:                           # 8. árbol completo
            break
        if not conjuntos.mismo_conjunto(u, v):                 # 4.
            conjuntos.unir(u, v)                               # 5.
            arbol.append((u, v, peso))
            costo += peso
            observador.paso(5, u=u, v=v, peso=peso, aceptada=True)
        else:                                                  # 6.
            observador.paso(7, u=u, v=v, peso=peso, aceptada=False)   # 7. ciclo
    return ResultadoKruskal(tuple(arbol), costo, conjuntos.num_conjuntos)   # 9.
