"""Genera web/src/features/inicio/demoNpc.json: una demostración real del motor para la pantalla de inicio.

Un NPC recorre la ruta de A*; cuando aparece un obstáculo replanifica desde donde está.
La web solo reproduce estos datos; no calcula rutas.

    python tools/web/generar_demo.py
"""

import json
from pathlib import Path

from npc_nav.application import ejecutar_busqueda
from npc_nav.domain import Mapa, SesionNavegacion

FILAS = (
    '..............................',
    '......@.........@.............',
    '......@.........@.............',
    '......@...@@@...@.....@@@@....',
    '..........@.....@.....@.......',
    '..........@.....@.............',
    '..@@@@....@...................',
    '..........@.....@@@@@@@@......',
    '......@...@...................',
    '......@...@@@@@@@@@...@.......',
    '......@...............@.......',
    '..........@@@@@@@@@@@@@.......',
    '..@@@@@...@...........@.......',
    '..............................',
)
INICIO, DESTINO = (7, 0), (7, 29)
DESTINO_JSON = Path(__file__).resolve().parents[3] / 'web/src/features/inicio/demoNpc.json'


def compacta(traza):
    return [[e.posicion[0], e.posicion[1], 1 if e.tipo == 'expandido' else 0] for e in traza]


def main():
    sesion = SesionNavegacion(Mapa('demo.map', FILAS))
    primera = ejecutar_busqueda(sesion, 'astar', INICIO, DESTINO, con_traza=True)
    k = int(len(primera.ruta) * 0.45)
    bloqueo = primera.ruta[k + 3]
    sesion.actualizar_obstaculos(bloquear=[bloqueo])
    segunda = ejecutar_busqueda(sesion, 'astar', primera.ruta[k], DESTINO, con_traza=True)
    datos = {
        'filas': list(FILAS), 'inicio': list(INICIO), 'destino': list(DESTINO),
        'primera': {'ruta': [list(p) for p in primera.ruta], 'traza': compacta(primera.traza),
                    'costo': round(primera.costo, 4)},
        'indice_npc': k, 'bloqueo': list(bloqueo),
        'segunda': {'ruta': [list(p) for p in segunda.ruta], 'traza': compacta(segunda.traza),
                    'costo': round(segunda.costo, 4)},
    }
    DESTINO_JSON.parent.mkdir(parents=True, exist_ok=True)
    DESTINO_JSON.write_text(json.dumps(datos, separators=(',', ':')), encoding='utf-8')
    print(f'ruta 1: {len(primera.ruta)} celdas, {len(primera.traza)} eventos | '
          f'bloqueo {bloqueo} | ruta 2: {len(segunda.ruta)} celdas, {len(segunda.traza)} eventos')
    grilla = [list(f) for f in FILAS]
    for f, c in primera.ruta: grilla[f][c] = '1'
    for f, c in segunda.ruta: grilla[f][c] = '2'
    grilla[bloqueo[0]][bloqueo[1]] = 'X'
    print('\n'.join(''.join(f) for f in grilla))


if __name__ == '__main__':
    main()
