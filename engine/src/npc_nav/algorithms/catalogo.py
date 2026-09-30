"""Catálogo de algoritmos de búsqueda disponibles para el motor, la API y la web.

Para agregar un algoritmo: crear su archivo en esta carpeta con la firma de
`contrato.Algoritmo` y registrarlo aquí.
"""

from dataclasses import dataclass

from .astar import astar
from .bfs import bfs
from .contrato import Algoritmo
from .dijkstra import dijkstra
from .voraz import voraz


@dataclass(frozen=True)
class InfoAlgoritmo:
    clave: str
    nombre: str
    funcion: Algoritmo
    garantiza_optimo: bool
    tecnica: str
    """Técnica del curso a la que pertenece (enunciado, sección 6)."""
    complejidad: str
    referencia: str


ALGORITMOS: dict[str, InfoAlgoritmo] = {info.clave: info for info in (
    InfoAlgoritmo('bfs', 'BFS (anchura)', bfs, False,
                  'Recorridos y búsquedas en grafos', 'O(V + E)',
                  'Cormen et al. (2009)'),
    InfoAlgoritmo('dijkstra', 'Dijkstra', dijkstra, True,
                  'Recorridos y búsquedas en grafos', 'O(E log V)',
                  'Dijkstra (1959)'),
    InfoAlgoritmo('voraz', 'Voraz primero el mejor', voraz, False,
                  'Algoritmos voraces', 'O(E log V)',
                  'Russell y Norvig (2021)'),
    InfoAlgoritmo('astar', 'A*', astar, True,
                  'Algoritmos voraces (heurístico) + búsqueda en grafos', 'O(E log V)',
                  'Hart, Nilsson y Raphael (1968)'),
)}


def obtener(clave: str) -> InfoAlgoritmo:
    try:
        return ALGORITMOS[clave]
    except KeyError:
        disponibles = ', '.join(ALGORITMOS)
        raise ValueError(f'Algoritmo desconocido: {clave!r}. Disponibles: {disponibles}') from None
