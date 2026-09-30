"""Caso de uso: presentar la evidencia de verificación de un algoritmo.

Combina el resumen (`resumen.json`) con los datos por escenario (`casos.csv`) en una estructura
lista para mostrar: cifras globales, tabla por mapa y una nube de puntos costo → nodos expandidos.
Solo lee resultados ya generados por `verificar_benchmark`; no vuelve a ejecutar búsquedas.
"""

from collections import Counter

# Campos del resumen que se exponen tal cual (el resto se recalcula o se descarta).
_CAMPOS = ('estado', 'algoritmo', 'clave_algoritmo', 'garantiza_optimo', 'fecha_utc', 'total_casos',
           'correctos', 'fallidos', 'tolerancia_absoluta', 'criterio', 'medicion', 'entorno',
           'sha256_codigo')


def consultar_evidencia(repositorio, clave: str) -> dict:
    """`repositorio` es un `RepositorioEvidencia`. Lanza FileNotFoundError si no hay evidencia."""
    resumen = repositorio.resumen(clave)
    casos = repositorio.casos(clave)

    nombres = [mapa['mapa'].removesuffix('.map') for mapa in resumen['mapas']]
    indice_mapa = {f'{nombre}.map': i for i, nombre in enumerate(nombres)}
    errores = [c['error_absoluto'] for c in casos if c['error_absoluto'] is not None]

    return {
        **{campo: resumen[campo] for campo in _CAMPOS if campo in resumen},
        'error_maximo': max(errores, default=None),
        'estados': dict(Counter(c['estado'] for c in casos)),
        'mapas': [{**mapa, 'mapa': mapa['mapa'].removesuffix('.map')} for mapa in resumen['mapas']],
        # Series paralelas (más livianas que una lista de objetos): un punto por escenario.
        'puntos': {
            'mapas': nombres,
            'mapa': [indice_mapa[c['mapa']] for c in casos],
            'costo': [round(c['costo_referencia'], 3) for c in casos],
            'expandidos': [c['nodos_expandidos'] for c in casos],
            'tiempo_ms': [round(c['tiempo_ms'], 3) for c in casos],
        },
    }
