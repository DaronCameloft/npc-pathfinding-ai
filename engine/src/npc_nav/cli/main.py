"""Línea de comandos del motor.

    npc-nav algoritmos
    npc-nav analizar --mapa den011d
    npc-nav buscar   --mapa den011d --caso 375 --algoritmo astar [--traza] [--output archivo.json]
    npc-nav comparar --mapa den011d --caso 375 [--algoritmos bfs,dijkstra,voraz,astar]
    npc-nav validar  [--output results/validacion_dataset.json]
    npc-nav verificar --algoritmo astar [--output-dir results/astar]

También se puede invocar como `python -m npc_nav ...`.
"""

import argparse
import platform
import sys
from dataclasses import asdict
from pathlib import Path

from .. import algorithms
from ..algorithms.catalogo import ALGORITMOS, obtener
from ..application import (comparar_algoritmos, ejecutar_busqueda, estadisticas_grafo,
                           validar_dataset, verificar_benchmark)
from ..domain.sesion import SesionNavegacion
from ..infrastructure.exportadores import guardar_csv, guardar_json, sha256
from ..infrastructure.repositorio import RepositorioDataset

CARPETA_RESULTADOS = Path(__file__).resolve().parents[3] / 'results'


def _cmd_algoritmos(args, repo):
    for info in ALGORITMOS.values():
        optimo = 'óptimo' if info.garantiza_optimo else 'no óptimo'
        print(f'{info.clave:10} {info.nombre:26} {info.complejidad:11} {optimo:10} {info.tecnica}')


def _cmd_analizar(args, repo):
    datos = estadisticas_grafo(repo.mapa(args.mapa))
    print(f"Mapa:            {datos['mapa']}  ({datos['alto']} x {datos['ancho']} = "
          f"{datos['celdas']:,} celdas)")
    print(f"Vértices:        {datos['vertices']:,}  ({datos['porcentaje_transitable']:.1f}% del mapa)")
    print(f"Aristas:         {datos['aristas']:,}")
    print(f"Grado promedio:  {datos['grado_promedio']:.2f}")
    print(f"Densidad:        {datos['densidad']:.2e}")
    print(f"Componentes:     {datos['componentes']}  (mayor: {datos['tamanos_componentes'][0]:,})")
    print(f"Terrenos:        {datos['terrenos']}")


def _cmd_buscar(args, repo):
    caso = repo.escenario(args.mapa, args.caso)
    sesion = SesionNavegacion(repo.mapa(args.mapa))
    ejecucion = ejecutar_busqueda(sesion, args.algoritmo, caso.inicio, caso.destino,
                                  con_traza=args.traza)
    contenido = {'mapa': sesion.mapa.nombre, 'caso': args.caso,
                 'escenario': asdict(caso), 'resultado': asdict(ejecucion)}
    if args.output:
        guardar_json(args.output, contenido)
        print(f'Guardado en {args.output}: {ejecucion.estado}, costo={ejecucion.costo}, '
              f'eventos={len(ejecucion.traza)}')
    else:
        m = ejecucion.metricas
        print(f'{ejecucion.algoritmo}: {ejecucion.estado}, costo={ejecucion.costo} '
              f'(óptimo publicado {caso.optimo}), pasos={max(0, len(ejecucion.ruta) - 1)}, '
              f'expandidos={m.nodos_expandidos}, tiempo={m.tiempo_ms:.2f} ms')


def _cmd_comparar(args, repo):
    caso = repo.escenario(args.mapa, args.caso)
    sesion = SesionNavegacion(repo.mapa(args.mapa))
    claves = [clave.strip() for clave in args.algoritmos.split(',') if clave.strip()]
    ejecuciones = comparar_algoritmos(sesion, claves, caso.inicio, caso.destino)
    print(f'{args.mapa} caso {args.caso}: óptimo publicado {caso.optimo:.4f}')
    print(f"{'algoritmo':10} {'costo':>10} {'expandidos':>11} {'descubiertos':>13} {'tiempo ms':>10}")
    for e in ejecuciones:
        costo = f'{e.costo:.4f}' if e.costo is not None else '—'
        print(f'{e.algoritmo:10} {costo:>10} {e.metricas.nodos_expandidos:>11} '
              f'{e.metricas.nodos_descubiertos:>13} {e.metricas.tiempo_ms:>10.2f}')


