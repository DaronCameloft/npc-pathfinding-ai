"""Reglas de movimiento octil: definen las aristas del grafo y sus pesos.

- Cuatro movimientos cardinales de costo 1.
- Cuatro diagonales de costo raíz de 2.
- Una diagonal solo es legal si el destino y las dos celdas cardinales laterales
  están libres: el NPC no atraviesa esquinas entre obstáculos. Es la misma regla
  con la que Moving AI calcula los óptimos de los archivos .scen.
"""

from collections.abc import Callable
from math import sqrt

from .mapa import Posicion

COSTO_CARDINAL = 1.0
COSTO_DIAGONAL = sqrt(2)
CARDINALES = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONALES = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def movimientos_desde(origen: Posicion, transitable: Callable[[Posicion], bool]):
    """Devuelve pares (vecino, costo); una celda bloqueada no tiene movimientos."""
    if not transitable(origen):
        return ()
    fila, columna = origen
    movimientos = []
    for df, dc in CARDINALES:
        destino = (fila + df, columna + dc)
        if transitable(destino):
            movimientos.append((destino, COSTO_CARDINAL))
    for df, dc in DIAGONALES:
        destino = (fila + df, columna + dc)
        if (transitable(destino) and transitable((fila + df, columna))
                and transitable((fila, columna + dc))):
            movimientos.append((destino, COSTO_DIAGONAL))
    return tuple(movimientos)


def distancia_octil(a: Posicion, b: Posicion) -> float:
    """Costo del trayecto más corto sin obstáculos: heurística admisible y consistente.

    h = max(df, dc) + (raíz de 2 - 1) * min(df, dc)
    """
    df, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(df, dc) + (COSTO_DIAGONAL - 1) * min(df, dc)
