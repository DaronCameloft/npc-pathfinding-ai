"""Edmonds-Karp — flujo máximo y corte mínimo con caminos aumentantes por BFS.

Referencia: Edmonds, J. y Karp, R. M. (1972). Theoretical improvements in
algorithmic efficiency for network flow problems. Journal of the ACM 19(2),
248-264.

Pseudocódigo
------------
 1. flujo = 0; residual(u, v) = capacidad(u, v) y residual(v, u) = 0
 2. repetir:
 3.     BFS desde la fuente por aristas con residual > 0, guardando padres
 4.     si el BFS no alcanzó el sumidero: salir del ciclo
 5.     cuello = menor residual del camino fuente → sumidero encontrado
 6.     para cada arista (u, v) del camino:
 7.         residual(u, v) -= cuello; residual(v, u) += cuello
 8.     flujo += cuello
 9. corte mínimo: lo que alcanzó el último BFS es el lado de la fuente
10. devolver el flujo y el corte

Propiedades
-----------
- Es Ford-Fulkerson eligiendo siempre el camino aumentante con menos aristas
  (BFS). Así termina en O(V · E²) aunque las capacidades no sean enteras.
- Flujo máximo = corte mínimo: las aristas que salen del lado de la fuente
  hacia el resto están saturadas y su capacidad suma exactamente el flujo.
- En el proyecto cada celda de un pasillo tiene capacidad 1 (se parte en una
  entrada y una salida). El flujo máximo es cuántos NPC pueden cruzarlo a la
  vez sin compartir celdas, y el corte mínimo son las celdas que hay que
  bloquear para cerrarlo (teorema de Menger).
"""

from collections import deque
from dataclasses import dataclass

from .contrato import PASOS_NULOS


@dataclass(frozen=True)
class ResultadoFlujo:
    valor: float
    flujo: dict
    """{(u, v): unidades} sobre las aristas originales con flujo positivo."""
    lado_fuente: frozenset
    """Vértices alcanzables desde la fuente en la red residual final."""


def edmonds_karp(capacidades, fuente, sumidero, observador=PASOS_NULOS) -> ResultadoFlujo:
    """`capacidades` es {u: {v: capacidad}} (red dirigida, sin aristas antiparalelas).

    Las capacidades deben ser finitas: para "sin límite" use un número mayor que
    cualquier corte posible (con infinito, inf - inf no da el flujo enviado).
    """
    if fuente == sumidero:
        raise ValueError('La fuente y el sumidero deben ser distintos')
    residual = {fuente: {}, sumidero: {}}                      # 1.
    for u, salientes in capacidades.items():
        for v, capacidad in salientes.items():
            residual.setdefault(u, {})
            residual[u][v] = residual[u].get(v, 0) + capacidad
            residual.setdefault(v, {}).setdefault(u, 0)
    valor = 0

    while True:                                                # 2.
        padre = {fuente: None}                                 # 3. BFS
        cola = deque([fuente])
        while cola and sumidero not in padre:
            u = cola.popleft()
            for v, libre in residual[u].items():
                if libre > 0 and v not in padre:
                    padre[v] = u
                    cola.append(v)
        if sumidero not in padre:                              # 4.
            break

        camino = [sumidero]
        while camino[-1] != fuente:
            camino.append(padre[camino[-1]])
        camino.reverse()
        aristas = list(zip(camino, camino[1:]))
        cuello = min(residual[u][v] for u, v in aristas)       # 5.
        for u, v in aristas:                                   # 6.
            residual[u][v] -= cuello                           # 7.
            residual[v][u] += cuello
        valor += cuello                                        # 8.
        observador.paso(8, camino=tuple(camino), cuello=cuello, flujo=valor)

    lado_fuente = frozenset(padre)                             # 9. último BFS
    observador.paso(9, lado_fuente=lado_fuente)
    flujo = {}
    for u, salientes in capacidades.items():
        for v, capacidad in salientes.items():
            enviado = capacidad - residual[u][v]
            if enviado > 0:
                flujo[(u, v)] = enviado
    return ResultadoFlujo(valor, flujo, lado_fuente)          # 10.
