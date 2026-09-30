"""Dominio: mapa, reglas de movimiento y sesión con obstáculos dinámicos.

Sin dependencias externas ni entrada/salida.
"""

from .escenario import Escenario
from .mapa import TERRENOS, TRANSITABLES, Mapa, Posicion
from .movimiento import COSTO_CARDINAL, COSTO_DIAGONAL, distancia_octil, movimientos_desde
from .sesion import SesionNavegacion

__all__ = ['Escenario', 'Mapa', 'Posicion', 'TERRENOS', 'TRANSITABLES',
           'COSTO_CARDINAL', 'COSTO_DIAGONAL', 'distancia_octil', 'movimientos_desde',
           'SesionNavegacion']
