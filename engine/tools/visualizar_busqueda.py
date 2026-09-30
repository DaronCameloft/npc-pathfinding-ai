"""Dibuja la exploración de varios algoritmos sobre el mismo escenario.

Azul = celdas expandidas · amarillo = frontera pendiente · rojo = ruta final
● = inicio · ★ = destino

Requiere la dependencia opcional: pip install -e ".[figures]"

Uso, desde engine/:
    python tools/visualizar_busqueda.py den011d 375
    python tools/visualizar_busqueda.py brc100d 1160 --algoritmos voraz,astar
    python tools/visualizar_busqueda.py brc201d 40 --output ../docs/figuras/busqueda.png
"""

import argparse
from math import ceil
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

from npc_nav.algorithms import ALGORITMOS  # noqa: E402
from npc_nav.application import ejecutar_busqueda  # noqa: E402
from npc_nav.domain import SesionNavegacion  # noqa: E402
from npc_nav.infrastructure import RepositorioDataset  # noqa: E402

LIBRE, OBSTACULO, FRONTERA, EXPANDIDO = 0, 1, 2, 3
COLORES = ListedColormap(['#f3efe6', '#2b2b2b', '#f6c46b', '#7fb3d5'])


def pintar(ax, mapa, caso, ejecucion, nombre):
    matriz = [[LIBRE if celda in '.G' else OBSTACULO for celda in fila] for fila in mapa.celdas]
    for evento in ejecucion.traza:                     # primero la frontera...
        if evento.tipo == 'frontera':
            fila, columna = evento.posicion
            matriz[fila][columna] = FRONTERA
    for evento in ejecucion.traza:                     # ...y encima lo expandido
        if evento.tipo == 'expandido':
            fila, columna = evento.posicion
            matriz[fila][columna] = EXPANDIDO
    ax.imshow(matriz, cmap=COLORES, vmin=0, vmax=3, interpolation='nearest')
    if ejecucion.ruta:
        ax.plot([c for _, c in ejecucion.ruta], [f for f, _ in ejecucion.ruta],
                color='#c0392b', linewidth=2.2)
    ax.plot(caso.inicio[1], caso.inicio[0], 'o', color='#27ae60', markersize=10, mec='white')
    ax.plot(caso.destino[1], caso.destino[0], '*', color='#c0392b', markersize=16, mec='white')
    costo = f'{ejecucion.costo:.1f}' if ejecucion.costo is not None else 'sin ruta'
    ax.set_title(f'{nombre}  —  costo {costo}  ·  '
                 f'{ejecucion.metricas.nodos_expandidos:,} nodos expandidos', fontsize=13)
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('mapa', help='Nombre del mapa, p. ej. den011d')
    parser.add_argument('caso', type=int, help='Índice del escenario, desde cero')
    parser.add_argument('--algoritmos', default=','.join(ALGORITMOS))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()

    repo = RepositorioDataset()
    mapa, caso = repo.mapa(args.mapa), repo.escenario(args.mapa, args.caso)
    sesion = SesionNavegacion(mapa)
    claves = [clave.strip() for clave in args.algoritmos.split(',') if clave.strip()]

    columnas = 2 if len(claves) > 1 else 1
    filas = ceil(len(claves) / columnas)
    fig, ejes = plt.subplots(filas, columnas, figsize=(7 * columnas, 5.25 * filas), squeeze=False)
    for ax, clave in zip(ejes.flat, claves):
        ejecucion = ejecutar_busqueda(sesion, clave, caso.inicio, caso.destino, con_traza=True)
        pintar(ax, mapa, caso, ejecucion, ALGORITMOS[clave].nombre)
    for ax in list(ejes.flat)[len(claves):]:
        ax.axis('off')
    fig.suptitle(f'Mapa {args.mapa}, caso {args.caso} (óptimo publicado {caso.optimo:.1f}) · '
                 'azul = expandidos · amarillo = frontera · rojo = ruta · ● inicio · ★ destino',
                 fontsize=12)
    fig.tight_layout()
    salida = args.output or Path(f'comparacion_{args.mapa}_{args.caso}.png')
    salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(salida, dpi=110)
    print(f'Guardado: {salida}')


if __name__ == '__main__':
    main()
