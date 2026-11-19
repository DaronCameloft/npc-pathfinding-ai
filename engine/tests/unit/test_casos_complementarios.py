"""Casos de uso de patrullaje (Kruskal), pasillo (Edmonds-Karp) y botín (mochila)."""

import unittest
from itertools import combinations

from npc_nav.algorithms import astar
from npc_nav.application import (BOTIN_DE_EJEMPLO, Objeto, analizar_pasillo, elegir_botin,
                                 puntos_de_interes, red_de_patrullaje)
from npc_nav.domain import Mapa, SesionNavegacion

# Sala izquierda y sala derecha unidas por una puerta de dos celdas (filas 2 y 3, columna 4).
SALAS = Mapa('salas.map', (
    '.........',
    '....@....',
    '.........',
    '.........',
    '....@....',
    '....@....',
))

ISLAS = Mapa('islas.map', (
    '...@...',
    '...@...',
    '...@...',
))


class PatrullajeTests(unittest.TestCase):
    def test_el_arbol_es_minimo_sobre_los_costos_a_estrella(self):
        puntos = [(0, 0), (5, 0), (0, 8), (5, 8), (2, 4)]
        red = red_de_patrullaje(SALAS, puntos)
        sesion = SesionNavegacion(SALAS)
        costo = {(i, j): astar(sesion, puntos[i], puntos[j]).costo
                 for i, j in combinations(range(len(puntos)), 2)}
        mejor = min(sum(costo[par] for par in sub)
                    for sub in combinations(costo, len(puntos) - 1)
                    if len({v for par in sub for v in par}) == len(puntos)
                    and _conecta(len(puntos), sub))
        self.assertAlmostEqual(red.costo_arbol, mejor)
        self.assertEqual(len(red.arbol), len(puntos) - 1)
        self.assertEqual(red.componentes, 1)
        self.assertEqual(len(red.candidatas), 10)
        self.assertEqual([t.costo for t in red.candidatas], sorted(t.costo for t in red.candidatas))
        for tramo in red.arbol:
            self.assertEqual(tramo.ruta[0], puntos[tramo.desde])
            self.assertEqual(tramo.ruta[-1], puntos[tramo.hasta])
            self.assertAlmostEqual(sesion.costo_ruta(tramo.ruta), tramo.costo)

    def test_puntos_sin_ruta_forman_un_bosque(self):
        red = red_de_patrullaje(ISLAS, [(0, 0), (2, 2), (0, 6)])
        self.assertEqual(red.componentes, 2)
        self.assertEqual(red.sin_ruta, ((0, 2), (1, 2)))
        self.assertEqual(len(red.arbol), 1)

    def test_puntos_invalidos(self):
        for puntos in ([(0, 0)], [(0, 0), (0, 0)], [(0, 0), (1, 4)]):
            with self.subTest(puntos=puntos), self.assertRaises(ValueError):
                red_de_patrullaje(SALAS, puntos)

    def test_el_sorteo_es_determinista_y_cae_en_la_region_mayor(self):
        a = puntos_de_interes(ISLAS, 3, semilla=5)
        self.assertEqual(a, puntos_de_interes(ISLAS, 3, semilla=5))
        self.assertEqual(len(set(a)), 3)
        lado = {p[1] < 3 for p in a}
        self.assertEqual(len(lado), 1)      # las islas miden igual, pero se usa una sola


def _conecta(n, pares):
    from npc_nav.algorithms.ufds import UFDS
    conjuntos = UFDS()
    for v in range(n):
        conjuntos.agregar(v)
    for u, v in pares:
        conjuntos.unir(u, v)
    return conjuntos.num_conjuntos == 1


class PasilloTests(unittest.TestCase):
    def test_la_puerta_limita_el_flujo_y_es_el_corte(self):
        analisis = analizar_pasillo(SALAS, (0, 0, 5, 8), 'horizontal')
        # La columna 4 solo tiene libres (0, 4), (2, 4) y (3, 4).
        self.assertEqual(analisis.flujo_maximo, 3)
        self.assertEqual(len(analisis.corte), analisis.flujo_maximo)
        # Es el corte mínimo más cercano a la fuente: pegado a la puerta, del lado de entrada.
        self.assertTrue({p[1] for p in analisis.corte} <= {3, 4})
        self._caminos_validos(analisis)

    def test_bloquear_el_corte_cierra_el_pasillo(self):
        analisis = analizar_pasillo(SALAS, (0, 0, 5, 8), 'horizontal')
        cerrado = analizar_pasillo(SALAS, (0, 0, 5, 8), 'horizontal', analisis.corte)
        self.assertEqual(cerrado.flujo_maximo, 0)
        self.assertEqual(cerrado.caminos, ())
        self.assertEqual(cerrado.bloqueadas, tuple(sorted(analisis.corte)))

    def test_direccion_vertical(self):
        analisis = analizar_pasillo(SALAS, (0, 0, 5, 3), 'vertical')
        self.assertEqual(analisis.flujo_maximo, 4)          # cuatro columnas libres
        self._caminos_validos(analisis)

    def test_zonas_invalidas(self):
        for zona, direccion in (((0, 0, 9, 9), 'horizontal'), ((0, 0, 5, 0), 'horizontal'),
                                ((0, 0, 5, 8), 'diagonal')):
            with self.subTest(zona=zona), self.assertRaises(ValueError):
                analizar_pasillo(SALAS, zona, direccion)

    def _caminos_validos(self, analisis):
        sesion = SesionNavegacion(SALAS)
        usadas = [celda for camino in analisis.caminos for celda in camino]
        self.assertEqual(len(usadas), len(set(usadas)), 'los caminos comparten celdas')
        self.assertEqual(len(analisis.caminos), analisis.flujo_maximo)
        for camino in analisis.caminos:
            self.assertIn(camino[0], analisis.entradas)
            self.assertIn(camino[-1], analisis.salidas)
            sesion.costo_ruta(camino)       # lanza ValueError si un paso no es un movimiento


class BotinTests(unittest.TestCase):
    def test_el_ejemplo_muestra_que_el_voraz_no_es_optimo(self):
        seleccion = elegir_botin()
        self.assertLessEqual(seleccion.optima.peso, seleccion.capacidad)
        self.assertGreater(seleccion.optima.valor, seleccion.voraz.valor)
        self.assertEqual(seleccion.tabla[-1][-1], seleccion.optima.valor)
        self.assertEqual(len(seleccion.reconstruccion), len(BOTIN_DE_EJEMPLO) + 1)
        self.assertEqual(seleccion.reconstruccion[0], (len(BOTIN_DE_EJEMPLO), seleccion.capacidad))

    def test_objetos_propios(self):
        seleccion = elegir_botin([Objeto('a', 3, 4), Objeto('b', 4, 5), Objeto('c', 2, 3)], 6)
        self.assertEqual(seleccion.optima.elegidos, (1, 2))
        self.assertEqual(seleccion.optima.valor, 8)

    def test_datos_invalidos(self):
        with self.assertRaises(ValueError):
            elegir_botin([], 5)
        with self.assertRaises(ValueError):
            elegir_botin([Objeto('a', 0, 4)], 5)
        with self.assertRaises(ValueError):
            elegir_botin(capacidad=500)


if __name__ == '__main__':
    unittest.main()
