"""Genera las figuras del grafo de la sección 3 del informe TB1.

Tres vistas por mapa:
  1. Vista global: el mapa completo coloreado por terreno. A esta escala dibujar
     cada arista sería ilegible, así que se renderiza como matriz de celdas.
  2. Subgrafo: una ventana pequeña dibujada como grafo explícito, con nodos y
     aristas visibles (azul = cardinal, costo 1; rojo = diagonal, costo raíz de 2).
  3. Regiones conectadas detectadas con UFDS.

Requiere la dependencia opcional: pip install -e ".[figures]"

Uso, desde engine/:
    python tools/tb1/visualizar_grafo.py den011d
    python tools/tb1/visualizar_grafo.py brc100d 22            # ventana de 22x22
    python tools/tb1/visualizar_grafo.py brc100d 100 100 25    # ventana fija
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

from npc_nav.algorithms import regiones_conectadas  # noqa: E402
from npc_nav.application import construir_grafo  # noqa: E402
from npc_nav.domain import TRANSITABLES  # noqa: E402
from npc_nav.infrastructure import RepositorioDataset  # noqa: E402

CARPETA_FIGURAS = Path(__file__).resolve().parents[3] / 'docs' / 'figuras' / 'tb1'

CODIGO = {'.': 0, 'G': 0, 'T': 1, 'S': 2, 'W': 3, '@': 4, 'O': 4}
COLORES = ListedColormap(['#f5f0e6',   # transitable
                          '#3f6b45',   # árboles
                          '#8a7f4a',   # pantano
                          '#3b6b8a',   # agua
                          '#1c1c1c'])  # fuera de límites


def buscar_ventana(celdas, alto, ancho, lado=20, paso=8, objetivo=0.72):
    """Ventana lado x lado cuya proporción de celdas transitables se acerca más a
    `objetivo`. Usa una tabla de sumas acumuladas para contar cada ventana en O(1).
    """
    acum = [[0] * (ancho + 1) for _ in range(alto + 1)]
    for f in range(alto):
        fila_acum, fila_prev = acum[f + 1], acum[f]
        for c in range(ancho):
            fila_acum[c + 1] = (fila_acum[c] + fila_prev[c + 1] - fila_prev[c]
                                + (1 if celdas[f][c] in TRANSITABLES else 0))
    total = lado * lado
    mejor, mejor_dif = (0, 0, 0), 2.0
    for f in range(0, max(1, alto - lado), paso):
        for c in range(0, max(1, ancho - lado), paso):
            n = (acum[f + lado][c + lado] - acum[f][c + lado]
                 - acum[f + lado][c] + acum[f][c])
            dif = abs(n / total - objetivo)
            if dif < mejor_dif:
                mejor, mejor_dif = (f, c, n), dif
    return mejor


def vista_global(mapa, salida):
    matriz = [[CODIGO.get(ch, 4) for ch in fila] for fila in mapa.celdas]
    fig, ax = plt.subplots(figsize=(10, 10 * mapa.alto / mapa.ancho))
    ax.imshow(matriz, cmap=COLORES, vmin=0, vmax=4, interpolation='nearest')
    ax.set_title(f'Mapa completo: {mapa.alto} x {mapa.ancho} celdas', fontsize=11)
    ax.set_xlabel('columna')
    ax.set_ylabel('fila')
    fig.tight_layout()
    fig.savefig(salida, dpi=150)
    plt.close(fig)
    print(f'Guardado: {salida}')


def vista_subgrafo(mapa, grafo, f0, c0, lado, salida):
    f1, c1 = min(f0 + lado, mapa.alto), min(c0 + lado, mapa.ancho)
    fig, ax = plt.subplots(figsize=(8, 8))
    for f in range(f0, f1):
        for c in range(c0, c1):
            if mapa.celdas[f][c] not in TRANSITABLES:
                ax.add_patch(plt.Rectangle((c - 0.5, f - 0.5), 1, 1, color='#3f6b45',
                                           alpha=0.45, linewidth=0))
    dibujadas = set()
    for f in range(f0, f1):
        for c in range(c0, c1):
            for vf, vc in grafo.get((f, c), ()):
                if not (f0 <= vf < f1 and c0 <= vc < c1):
                    continue
                clave = tuple(sorted([(f, c), (vf, vc)]))
                if clave in dibujadas:
                    continue
                dibujadas.add(clave)
                diagonal = vf != f and vc != c
                ax.plot([c, vc], [f, vf], color='#c0392b' if diagonal else '#2c3e50',
                        linewidth=0.7, alpha=0.55, zorder=1)
    nodos = [(f, c) for f in range(f0, f1) for c in range(c0, c1) if (f, c) in grafo]
    ax.scatter([c for _, c in nodos], [f for f, _ in nodos], s=14, color='#1a1a1a', zorder=2)
    ax.set_title(f'Subgrafo: ventana {lado}x{lado} desde ({f0},{c0})\n'
                 f'{len(nodos)} nodos, {len(dibujadas)} aristas '
                 f'(azul = cardinal costo 1, rojo = diagonal costo raíz de 2)', fontsize=10)
    ax.set_xlim(c0 - 1, c1)
    ax.set_ylim(f1, f0 - 1)
    ax.set_aspect('equal')
    ax.set_xlabel('columna')
    ax.set_ylabel('fila')
    fig.tight_layout()
    fig.savefig(salida, dpi=150)
    plt.close(fig)
    print(f'Guardado: {salida}  ({len(nodos)} nodos, {len(dibujadas)} aristas)')


def vista_regiones(mapa, grafo, salida):
    ufds, _ = regiones_conectadas(grafo)
    raices = {}
    matriz = [[-1] * mapa.ancho for _ in range(mapa.alto)]
    for f, c in grafo:
        raiz = ufds.encontrar((f, c))
        matriz[f][c] = raices.setdefault(raiz, len(raices))
    fig, ax = plt.subplots(figsize=(10, 10 * mapa.alto / mapa.ancho))
    ax.imshow(matriz, cmap='tab20', interpolation='nearest')
    ax.set_title(f'Regiones conectadas detectadas con UFDS: {len(raices)}', fontsize=11)
    fig.tight_layout()
    fig.savefig(salida, dpi=150)
    plt.close(fig)
    print(f'Guardado: {salida}  ({len(raices)} regiones)')


def main():
    parser = argparse.ArgumentParser(description='Genera figuras de un mapa Moving AI.')
    parser.add_argument('mapa', help='Nombre del mapa, p. ej. den011d')
    parser.add_argument('ventana', nargs='*', type=int, help='lado, o bien fila columna lado')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    if len(args.ventana) not in (0, 1, 3):
        parser.error('Use solo lado, o bien fila columna lado')

    mapa = RepositorioDataset().mapa(args.mapa)
    grafo = construir_grafo(mapa)
    salida = args.output_dir or CARPETA_FIGURAS / mapa.nombre.removesuffix('.map')
    salida.mkdir(parents=True, exist_ok=True)

    vista_global(mapa, salida / 'figura_grafo_completo.png')
    vista_regiones(mapa, grafo, salida / 'figura_regiones.png')
    if len(args.ventana) == 3:
        f0, c0, lado = args.ventana
    else:
        lado = args.ventana[0] if args.ventana else 20
        f0, c0, n = buscar_ventana(mapa.celdas, mapa.alto, mapa.ancho, lado)
        print(f'Ventana elegida automáticamente: fila {f0}, columna {c0} '
              f'({n} celdas transitables de {lado * lado})')
    vista_subgrafo(mapa, grafo, f0, c0, lado, salida / 'figura_subgrafo.png')


if __name__ == '__main__':
    main()
