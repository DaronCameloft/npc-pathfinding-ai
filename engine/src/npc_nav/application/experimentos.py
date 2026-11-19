"""Caso de uso: experimento dinámico reproducible A* (recálculo completo) frente a D* Lite.

Para cada escenario elegido con la semilla, el NPC avanza por su ruta y en cada
evento ocurre uno de estos cambios (docs/plan.md, «Casos dinámicos»):

- `bloqueo_ruta`: se bloquea una celda de la ruta restante, entre 2 y 15 pasos
  por delante del NPC.
- `pasillo`: se bloquea un bloque de 3×3 centrado en la ruta (cierra un pasillo).
- `lejano`: se bloquea una celda al azar que no está en la ruta (no la afecta).
- `desbloqueo`: se libera un obstáculo puesto antes (la ruta puede acortarse).

Ambos algoritmos reciben los mismos cambios desde la misma posición (ver
`navegacion.py`). En cada evento se registra costo, celdas procesadas y tiempo,
y se comprueba que los dos costos coincidan: así el experimento también valida
D* Lite contra A* sobre el mapa modificado (protocolo de validación, punto 2).
"""

import random
from collections.abc import Callable
from dataclasses import dataclass
from statistics import median

from ..domain.movimiento import distancia_octil
from .navegacion import NavegacionDinamica

TIPOS = ('bloqueo_ruta', 'pasillo', 'lejano', 'desbloqueo')
_PESOS = (3, 2, 2, 1)


@dataclass(frozen=True)
class Evento:
    tipo: str
    bloquear: tuple
    liberar: tuple


def _elegir_evento(rng: random.Random, nav: NavegacionDinamica, transitables: list) -> Evento | None:
    restante = nav.ruta_restante()
    protegidas = {nav.posicion, nav.destino}
    tipo = rng.choices(TIPOS, weights=_PESOS)[0]
    if tipo == 'desbloqueo' and not nav.sesion.bloqueadas:
        tipo = 'bloqueo_ruta'
    if tipo == 'desbloqueo':
        return Evento(tipo, (), (rng.choice(sorted(nav.sesion.bloqueadas)),))
    if tipo == 'lejano':
        en_ruta = set(restante)
        for _ in range(100):
            celda = rng.choice(transitables)
            if celda not in en_ruta and celda not in protegidas and celda not in nav.sesion.bloqueadas:
                return Evento(tipo, (celda,), ())
        return None
    if len(restante) < 4:
        return None
    centro = restante[rng.randint(2, min(15, len(restante) - 2))]
    if tipo == 'bloqueo_ruta':
        celdas = {centro}
    else:
        celdas = {(centro[0] + df, centro[1] + dc) for df in (-1, 0, 1) for dc in (-1, 0, 1)}
    celdas = {c for c in celdas if nav.sesion.mapa.transitable(c)} - protegidas
    return Evento(tipo, tuple(sorted(celdas)), ()) if celdas else None


