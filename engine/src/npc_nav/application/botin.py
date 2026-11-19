"""Caso de uso: qué botín carga el NPC (mochila 0/1 por programación dinámica).

El NPC encuentra objetos con un peso (entero) y un valor y solo puede cargar
hasta `capacidad`. La programación dinámica da la mejor combinación. Como
contraste se calcula el voraz por densidad (valor / peso), que es la intuición
natural pero no garantiza el óptimo en la versión 0/1.
"""

from dataclasses import dataclass
from time import perf_counter_ns

from ..algorithms.mochila import mochila

MAX_OBJETOS = 25
MAX_CAPACIDAD = 100


@dataclass(frozen=True)
class Objeto:
    nombre: str
    peso: int
    valor: int


BOTIN_DE_EJEMPLO = (
    Objeto('Espada larga', 8, 40),
    Objeto('Escudo de roble', 9, 38),
    Objeto('Arco corto', 5, 26),
    Objeto('Poción de vida', 1, 6),
    Objeto('Pergamino de fuego', 2, 13),
    Objeto('Gema azul', 3, 20),
    Objeto('Anillo de plata', 1, 7),
    Objeto('Yelmo de hierro', 6, 27),
    Objeto('Cota de malla', 12, 52),
    Objeto('Libro de runas', 4, 17),
    Objeto('Bolsa de monedas', 2, 11),
    Objeto('Daga élfica', 3, 16),
)
CAPACIDAD_DE_EJEMPLO = 20


@dataclass(frozen=True)
class Carga:
    elegidos: tuple[int, ...]
    peso: int
    valor: int


@dataclass(frozen=True)
class SeleccionBotin:
    objetos: tuple[Objeto, ...]
    capacidad: int
    optima: Carga
    """Programación dinámica."""
    voraz: Carga
    """Voraz por densidad valor/peso, como contraste."""
    tabla: tuple[tuple[int, ...], ...]
    """tabla[i][c]: mejor valor con los i primeros objetos y capacidad c."""
    reconstruccion: tuple[tuple[int, int], ...]
    """Celdas (i, c) que recorre la reconstrucción, desde (n, W) hasta la fila 0."""
    tiempo_ms: float


def _carga(objetos, elegidos) -> Carga:
    elegidos = tuple(sorted(elegidos))
    return Carga(elegidos, sum(objetos[i].peso for i in elegidos),
                 sum(objetos[i].valor for i in elegidos))


def _voraz_por_densidad(objetos, capacidad) -> Carga:
    """Toma los objetos de mayor valor por unidad de peso mientras quepan."""
    orden = sorted(range(len(objetos)),
                   key=lambda i: (-objetos[i].valor / max(objetos[i].peso, 1e-9), i))
    elegidos, libre = [], capacidad
    for i in orden:
        if objetos[i].peso <= libre:
            elegidos.append(i)
            libre -= objetos[i].peso
    return _carga(objetos, elegidos)


def elegir_botin(objetos=BOTIN_DE_EJEMPLO, capacidad: int = CAPACIDAD_DE_EJEMPLO) -> SeleccionBotin:
    objetos = tuple(objetos)
    if not 1 <= len(objetos) <= MAX_OBJETOS:
        raise ValueError(f'Indique entre 1 y {MAX_OBJETOS} objetos')
    if not 0 <= capacidad <= MAX_CAPACIDAD:
        raise ValueError(f'La capacidad debe estar entre 0 y {MAX_CAPACIDAD}')
    if any(o.peso < 1 or o.valor < 0 for o in objetos):
        raise ValueError('Cada objeto necesita peso entero positivo y valor no negativo')

    reloj = perf_counter_ns()
    resultado = mochila([o.peso for o in objetos], [o.valor for o in objetos], capacidad)
    tiempo_ms = (perf_counter_ns() - reloj) / 1_000_000

    elegidos, c, camino = set(resultado.elegidos), capacidad, []
    for i in range(len(objetos), 0, -1):
        camino.append((i, c))
        if i - 1 in elegidos:
            c -= objetos[i - 1].peso
    camino.append((0, c))

    return SeleccionBotin(objetos=objetos, capacidad=capacidad,
                          optima=_carga(objetos, resultado.elegidos),
                          voraz=_voraz_por_densidad(objetos, capacidad),
                          tabla=resultado.tabla, reconstruccion=tuple(camino),
                          tiempo_ms=tiempo_ms)
