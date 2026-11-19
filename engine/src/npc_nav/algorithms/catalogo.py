"""Catálogo de algoritmos disponibles para el motor, la API y la web.

- `ALGORITMOS`: búsquedas de ruta con la firma de `contrato.Algoritmo`.
- `COMPLEMENTARIOS`: Kruskal, Edmonds-Karp y mochila; cada uno con su caso de uso.

Para agregar un algoritmo: crear su archivo en esta carpeta y registrarlo aquí.
"""

from dataclasses import dataclass

from .astar import astar
from .bfs import bfs
from .contrato import Algoritmo
from .dijkstra import dijkstra
from .dstar_lite import dstar_lite
from .edmonds_karp import edmonds_karp
from .kruskal import kruskal
from .mochila import mochila
from .pseudocodigo import LineaPseudocodigo, pseudocodigo_de
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
    incremental: bool = False
    """Conserva su estado entre cambios del mapa y busca desde la meta hacia el NPC."""

    @property
    def pseudocodigo(self) -> tuple[LineaPseudocodigo, ...]:
        """Líneas numeradas del docstring del algoritmo (las mismas de la traza)."""
        return pseudocodigo_de(self.funcion)


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
    InfoAlgoritmo('dstar_lite', 'D* Lite', dstar_lite, True,
                  'Búsqueda incremental en grafos (programación dinámica)', 'O(E log V)',
                  'Koenig y Likhachev (2002)', incremental=True),
)}


@dataclass(frozen=True)
class InfoComplementario:
    """Algoritmo que no busca una ruta origen→destino: tiene su propio caso de uso."""
    clave: str
    nombre: str
    funcion: object
    tecnica: str
    complejidad: str
    referencia: str
    caso_de_uso: str

    @property
    def pseudocodigo(self) -> tuple[LineaPseudocodigo, ...]:
        return pseudocodigo_de(self.funcion)


COMPLEMENTARIOS: dict[str, InfoComplementario] = {info.clave: info for info in (
    InfoComplementario('kruskal', 'Kruskal', kruskal,
                       'Árbol de expansión mínima (voraz + UFDS)', 'O(E log E)',
                       'Kruskal (1956)',
                       'Red de patrullaje más corta entre puntos de interés del mapa'),
    InfoComplementario('edmonds_karp', 'Edmonds-Karp', edmonds_karp,
                       'Flujo en redes', 'O(V · E²)',
                       'Edmonds y Karp (1972)',
                       'Cuántos NPC cruzan un pasillo a la vez y qué celdas lo cierran'),
    InfoComplementario('mochila', 'Mochila 0/1', mochila,
                       'Programación dinámica', 'O(n · W)',
                       'Bellman (1957)',
                       'Qué botín carga el NPC sin pasar su peso máximo'),
)}
"""No entran en /comparar ni en `npc-nav verificar`: cada uno tiene su endpoint."""


def obtener(clave: str) -> InfoAlgoritmo:
    try:
        return ALGORITMOS[clave]
    except KeyError:
        disponibles = ', '.join(ALGORITMOS)
        raise ValueError(f'Algoritmo desconocido: {clave!r}. Disponibles: {disponibles}') from None