def experimento_dinamico(repo, mapa: str, *, casos: int = 30, eventos: int = 5,
                         semilla: int = 2026, algoritmos=('astar', 'dstar_lite'),
                         progreso: Callable[[str], None] | None = None) -> tuple[dict, list[dict]]:
    """Devuelve (resumen, filas). Una fila por algoritmo y planificación."""
    rng = random.Random(f'{semilla}:{mapa}')
    escenarios = repo.escenarios(mapa)
    # Rutas largas: la mitad superior por costo óptimo, donde hay espacio para eventos.
    largos = sorted(range(len(escenarios)), key=lambda i: escenarios[i].optimo)[len(escenarios) // 2:]
    elegidos = sorted(rng.sample(largos, min(casos, len(largos))))
    mapa_datos = repo.mapa(mapa)
    transitables = list(mapa_datos.posiciones_transitables())

    filas = []
    for numero, indice in enumerate(elegidos, start=1):
        caso = escenarios[indice]
        nav = NavegacionDinamica(mapa_datos, caso.inicio, caso.destino, algoritmos=algoritmos)
        planes = list(nav.historial)
        tipos = ['inicial'] * len(planes)
        distancias = [0.0] * len(planes)
        for _ in range(eventos):
            restante = nav.ruta_restante()
            if len(restante) > 6:
                nav.avanzar(rng.randint(1, max(1, len(restante) // (eventos + 1))))
            evento = _elegir_evento(rng, nav, transitables)
            if evento is None:
                continue
            nuevas = nav.cambiar_obstaculos(bloquear=evento.bloquear, liberar=evento.liberar)
            celdas = evento.bloquear or evento.liberar
            distancia = min(distancia_octil(nav.posicion, c) for c in celdas)
            planes += nuevas
            tipos += [evento.tipo] * len(nuevas)
            distancias += [distancia] * len(nuevas)

        for orden, (plan, tipo, distancia) in enumerate(zip(planes, tipos, distancias)):
            filas.append({
                'mapa': mapa, 'caso': indice, 'planificacion': orden // len(algoritmos),
                'tipo': tipo, 'algoritmo': plan.algoritmo, 'estado': plan.estado,
                'costo': '' if plan.costo is None else round(plan.costo, 6),
                'celdas_cambiadas': len(plan.celdas_cambiadas),
                'distancia_al_npc': round(distancia, 3), 'ruta_afectada': plan.ruta_afectada,
                'nodos_expandidos': plan.metricas.nodos_expandidos,
                'nodos_descubiertos': plan.metricas.nodos_descubiertos,
                'tiempo_ms': round(plan.metricas.tiempo_ms, 4),
            })
        if progreso:
            progreso(f'{mapa}: {numero}/{len(elegidos)} escenarios')
    return _resumir(mapa, semilla, elegidos, eventos, algoritmos, filas), filas


def _resumir(mapa, semilla, elegidos, eventos, algoritmos, filas) -> dict:
    def grupo(tipo_filtro):
        seleccion = [f for f in filas if tipo_filtro(f['tipo'])]
        por_algoritmo = {}
        for clave in algoritmos:
            propias = [f for f in seleccion if f['algoritmo'] == clave]
            if not propias:
                continue
            por_algoritmo[clave] = {
                'planificaciones': len(propias),
                'mediana_expandidos': median(f['nodos_expandidos'] for f in propias),
                'total_expandidos': sum(f['nodos_expandidos'] for f in propias),
                'mediana_tiempo_ms': round(median(f['tiempo_ms'] for f in propias), 4),
                'total_tiempo_ms': round(sum(f['tiempo_ms'] for f in propias), 3),
            }
        return por_algoritmo

    # Cada planificación de A* debe tener el mismo costo que la de D* Lite.
    pares = {}
    for f in filas:
        pares.setdefault((f['caso'], f['planificacion']), {})[f['algoritmo']] = f['costo']
    discrepancias = [k for k, costos in pares.items()
                     if len({c if c == '' else round(c, 5) for c in costos.values()}) > 1]

    replan = grupo(lambda t: t != 'inicial')
    base, incremental = algoritmos[0], algoritmos[-1]
    proporcion = None
    if base in replan and incremental in replan and replan[base]['total_expandidos']:
        proporcion = round(replan[incremental]['total_expandidos'] / replan[base]['total_expandidos'], 4)
    return {
        'mapa': mapa, 'semilla': semilla, 'escenarios': list(elegidos),
        'eventos_por_escenario': eventos, 'algoritmos': list(algoritmos),
        'planificaciones_comparadas': len(pares),
        'costos_coinciden': not discrepancias, 'discrepancias': discrepancias,
        'inicial': grupo(lambda t: t == 'inicial'),
        'replanificacion': replan,
        'por_tipo': {tipo: grupo(lambda t, tipo=tipo: t == tipo) for tipo in TIPOS},
        'proporcion_expandidos_replanificacion': proporcion,
        'nota': ('proporcion = celdas procesadas por el último algoritmo / el primero, '
                 'sumadas en todas las replanificaciones. Tiempos en ms del motor, '
                 'sin red ni animación.'),
    }
