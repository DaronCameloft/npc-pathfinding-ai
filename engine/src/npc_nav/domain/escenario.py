"""Consulta de referencia del benchmark: origen, destino y costo óptimo publicado."""

from dataclasses import dataclass
from math import isfinite

from .mapa import Posicion


@dataclass(frozen=True)
class Escenario:
    bucket: int
    mapa: str
    ancho: int
    alto: int
    inicio: Posicion
    destino: Posicion
    optimo: float

    def __post_init__(self):
        if self.bucket < 0 or self.ancho <= 0 or self.alto <= 0:
            raise ValueError('Bucket y dimensiones del escenario inválidos')
        if not isfinite(self.optimo) or self.optimo < 0:
            raise ValueError('El costo de referencia debe ser finito y no negativo')
        for fila, columna in (self.inicio, self.destino):
            if not (0 <= fila < self.alto and 0 <= columna < self.ancho):
                raise ValueError('Coordenada del escenario fuera de sus dimensiones')
