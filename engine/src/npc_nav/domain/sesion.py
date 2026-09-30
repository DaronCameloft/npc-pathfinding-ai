"""Sesión de navegación: el mapa original más los obstáculos dinámicos de una partida.

Es el grafo que consultan todos los algoritmos. No se guardan listas de
adyacencia: los vecinos se calculan al consultarlos, así un bloqueo nunca deja
aristas desactualizadas.
"""

from collections.abc import Iterable
from math import inf

from .mapa import Mapa, Posicion
from .movimiento import movimientos_desde


class SesionNavegacion:
    """Mapa estático compartido + obstáculos propios de esta sesión."""

    def __init__(self, mapa: Mapa):
        self.mapa = mapa
        self._bloqueadas: set[Posicion] = set()
        self._version = 0

    @property
    def bloqueadas(self) -> frozenset[Posicion]:
        return frozenset(self._bloqueadas)

    @property
    def version(self) -> int:
        """Aumenta cada vez que cambian los obstáculos."""
        return self._version

    def transitable(self, posicion: Posicion) -> bool:
        return self.mapa.transitable(posicion) and posicion not in self._bloqueadas

    def vecinos(self, origen: Posicion) -> tuple[tuple[Posicion, float], ...]:
        """Aristas salientes de `origen`: pares (vecino, costo)."""
        return movimientos_desde(origen, self.transitable)

    def costo_movimiento(self, origen: Posicion, destino: Posicion) -> float:
        """Un movimiento inexistente o bloqueado tiene costo infinito."""
        return next((costo for vecino, costo in self.vecinos(origen)
                     if vecino == destino), inf)

    def validar_consulta(self, inicio: Posicion, destino: Posicion) -> None:
        """Comprueba extremos transitables; no demuestra que exista una ruta."""
        for nombre, posicion in (('inicio', inicio), ('destino', destino)):
            if not self.transitable(posicion):
                raise ValueError(f'{nombre} no es una celda transitable: {posicion}')

    def costo_ruta(self, ruta: Iterable[Posicion]) -> float:
        """Suma los pesos de una ruta y rechaza saltos o pasos bloqueados."""
        puntos = tuple(ruta)
        if not puntos:
            raise ValueError('Una ruta debe contener al menos una posición')
        self.validar_consulta(puntos[0], puntos[-1])
        total = 0.0
        for origen, destino in zip(puntos, puntos[1:]):
            costo = self.costo_movimiento(origen, destino)
            if costo == inf:
                raise ValueError(f'Paso de ruta inválido: {origen} → {destino}')
            total += costo
        return total

    def actualizar_obstaculos(self, *, bloquear: Iterable[Posicion] = (),
                              liberar: Iterable[Posicion] = ()) -> tuple[Posicion, ...]:
        """Aplica un cambio atómico y devuelve las celdas que realmente cambiaron.

        Solo se puede bloquear o liberar terreno originalmente transitable.
        """
        bloquear, liberar = set(bloquear), set(liberar)
        if bloquear & liberar:
            raise ValueError('Una celda no puede bloquearse y liberarse en el mismo cambio')
        for posicion in bloquear | liberar:
            if not self.mapa.transitable(posicion):
                raise ValueError(f'Obstáculo fuera del terreno transitable: {posicion}')
        nuevas = (self._bloqueadas | bloquear) - liberar
        cambiadas = tuple(sorted(self._bloqueadas ^ nuevas))
        if cambiadas:
            self._bloqueadas = nuevas
            self._version += 1
        return cambiadas
