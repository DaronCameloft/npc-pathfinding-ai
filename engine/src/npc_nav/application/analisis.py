"""Caso de uso: caracterizar el grafo de un mapa (sección 2 del informe TB1)."""

from collections import Counter

from ..algorithms.ufds import regiones_conectadas
from ..domain.mapa import Mapa, Posicion
from ..domain.sesion import SesionNavegacion

ETIQUETAS_TERRENO = {'.': 'transitable', 'G': 'transitable', '@': 'fuera de límites',
                     'O': 'fuera de límites', 'T': 'árboles', 'S': 'pantano', 'W': 'agua'}


def construir_grafo(mapa: Mapa) -> dict[Posicion, list[Posicion]]:
    """Lista de adyacencia explícita {celda: [vecinos]} del mapa original."""
    sesion = SesionNavegacion(mapa)
    return {posicion: [vecino for vecino, _ in sesion.vecinos(posicion)]
            for posicion in mapa.posiciones_transitables()}


def estadisticas_grafo(mapa: Mapa) -> dict:
    grafo = construir_grafo(mapa)
    vertices = len(grafo)
    aristas = sum(map(len, grafo.values())) // 2        # grafo no dirigido
    _, regiones = regiones_conectadas(grafo)
    return {
        'mapa': mapa.nombre, 'alto': mapa.alto, 'ancho': mapa.ancho,
        'celdas': mapa.alto * mapa.ancho,
        'vertices': vertices, 'aristas': aristas,
        'porcentaje_transitable': 100 * vertices / (mapa.alto * mapa.ancho),
        'grado_promedio': 2 * aristas / vertices if vertices else 0.0,
        'densidad': 2 * aristas / (vertices * (vertices - 1)) if vertices > 1 else 0.0,
        'componentes': len(regiones),
        'tamanos_componentes': regiones,
        'terrenos': dict(Counter(celda for fila in mapa.celdas for celda in fila)),
    }
