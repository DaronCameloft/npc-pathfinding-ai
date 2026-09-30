"""Caso de uso: comprobar la integridad del dataset (sin buscar rutas)."""

from ..algorithms.ufds import regiones_conectadas
from ..domain.movimiento import distancia_octil
from ..domain.sesion import SesionNavegacion
from .analisis import construir_grafo


def validar_dataset(repositorio) -> dict:
    """Valida cada par mapa/escenarios de un `RepositorioDataset`.

    Comprueba formato, dimensiones, extremos transitables, que inicio y destino
    estén en la misma región (UFDS) y que el óptimo publicado respete la cota
    octil. Lanza ValueError con el primer problema encontrado.
    """
    mapas = repositorio.listar_mapas()
    if not mapas:
        raise ValueError(f'{repositorio.carpeta}: no contiene mapas')
    if repositorio.listar_escenarios() != mapas:
        raise ValueError('Los mapas y escenarios deben formar pares nombre.map / nombre.map.scen')

    resultados = []
    for nombre in mapas:
        mapa = repositorio.mapa(nombre)
        sesion = SesionNavegacion(mapa)
        grafo = construir_grafo(mapa)
        if not grafo:
            raise ValueError(f'{nombre}: no contiene celdas transitables')
        ufds, regiones = regiones_conectadas(grafo)
        casos = repositorio.escenarios(nombre)
        for indice, caso in enumerate(casos):
            try:
                if (caso.mapa.split('/')[-1] != mapa.nombre
                        or (caso.alto, caso.ancho) != (mapa.alto, mapa.ancho)):
                    raise ValueError('Mapa o dimensiones no coinciden')
                sesion.validar_consulta(caso.inicio, caso.destino)
                if not ufds.mismo_conjunto(caso.inicio, caso.destino):
                    raise ValueError('Los extremos están en componentes distintas')
                if caso.optimo + 1e-6 < distancia_octil(caso.inicio, caso.destino):
                    raise ValueError('El costo de referencia es menor que la distancia octil')
                if caso.inicio == caso.destino and caso.optimo != 0:
                    raise ValueError('Una consulta con extremos iguales debe tener costo cero')
            except ValueError as error:
                raise ValueError(f'{nombre}.map.scen, caso {indice}: {error}') from error
        resultados.append({
            'mapa': mapa.nombre, 'alto': mapa.alto, 'ancho': mapa.ancho,
            'vertices': len(grafo), 'aristas': sum(map(len, grafo.values())) // 2,
            'componentes': len(regiones), 'escenarios': len(casos),
            **repositorio.huellas(nombre),
        })
    return {
        'estado': 'valido',
        'alcance': 'Formato, dimensiones, terreno, costos finitos, conectividad y cota octil. '
                   'No calcula rutas; la optimalidad se comprueba con la verificación.',
        'total_escenarios': sum(m['escenarios'] for m in resultados),
        'mapas': resultados,
    }
