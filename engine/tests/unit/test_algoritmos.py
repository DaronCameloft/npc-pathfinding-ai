"""Contrato común de los algoritmos y optimalidad frente a un oráculo independiente."""

import random
import unittest
from heapq import heappop, heappush
from math import inf, sqrt

from npc_nav.algorithms import ALGORITMOS, astar, bfs, dijkstra, voraz
from npc_nav.domain import Mapa, SesionNavegacion

OPTIMOS = [info for info in ALGORITMOS.values() if info.garantiza_optimo]


def costo_oraculo(sesion, inicio, destino):
    """Dijkstra mínimo escrito aparte, usado solo como referencia de pruebas."""
    cola, costos = [(0.0, inicio)], {inicio: 0.0}
    while cola:
        costo, actual = heappop(cola)
        if costo != costos[actual]:
            continue
        if actual == destino:
            return costo
        for vecino, peso in sesion.vecinos(actual):
            if costo + peso < costos.get(vecino, inf):
                costos[vecino] = costo + peso
                heappush(cola, (costo + peso, vecino))
    return None


def mapas_aleatorios(cantidad=30, lado=6, semilla=20260927):
    rng = random.Random(semilla)
    for numero in range(cantidad):
        filas = [''.join('@' if rng.random() < 0.28 else '.' for _ in range(lado))
                 for _ in range(lado)]
        filas[0], filas[-1] = '.' + filas[0][1:], filas[-1][:-1] + '.'
        yield numero, SesionNavegacion(Mapa(f'aleatorio{numero}.map', tuple(filas)))


class ContratoComunTests(unittest.TestCase):
    """Lo que TODO algoritmo del catálogo debe cumplir."""

    def test_ruta_legal_con_costo_coherente(self):
        for info in ALGORITMOS.values():
            for numero, sesion in mapas_aleatorios():
                with self.subTest(algoritmo=info.clave, mapa=numero):
                    resultado = info.funcion(sesion, (0, 0), (5, 5))
                    esperado = costo_oraculo(sesion, (0, 0), (5, 5))
                    if esperado is None:
                        self.assertFalse(resultado.encontrada)
                        continue
                    self.assertEqual((resultado.ruta[0], resultado.ruta[-1]), ((0, 0), (5, 5)))
                    self.assertAlmostEqual(sesion.costo_ruta(resultado.ruta), resultado.costo)
                    self.assertGreaterEqual(resultado.costo + 1e-9, esperado)

    def test_destino_libre_pero_inaccesible(self):
        sesion = SesionNavegacion(Mapa('islas.map', ('.@', '@.')))
        for info in ALGORITMOS.values():
            with self.subTest(algoritmo=info.clave):
                resultado = info.funcion(sesion, (0, 0), (1, 1))
                self.assertEqual((resultado.ruta, resultado.costo), ((), None))

    def test_origen_igual_a_destino(self):
        sesion = SesionNavegacion(Mapa('uno.map', ('.',)))
        for info in ALGORITMOS.values():
            with self.subTest(algoritmo=info.clave):
                resultado = info.funcion(sesion, (0, 0), (0, 0))
                self.assertEqual((resultado.ruta, resultado.costo), (((0, 0),), 0))

    def test_rodea_muro_sin_cortar_esquinas(self):
        sesion = SesionNavegacion(Mapa('muro.map', ('.@.', '.@.', '...')))
        for info in ALGORITMOS.values():
            with self.subTest(algoritmo=info.clave):
                resultado = info.funcion(sesion, (0, 0), (0, 2))
                self.assertEqual(resultado.costo, 6)
                self.assertEqual(len(resultado.ruta), 7)


class OptimalidadTests(unittest.TestCase):
    def test_algoritmos_optimos_coinciden_con_el_oraculo(self):
        for info in OPTIMOS:
            for numero, sesion in mapas_aleatorios(cantidad=40, lado=8, semilla=7):
                esperado = costo_oraculo(sesion, (0, 0), (7, 7))
                with self.subTest(algoritmo=info.clave, mapa=numero):
                    resultado = info.funcion(sesion, (0, 0), (7, 7))
                    if esperado is None:
                        self.assertFalse(resultado.encontrada)
                    else:
                        self.assertAlmostEqual(resultado.costo, esperado)

    def test_ruta_abierta_con_costo_octil(self):
        sesion = SesionNavegacion(Mapa('abierto.map', ('....', '....', '....')))
        for funcion in (astar, dijkstra):
            with self.subTest(algoritmo=funcion.__name__):
                self.assertAlmostEqual(funcion(sesion, (0, 0), (2, 3)).costo, 1 + 2 * sqrt(2))

    def test_recalculo_respeta_bloqueo_y_liberacion(self):
        sesion = SesionNavegacion(Mapa('abierto.map', ('...', '...', '...')))
        self.assertEqual(astar(sesion, (1, 0), (1, 2)).costo, 2)
        sesion.actualizar_obstaculos(bloquear=((1, 1),))
        modificada = astar(sesion, (1, 0), (1, 2))
        self.assertEqual(modificada.costo, 4)
        self.assertNotIn((1, 1), modificada.ruta)
        sesion.actualizar_obstaculos(liberar=((1, 1),))
        self.assertEqual(astar(sesion, (1, 0), (1, 2)).costo, 2)


class NoOptimosTests(unittest.TestCase):
    """BFS y voraz son líneas base: sus rutas son legales pero pueden costar más."""

    def test_bfs_minimiza_pasos_no_costo(self):
        # BFS encuentra una ruta con el mínimo de pasos, pero usa más diagonales
        # (raíz de 2) que la óptima: cuesta 10.83 frente a 10.
        filas = ('.@..@..',
                 '.@.....',
                 '...@...',
                 '@@.....',
                 '...@.@.')
        sesion = SesionNavegacion(Mapa('pasos.map', filas))
        resultado, optimo = bfs(sesion, (0, 0), (4, 6)), astar(sesion, (0, 0), (4, 6))
        self.assertLessEqual(len(resultado.ruta), len(optimo.ruta))   # menos o igual pasos
        self.assertAlmostEqual(optimo.costo, 10.0)
        self.assertGreater(resultado.costo, optimo.costo + 0.5)       # pero más caro

    def test_voraz_puede_ser_suboptimo(self):
        # La heurística arrastra al voraz hacia el destino por un camino más largo.
        filas = ('.......',
                 '.@.@@.@',
                 '.....@.',
                 '...@.@@',
                 '@......')
        sesion = SesionNavegacion(Mapa('trampa.map', filas))
        resultado, optimo = voraz(sesion, (0, 0), (4, 6)), astar(sesion, (0, 0), (4, 6))
        self.assertAlmostEqual(optimo.costo, 6 + 2 * sqrt(2))
        self.assertAlmostEqual(resultado.costo, 10.0)
        self.assertGreater(resultado.costo, optimo.costo)
