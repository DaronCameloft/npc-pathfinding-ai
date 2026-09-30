"""Mapa del escenario: terreno inmutable leído del dataset.

Las posiciones se expresan como (fila, columna), con origen (0, 0) en la
esquina superior izquierda.
"""

from dataclasses import dataclass

Posicion = tuple[int, int]

TRANSITABLES = frozenset('.G')
"""Solo '.' y 'G' son transitables en este proyecto."""

TERRENOS = frozenset('.G@OTSW')
"""Símbolos válidos del formato Moving AI: @ y O fuera de límites, T árboles,
S pantano y W agua. Todos excepto '.' y 'G' se tratan como obstáculos."""


@dataclass(frozen=True)
class Mapa:
    nombre: str
    celdas: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, 'celdas', tuple(self.celdas))
        if not self.celdas or not self.celdas[0]:
            raise ValueError('El mapa debe tener dimensiones positivas')
        if any(len(fila) != self.ancho for fila in self.celdas):
            raise ValueError('Las filas del mapa deben tener el mismo ancho')
        if any(celda not in TERRENOS for fila in self.celdas for celda in fila):
            raise ValueError('El mapa contiene un símbolo de terreno desconocido')

    @property
    def alto(self) -> int:
        return len(self.celdas)

    @property
    def ancho(self) -> int:
        return len(self.celdas[0])

    def contiene(self, posicion: Posicion) -> bool:
        fila, columna = posicion
        return 0 <= fila < self.alto and 0 <= columna < self.ancho

    def transitable(self, posicion: Posicion) -> bool:
        return (self.contiene(posicion)
                and self.celdas[posicion[0]][posicion[1]] in TRANSITABLES)

    def posiciones_transitables(self):
        """Recorre todas las celdas transitables (los vértices del grafo)."""
        for fila, texto in enumerate(self.celdas):
            for columna, celda in enumerate(texto):
                if celda in TRANSITABLES:
                    yield fila, columna