def _cmd_validar(args, repo):
    reporte = validar_dataset(repo)
    if args.output:
        guardar_json(args.output, reporte)
    print(f"Dataset válido: {reporte['total_escenarios']} escenarios en "
          f"{len(reporte['mapas'])} mapas")


def _cmd_verificar(args, repo):
    info = obtener(args.algoritmo)
    reporte, filas = verificar_benchmark(repo, info.clave, tolerancia=args.tolerancia,
                                         progreso=lambda texto: print(texto, flush=True))
    carpeta_algoritmos = Path(algorithms.__file__).parent
    reporte['entorno'] = {'python': platform.python_version(), 'plataforma': platform.platform(),
                          'procesador': platform.processor()}
    reporte['sha256_codigo'] = {
        archivo: sha256(carpeta_algoritmos / archivo)
        for archivo in (f'{info.funcion.__module__.rsplit(".", 1)[-1]}.py', 'contrato.py')}
    salida = Path(args.output_dir or CARPETA_RESULTADOS / info.clave)
    guardar_json(salida / 'resumen.json', reporte)
    guardar_csv(salida / 'casos.csv', filas)
    print(f"Resultado: {reporte['correctos']}/{reporte['total_casos']} correctos; "
          f"{reporte['fallidos']} fallidos. Evidencia en {salida}")
    return 1 if reporte['fallidos'] else 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='npc-nav', description='Motor de navegación de NPCs')
    parser.add_argument('--data-dir', type=Path,
                        help='Carpeta con maps/ y scenarios/ (por defecto engine/data)')
    sub = parser.add_subparsers(dest='comando', required=True)

    sub.add_parser('algoritmos', help='Lista los algoritmos disponibles').set_defaults(
        funcion=_cmd_algoritmos)

    p = sub.add_parser('analizar', help='Estadísticas del grafo de un mapa')
    p.add_argument('--mapa', required=True)
    p.set_defaults(funcion=_cmd_analizar)

    p = sub.add_parser('buscar', help='Ejecuta un algoritmo sobre un escenario')
    p.add_argument('--mapa', required=True)
    p.add_argument('--caso', type=int, default=0, help='Índice del escenario, desde cero')
    p.add_argument('--algoritmo', default='astar', choices=list(ALGORITMOS))
    p.add_argument('--traza', action='store_true', help='Incluir eventos para el dashboard')
    p.add_argument('--output', type=Path)
    p.set_defaults(funcion=_cmd_buscar)

    p = sub.add_parser('comparar', help='Compara algoritmos sobre el mismo escenario')
    p.add_argument('--mapa', required=True)
    p.add_argument('--caso', type=int, default=0)
    p.add_argument('--algoritmos', default=','.join(ALGORITMOS))
    p.set_defaults(funcion=_cmd_comparar)

    p = sub.add_parser('validar', help='Integridad del dataset')
    p.add_argument('--output', type=Path)
    p.set_defaults(funcion=_cmd_validar)

    p = sub.add_parser('verificar', help='Contrasta un algoritmo con los óptimos de los .scen')
    p.add_argument('--algoritmo', default='astar', choices=list(ALGORITMOS))
    p.add_argument('--output-dir', type=Path)
    p.add_argument('--tolerancia', type=float, default=1e-5)
    p.set_defaults(funcion=_cmd_verificar)
    return parser


def main(argv=None) -> int:
    args = construir_parser().parse_args(argv)
    try:
        return args.funcion(args, RepositorioDataset(args.data_dir)) or 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
