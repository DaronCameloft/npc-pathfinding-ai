"""Contrato común de los algoritmos de búsqueda.

Cada algoritmo es una función con la misma firma:

    algoritmo(grafo, inicio, destino, observador) -> ResultadoBusqueda

- `grafo` solo necesita el método `vecinos(posicion) -> [(vecino, costo), ...]`.
- `observador` recibe los pasos de la búsqueda (para medir y para dibujar). El
  algoritmo no mide tiempos ni cuenta nodos: eso lo hace la capa de aplicación.
- Cada aviso indica en `linea` el número de la línea del pseudocódigo (docstring
  del algoritmo) que se está ejecutando, para que el dashboard la resalte.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol

from ..domain.mapa import Posicion


class Grafo(Protocol):
    def vecinos(self, posicion: Posicion) -> Iterable[tuple[Posicion, float]]: ...


class Observador(Protocol):
    def frontera(self, posicion: Posicion, g: float, h: float,
                 padre: Posicion | None, linea: int) -> None:
        """Una celda entra a la frontera o mejora su costo conocido."""

    def expandido(self, posicion: Posicion, g: float, h: float,
                  padre: Posicion | None, linea: int) -> None:
        """Una celda sale de la frontera y se procesan sus vecinos."""


class ObservadorNulo:
    """Observador que ignora todos los eventos."""

    def frontera(self, posicion, g, h, padre, linea):
        pass

    def expandido(self, posicion, g, h, padre, linea):
        pass


NULO = ObservadorNulo()


@dataclass(frozen=True)
class ResultadoBusqueda:
    ruta: tuple[Posicion, ...]
    """Posiciones desde el inicio hasta el destino; vacía si no hay ruta."""
    costo: float | None
    """Suma de pesos de la ruta; None si no hay ruta."""

    @property
    def encontrada(self) -> bool:
        return bool(self.ruta)


SIN_RUTA = ResultadoBusqueda((), None)

Algoritmo = Callable[[Grafo, Posicion, Posicion, Observador], ResultadoBusqueda]


def reconstruir_ruta(padres: dict[Posicion, Posicion], inicio: Posicion,
                     destino: Posicion) -> tuple[Posicion, ...]:
    """Sigue los punteros `padre` desde el destino hasta el inicio."""
    ruta = [destino]
    while ruta[-1] != inicio:
        ruta.append(padres[ruta[-1]])
    return tuple(reversed(ruta))
