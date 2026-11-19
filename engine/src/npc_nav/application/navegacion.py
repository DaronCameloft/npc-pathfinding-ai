"""Caso de uso: un NPC que avanza por su ruta mientras aparecen y desaparecen obstáculos.

Una `NavegacionDinamica` tiene un solo NPC (una posición), una sola sesión de
obstáculos y uno o más planificadores. Todos reciben los mismos cambios desde la
misma posición, así la comparación A* / D* Lite es justa (docs/plan.md,
«Protocolo de validación»):

- Algoritmos no incrementales (A*, Dijkstra, …): tras cada cambio se vuelve a
  buscar desde cero desde la posición actual (recálculo completo).
- D* Lite: conserva g, rhs y su cola entre cambios y solo corrige lo afectado.

El NPC sigue la ruta del primer algoritmo de la lista (el «guía»). Las rutas de
los demás tienen el mismo costo si son óptimos, aunque pueden pasar por otras
celdas con el mismo costo.

Medición: igual que en `busqueda.py`, el tiempo se toma con un observador que
solo cuenta. Si se pide traza, la misma operación se repite sobre una copia del
planificador (D* Lite se clona antes de cambiar), fuera del tiempo medido.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from time import perf_counter_ns

from ..algorithms.catalogo import obtener
from ..algorithms.contrato import ResultadoBusqueda
from ..algorithms.dstar_lite import DStarLite
from ..domain.mapa import Mapa, Posicion
from ..domain.sesion import SesionNavegacion
from .busqueda import EventoBusqueda, MetricasBusqueda, _Contador, _Grabador


@dataclass(frozen=True)
class Planificacion:
    algoritmo: str
    motivo: str
    """'inicial' o 'obstaculos'."""
    estado: str
    """'encontrada' o 'sin_ruta'."""
    posicion: Posicion
    """Celda del NPC desde la que se planificó."""
    paso: int
    """Movimientos que llevaba el NPC al planificar (índice en `recorrido`)."""
    ruta: tuple[Posicion, ...]
    costo: float | None
    version_mapa: int
    celdas_cambiadas: tuple[Posicion, ...]
    ruta_afectada: bool
    """Algún cambio bloqueó una celda de la ruta que el algoritmo tenía vigente."""
    metricas: MetricasBusqueda
    traza: tuple[EventoBusqueda, ...]


class _RecalculoCompleto:
    """Planificador sin memoria: cada cambio es una búsqueda nueva."""

    def __init__(self, sesion: SesionNavegacion, clave: str, destino: Posicion):
        self._sesion, self._funcion, self._destino = sesion, obtener(clave).funcion, destino

    def planificar(self, posicion, cambiadas, observador) -> ResultadoBusqueda:
        return self._funcion(self._sesion, posicion, self._destino, observador)

    def copia(self):
        return self


class _Incremental:
    """D* Lite: la primera llamada planifica; las siguientes reparan."""

    def __init__(self, sesion: SesionNavegacion, inicio: Posicion, destino: Posicion):
        self._dstar = DStarLite(sesion, inicio, destino)
        self._planificado = False

    def planificar(self, posicion, cambiadas, observador) -> ResultadoBusqueda:
        if not self._planificado:
            self._planificado = True
            return self._dstar.planificar(observador)
        return self._dstar.replanificar(posicion, cambiadas, observador)

    def copia(self):
        copia = _Incremental.__new__(_Incremental)
        copia._dstar, copia._planificado = self._dstar.clonar(), self._planificado
        return copia


class NavegacionDinamica:
    """Un NPC, un estado de obstáculos y uno o más planificadores sincronizados."""

    def __init__(self, mapa: Mapa, inicio: Posicion, destino: Posicion, *,
                 algoritmos: Sequence[str] = ('astar', 'dstar_lite'),
                 bloqueadas: Iterable[Posicion] = (), con_traza: bool = False):
        if not algoritmos:
            raise ValueError('Indique al menos un algoritmo')
        claves = [obtener(clave).clave for clave in algoritmos]
        if len(set(claves)) != len(claves):
            raise ValueError('Algoritmos repetidos')
        self.sesion = SesionNavegacion(mapa)
        bloqueadas = set(bloqueadas)
        if {inicio, destino} & bloqueadas:
            raise ValueError('El inicio y el destino no pueden estar bloqueados')
        self.sesion.actualizar_obstaculos(bloquear=bloqueadas)
        self.sesion.validar_consulta(inicio, destino)

        self.inicio, self.destino, self.posicion = inicio, destino, inicio
        self.recorrido: list[Posicion] = [inicio]
        self.distancia_recorrida = 0.0
        self.historial: list[Planificacion] = []
        self.vigentes: dict[str, Planificacion] = {}
        self._avance = 0
        """Índice de `posicion` dentro de la ruta vigente del guía."""
        self._planificadores = {
            clave: (_Incremental(self.sesion, inicio, destino) if obtener(clave).incremental
                    else _RecalculoCompleto(self.sesion, clave, destino))
            for clave in claves}
        self._planificar_todos('inicial', (), con_traza)

    # -- consultas -----------------------------------------------------------
    @property
    def algoritmos(self) -> tuple[str, ...]:
        return tuple(self._planificadores)

    @property
    def guia(self) -> str:
        return self.algoritmos[0]

    @property
    def llegado(self) -> bool:
        return self.posicion == self.destino

    def ruta_restante(self) -> tuple[Posicion, ...]:
        """Lo que le falta recorrer al NPC según el guía (vacía si no hay ruta)."""
        return self.vigentes[self.guia].ruta[self._avance:]

    # -- operaciones ---------------------------------------------------------
    def avanzar(self, pasos: int = 1) -> int:
        """Mueve el NPC por la ruta del guía; devuelve cuántos pasos dio."""
        if pasos < 0:
            raise ValueError('Los pasos no pueden ser negativos')
        ruta = self.vigentes[self.guia].ruta
        dados = 0
        while dados < pasos and ruta and self._avance < len(ruta) - 1:
            siguiente = ruta[self._avance + 1]
            self.distancia_recorrida += self.sesion.costo_movimiento(self.posicion, siguiente)
            self._avance += 1
            self.posicion = siguiente
            self.recorrido.append(siguiente)
            dados += 1
        return dados

    def cambiar_obstaculos(self, *, bloquear: Iterable[Posicion] = (),
                           liberar: Iterable[Posicion] = (),
                           con_traza: bool = False) -> list[Planificacion]:
        """Aplica el cambio y replanifica todos los algoritmos desde la posición actual.

        Devuelve las planificaciones nuevas (lista vacía si nada cambió).
        """
        bloquear = set(bloquear)
        if {self.posicion, self.destino} & bloquear:
            raise ValueError('No se puede bloquear la celda del NPC ni su destino')
        cambiadas = self.sesion.actualizar_obstaculos(bloquear=bloquear, liberar=liberar)
        if not cambiadas:
            return []
        return self._planificar_todos('obstaculos', cambiadas, con_traza)

    # -- interno -------------------------------------------------------------
    def _planificar_todos(self, motivo, cambiadas, con_traza) -> list[Planificacion]:
        bloqueadas = self.sesion.bloqueadas
        nuevas = []
        for clave, planificador in self._planificadores.items():
            anterior = self.vigentes.get(clave)
            vigente = anterior.ruta[self._avance:] if clave == self.guia and anterior else (
                anterior.ruta if anterior else ())
            afectada = any(celda in bloqueadas for celda in vigente)

            copia = planificador.copia() if con_traza else None
            contador = _Contador()
            reloj = perf_counter_ns()
            resultado = planificador.planificar(self.posicion, cambiadas, contador)
            tiempo_ms = (perf_counter_ns() - reloj) / 1_000_000
            traza = ()
            if con_traza:
                grabador = _Grabador()
                copia.planificar(self.posicion, cambiadas, grabador)
                traza = tuple(grabador.eventos)

            plan = Planificacion(
                algoritmo=clave, motivo=motivo,
                estado='encontrada' if resultado.encontrada else 'sin_ruta',
                posicion=self.posicion, paso=len(self.recorrido) - 1,
                ruta=resultado.ruta, costo=resultado.costo,
                version_mapa=self.sesion.version, celdas_cambiadas=tuple(cambiadas),
                ruta_afectada=afectada,
                metricas=MetricasBusqueda(contador.expandidos, len(contador.descubiertos),
                                          contador.max_frontera, tiempo_ms),
                traza=traza)
            self.vigentes[clave] = plan
            self.historial.append(plan)
            nuevas.append(plan)
        self._avance = 0
        return nuevas


@dataclass(frozen=True)
class CambioProgramado:
    """Cambio de obstáculos que ocurre cuando el NPC lleva `paso` movimientos."""
    paso: int
    bloquear: tuple[Posicion, ...] = ()
    liberar: tuple[Posicion, ...] = ()


@dataclass(frozen=True)
class ResumenAlgoritmo:
    algoritmo: str
    replanificaciones: int
    expandidos_inicial: int
    expandidos_replanificacion: int
    """Suma de celdas procesadas en todas las replanificaciones."""
    tiempo_inicial_ms: float
    tiempo_replanificacion_ms: float
    costo_final: float | None


@dataclass(frozen=True)
class ResultadoSimulacion:
    algoritmos: tuple[str, ...]
    inicio: Posicion
    destino: Posicion
    llegado: bool
    recorrido: tuple[Posicion, ...]
    distancia_recorrida: float
    bloqueadas: tuple[Posicion, ...]
    costos_coinciden: bool
    """Todos los algoritmos óptimos dieron el mismo costo en cada planificación."""
    resumen: tuple[ResumenAlgoritmo, ...]
    historial: tuple[Planificacion, ...]


def resumir(navegacion: NavegacionDinamica) -> tuple[tuple[ResumenAlgoritmo, ...], bool]:
    """Totales por algoritmo y si los óptimos coincidieron en cada planificación."""
    resumen = []
    for clave in navegacion.algoritmos:
        planes = [p for p in navegacion.historial if p.algoritmo == clave]
        inicial, resto = planes[0], planes[1:]
        resumen.append(ResumenAlgoritmo(
            algoritmo=clave, replanificaciones=len(resto),
            expandidos_inicial=inicial.metricas.nodos_expandidos,
            expandidos_replanificacion=sum(p.metricas.nodos_expandidos for p in resto),
            tiempo_inicial_ms=inicial.metricas.tiempo_ms,
            tiempo_replanificacion_ms=sum(p.metricas.tiempo_ms for p in resto),
            costo_final=navegacion.vigentes[clave].costo))

    optimos = [c for c in navegacion.algoritmos if obtener(c).garantiza_optimo]
    coinciden = True
    for version in {p.version_mapa for p in navegacion.historial}:
        costos = [p.costo for p in navegacion.historial
                  if p.version_mapa == version and p.algoritmo in optimos]
        if any(c is None for c in costos) != all(c is None for c in costos):
            coinciden = False
        elif costos and costos[0] is not None and max(costos) - min(costos) > 1e-6:
            coinciden = False
    return tuple(resumen), coinciden


def simular_navegacion(mapa: Mapa, inicio: Posicion, destino: Posicion,
                       cambios: Iterable[CambioProgramado], *,
                       algoritmos: Sequence[str] = ('astar', 'dstar_lite'),
                       bloqueadas: Iterable[Posicion] = (), con_traza: bool = False,
                       max_pasos: int = 100_000) -> ResultadoSimulacion:
    """Recorrido completo y reproducible: el NPC avanza y los cambios ocurren a su paso.

    Si un cambio intenta bloquear la celda del NPC o el destino, esas celdas se omiten.
    La simulación termina al llegar, al quedarse sin ruta o tras `max_pasos`.
    """
    navegacion = NavegacionDinamica(mapa, inicio, destino, algoritmos=algoritmos,
                                    bloqueadas=bloqueadas, con_traza=con_traza)
    pasos = 0
    for cambio in sorted(cambios, key=lambda c: c.paso):
        if cambio.paso > pasos:
            pasos += navegacion.avanzar(cambio.paso - pasos)
        bloquear = set(cambio.bloquear) - {navegacion.posicion, navegacion.destino}
        navegacion.cambiar_obstaculos(bloquear=bloquear, liberar=cambio.liberar,
                                      con_traza=con_traza)
    navegacion.avanzar(max(0, max_pasos - pasos))
    resumen, coinciden = resumir(navegacion)
    return ResultadoSimulacion(
        algoritmos=navegacion.algoritmos, inicio=inicio, destino=destino,
        llegado=navegacion.llegado, recorrido=tuple(navegacion.recorrido),
        distancia_recorrida=navegacion.distancia_recorrida,
        bloqueadas=tuple(sorted(navegacion.sesion.bloqueadas)),
        costos_coinciden=coinciden, resumen=resumen, historial=tuple(navegacion.historial))
