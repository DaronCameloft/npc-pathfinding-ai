"""Mochila 0/1 — programación dinámica de abajo hacia arriba.

Referencia: Bellman, R. (1957). Dynamic Programming. Princeton University
Press. Kellerer, H., Pferschy, U. y Pisinger, D. (2004). Knapsack Problems.
Springer, cap. 2.

Pseudocódigo
------------
 1. tabla[0][c] = 0 para toda capacidad c de 0 a W
 2. para i de 1 a n (objeto i con peso p y valor v):
 3.     para c de 0 a W:
 4.         tabla[i][c] = tabla[i-1][c]  (no llevar el objeto i)
 5.         si p <= c y tabla[i-1][c-p] + v > tabla[i][c]:
 6.             tabla[i][c] = tabla[i-1][c-p] + v  (llevarlo)
 7. c = W  (reconstrucción desde la última fila)
 8. para i de n a 1:
 9.     si tabla[i][c] != tabla[i-1][c]: llevar el objeto i y c = c - p
10. devolver tabla[n][W] y los objetos elegidos

Propiedades
-----------
- Subestructura óptima: la mejor mochila con los i primeros objetos y
  capacidad c lleva o no el objeto i, y el resto es la mejor mochila de un
  subproblema más pequeño. Cada subproblema se resuelve una sola vez.
- Tiempo y memoria O(n · W): pseudopolinomial (depende del valor de W, no de
  su tamaño en bits). El problema es NP-difícil en general.
- Un voraz por valor/peso NO es óptimo en la versión 0/1 (sí en la
  fraccionaria); la aplicación lo muestra como contraste.
- En el proyecto: el NPC elige qué botín cargar sin pasar el peso máximo.
"""

from dataclasses import dataclass

from .contrato import PASOS_NULOS


@dataclass(frozen=True)
class ResultadoMochila:
    valor: int
    elegidos: tuple[int, ...]
    """Índices (desde 0) de los objetos elegidos, en orden creciente."""
    tabla: tuple[tuple[int, ...], ...]
    """tabla[i][c]: mejor valor con los i primeros objetos y capacidad c."""


def mochila(pesos, valores, capacidad, observador=PASOS_NULOS) -> ResultadoMochila:
    if len(pesos) != len(valores):
        raise ValueError('Cada objeto necesita un peso y un valor')
    if capacidad < 0 or any(p < 0 for p in pesos):
        raise ValueError('La capacidad y los pesos no pueden ser negativos')
    n = len(pesos)
    tabla = [[0] * (capacidad + 1)]                            # 1.
    for i in range(1, n + 1):                                  # 2.
        p, v = pesos[i - 1], valores[i - 1]
        anterior = tabla[i - 1]
        fila = anterior[:]                                     # 3. y 4. no llevarlo
        for c in range(p, capacidad + 1):
            if anterior[c - p] + v > fila[c]:                  # 5.
                fila[c] = anterior[c - p] + v                  # 6. llevarlo
        tabla.append(fila)
        observador.paso(6, objeto=i - 1, fila=tuple(fila))

    elegidos, c = [], capacidad                                # 7.
    for i in range(n, 0, -1):                                  # 8.
        if tabla[i][c] != tabla[i - 1][c]:                     # 9.
            elegidos.append(i - 1)
            c -= pesos[i - 1]
            observador.paso(9, objeto=i - 1, capacidad_restante=c)
    return ResultadoMochila(tabla[n][capacidad], tuple(reversed(elegidos)),   # 10.
                            tuple(map(tuple, tabla)))
