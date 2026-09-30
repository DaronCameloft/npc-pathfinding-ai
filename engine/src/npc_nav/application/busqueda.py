"""Caso de uso: ejecutar y comparar algoritmos midiendo su trabajo.

Los algoritmos no miden nada; aquí se les inyecta un observador que cuenta
nodos y, si se pide, graba la traza para el dashboard.

Medición:
- `tiempo_ms` se toma en una ejecución con un observador que solo cuenta.
- Si se pide traza, se ejecuta una segunda vez con un observador que graba los
  eventos. La búsqueda es determinista, así que la traza corresponde exactamente
  a la ejecución medida, y el tiempo nunca incluye la grabación.
"""

from dataclasses import dataclass
from time import perf_counter_ns

from ..algorithms.catalogo import obtener
from ..domain.mapa import Posicion
from ..domain.sesion import SesionNavegacion


@dataclass(frozen=True)
class EventoBusqueda:
    tipo: str
    """'frontera' (entra o mejora en la frontera) o 'expandido' (se procesa)."""
    posicion: Posicion
    g: float
    h: float
    padre: Posicion | None = None


@dataclass(frozen=True)
class MetricasBusqueda:
    nodos_expandidos: int
    """Celdas procesadas (extraídas de la frontera con su costo vigente)."""
    nodos_descubiertos: int
    """Celdas distintas que llegaron a tener un costo conocido."""
    max_frontera: int
    """Máximo de celdas distintas pendientes en la frontera (memoria)."""
    tiempo_ms: float
    """Tiempo del algoritmo; excluye lectura de datos, traza, red y animación."""


@dataclass(frozen=True)
class Ejecucion:
    algoritmo: str
    estado: str
    """'encontrada' o 'sin_ruta'."""
    ruta: tuple[Posicion, ...]
    costo: float | None
    version_mapa: int
    metricas: MetricasBusqueda
    traza: tuple[EventoBusqueda, ...]


class _Contador:
    def __init__(self):
        self.expandidos = 0
        self.descubiertos = set()
        self.pendientes = set()
        self.max_frontera = 0

    def frontera(self, posicion, g, h, padre):
        self.descubiertos.add(posicion)
        self.pendientes.add(posicion)
        self.max_frontera = max(self.max_frontera, len(self.pendientes))

    def expandido(self, posicion, g, h, padre):
        self.expandidos += 1
        self.pendientes.discard(posicion)


class _Grabador:
    def __init__(self):
        self.eventos = []

    def frontera(self, posicion, g, h, padre):
        self.eventos.append(EventoBusqueda('frontera', posicion, g, h, padre))

    def expandido(self, posicion, g, h, padre):
        self.eventos.append(EventoBusqueda('expandido', posicion, g, h, padre))


def ejecutar_busqueda(sesion: SesionNavegacion, algoritmo: str, inicio: Posicion,
                      destino: Posicion, *, con_traza: bool = False) -> Ejecucion:
    """Ejecuta `algoritmo` sobre el estado actual de la sesión.

    Rechaza extremos no transitables con ValueError. Un destino libre pero
    inaccesible produce estado 'sin_ruta'.
    """
    info = obtener(algoritmo)
    sesion.validar_consulta(inicio, destino)
    version = sesion.version

    contador = _Contador()
    reloj = perf_counter_ns()
    resultado = info.funcion(sesion, inicio, destino, contador)
    tiempo_ms = (perf_counter_ns() - reloj) / 1_000_000

    traza = ()
    if con_traza:
        grabador = _Grabador()
        info.funcion(sesion, inicio, destino, grabador)
        traza = tuple(grabador.eventos)

    if sesion.version != version:
        raise RuntimeError('El mapa cambió durante la búsqueda; vuelva a calcular la ruta')
    return Ejecucion(
        algoritmo=info.clave,
        estado='encontrada' if resultado.encontrada else 'sin_ruta',
        ruta=resultado.ruta, costo=resultado.costo, version_mapa=version,
        metricas=MetricasBusqueda(contador.expandidos, len(contador.descubiertos),
                                  contador.max_frontera, tiempo_ms),
        traza=traza,
    )


def comparar_algoritmos(sesion: SesionNavegacion, algoritmos: list[str], inicio: Posicion,
                        destino: Posicion, *, con_traza: bool = False) -> list[Ejecucion]:
    """Ejecuta varios algoritmos sobre la misma sesión, consulta y estado del mapa."""
    return [ejecutar_busqueda(sesion, clave, inicio, destino, con_traza=con_traza)
            for clave in algoritmos]
