"""npc_nav — motor de navegación de NPCs sobre mapas Moving AI.

Capas (las dependencias solo apuntan hacia adentro):

    cli/, api/         interfaces: presentan resultados, no contienen lógica
    application/       casos de uso: ejecutar, comparar, validar, verificar
    infrastructure/    lectura del dataset y exportación de evidencia
    algorithms/        BFS, Dijkstra, voraz, A*, UFDS (lo que el equipo expone)
    domain/            mapa, reglas de movimiento y sesión con obstáculos
"""

__version__ = '0.2.0'
