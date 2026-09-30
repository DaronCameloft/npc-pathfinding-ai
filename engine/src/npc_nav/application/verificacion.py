"""Caso de uso: verificar un algoritmo contra los óptimos publicados en los .scen."""

from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
from math import ceil, isfinite
from statistics import median

from ..algorithms.catalogo import obtener
from ..domain.sesion import SesionNavegacion
from .busqueda import ejecutar_busqueda
from .validacion import validar_dataset


def _estado_caso(sesion, caso, ejecucion, tolerancia, garantiza_optimo) -> str:
    if ejecucion.estado != 'encontrada':
        return 'sin_ruta'
    if ejecucion.ruta[0] != caso.inicio or ejecucion.ruta[-1] != caso.destino:
        return 'extremos_incorrectos'
    try:
        costo_ruta = sesion.costo_ruta(ejecucion.ruta)
    except ValueError:
        return 'ruta_invalida'
    if abs(costo_ruta - ejecucion.costo) > tolerancia:
        return 'costo_ruta_incorrecto'
    diferencia = ejecucion.costo - caso.optimo
    if abs(diferencia) <= tolerancia:
        return 'ok'
    if diferencia > 0 and not garantiza_optimo:
        return 'suboptima'     # esperado en BFS y voraz: ruta legal pero más cara
    return 'costo_referencia_diferente'


def verificar_benchmark(repositorio, algoritmo: str = 'astar', *, tolerancia: float = 1e-5,
                        progreso: Callable[[str], None] | None = None) -> tuple[dict, list[dict]]:
    """Ejecuta `algoritmo` en todos los escenarios y compara con el óptimo publicado.

    Un algoritmo óptimo aprueba si todos los casos quedan en 'ok'. Uno no óptimo
    aprueba si sus rutas son legales ('ok' o 'suboptima').
    """
    if not isfinite(tolerancia) or tolerancia <= 0:
        raise ValueError('La tolerancia debe ser positiva y finita')
    info = obtener(algoritmo)
    aceptados = {'ok'} if info.garantiza_optimo else {'ok', 'suboptima'}
    integridad = validar_dataset(repositorio)

    filas, resumenes = [], []
    for datos in integridad['mapas']:
        nombre = datos['mapa'].removesuffix('.map')
        sesion = SesionNavegacion(repositorio.mapa(nombre))
        casos = repositorio.escenarios(nombre)
        filas_mapa = []
        for indice, caso in enumerate(casos):
            ejecucion = ejecutar_busqueda(sesion, info.clave, caso.inicio, caso.destino)
            filas_mapa.append({
                'mapa': datos['mapa'], 'indice_caso': indice, 'bucket': caso.bucket,
                'inicio_fila': caso.inicio[0], 'inicio_columna': caso.inicio[1],
                'destino_fila': caso.destino[0], 'destino_columna': caso.destino[1],
                'costo_referencia': caso.optimo, 'costo_obtenido': ejecucion.costo,
                'pasos_ruta': max(0, len(ejecucion.ruta) - 1),
                'error_absoluto': (None if ejecucion.costo is None
                                   else abs(ejecucion.costo - caso.optimo)),
                'estado': _estado_caso(sesion, caso, ejecucion, tolerancia,
                                       info.garantiza_optimo),
                **asdict(ejecucion.metricas),
            })
            if progreso and ((indice + 1) % 100 == 0 or indice + 1 == len(casos)):
                progreso(f'{datos["mapa"]}: {indice + 1}/{len(casos)} casos comprobados')
        tiempos = sorted(f['tiempo_ms'] for f in filas_mapa)
        resumenes.append({
            **datos,
            'correctos': sum(f['estado'] in aceptados for f in filas_mapa),
            'optimos': sum(f['estado'] == 'ok' for f in filas_mapa),
            'fallidos': sum(f['estado'] not in aceptados for f in filas_mapa),
            'error_maximo': max((f['error_absoluto'] for f in filas_mapa
                                 if f['error_absoluto'] is not None), default=None),
            'tiempo_mediana_ms': median(tiempos),
            'tiempo_p95_ms': tiempos[ceil(0.95 * len(tiempos)) - 1],
            'nodos_expandidos_mediana': median(f['nodos_expandidos'] for f in filas_mapa),
        })
        filas.extend(filas_mapa)

    fallidos = sum(m['fallidos'] for m in resumenes)
    reporte = {
        'estado': 'aprobado' if not fallidos else 'fallido',
        'algoritmo': info.nombre, 'clave_algoritmo': info.clave,
        'garantiza_optimo': info.garantiza_optimo,
        'fecha_utc': datetime.now(timezone.utc).isoformat(),
        'total_casos': len(filas), 'correctos': len(filas) - fallidos, 'fallidos': fallidos,
        'tolerancia_absoluta': tolerancia,
        'criterio': 'Ruta legal, extremos correctos y costo coincidente con la referencia '
                    'dentro de la tolerancia (para algoritmos no óptimos basta una ruta legal).',
        'medicion': 'Una ejecución por escenario, sin traza, lectura ni verificación de ruta '
                    'dentro del tiempo medido. Los tiempos son descriptivos: no demuestran '
                    'rendimiento en tiempo real ni ventaja frente a otro algoritmo.',
        'mapas': resumenes,
    }
    return reporte, filas
