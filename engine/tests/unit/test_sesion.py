"""Reglas de movimiento y obstáculos dinámicos, con casos comprobables a mano."""

import unittest
from math import inf, sqrt

from npc_nav.domain import Mapa, SesionNavegacion, distancia_octil


class SesionTests(unittest.TestCase):
    def setUp(self):
        self.mapa = Mapa('abierto.map', ('...', '...', '...'))
        self.sesion = SesionNavegacion(self.mapa)

    def test_ocho_movimientos_con_costos_y_simetria(self):
        vecinos = dict(self.sesion.vecinos((1, 1)))
        self.assertEqual(len(vecinos), 8)
        for destino, costo in vecinos.items():
            esperado = sqrt(2) if destino[0] != 1 and destino[1] != 1 else 1
            self.assertEqual(costo, esperado)
            self.assertEqual(self.sesion.costo_movimiento(destino, (1, 1)), costo)

    def test_costo_ruta_no_es_numero_de_pasos(self):
        self.assertAlmostEqual(self.sesion.costo_ruta(((0, 0), (1, 1), (1, 2))), sqrt(2) + 1)
        self.assertEqual(self.sesion.costo_ruta(((1, 1),)), 0)
        for ruta in ((), ((0, 0), (2, 2)), ((0, 0), (0, 0))):
            with self.subTest(ruta=ruta), self.assertRaises(ValueError):
                self.sesion.costo_ruta(ruta)

    def test_limites_y_muro_sin_movimientos(self):
        sesion = SesionNavegacion(Mapa('muro.map', ('.@', '..')))
        self.assertEqual(sesion.vecinos((0, 1)), ())
        self.assertEqual(sesion.vecinos((-1, 0)), ())
        self.assertEqual(sesion.costo_movimiento((0, 0), (0, 1)), inf)
        self.assertEqual(sesion.costo_movimiento((0, 0), (-1, 0)), inf)
        with self.assertRaises(ValueError):
            sesion.validar_consulta((0, 0), (0, 1))

    def test_diagonal_no_atraviesa_esquina(self):
        sesion = SesionNavegacion(Mapa('esquina.map', ('.@', '@.')))
        self.assertEqual(sesion.vecinos((0, 0)), ())

    def test_bloqueo_lateral_invalida_diagonal_y_liberacion_la_recupera(self):
        self.assertEqual(self.sesion.costo_movimiento((0, 0), (1, 1)), sqrt(2))
        self.sesion.actualizar_obstaculos(bloquear=((0, 1),))
        self.assertEqual(self.sesion.costo_movimiento((0, 0), (1, 1)), inf)
        with self.assertRaises(ValueError):
            self.sesion.costo_ruta(((0, 0), (1, 1)))
        self.sesion.actualizar_obstaculos(liberar=((0, 1),))
        self.assertEqual(self.sesion.costo_movimiento((0, 0), (1, 1)), sqrt(2))

    def test_cambios_invalidos_son_atomicos(self):
        for bloquear, liberar in ((((1, 1), (9, 9)), ()), (((1, 1),), ((1, 1),))):
            with self.assertRaises(ValueError):
                self.sesion.actualizar_obstaculos(bloquear=bloquear, liberar=liberar)
            self.assertEqual(self.sesion.bloqueadas, frozenset())
            self.assertEqual(self.sesion.version, 0)

    def test_version_y_celdas_cambiadas(self):
        self.assertEqual(self.sesion.actualizar_obstaculos(bloquear=((1, 1),)), ((1, 1),))
        self.assertEqual(self.sesion.version, 1)
        self.assertEqual(self.sesion.actualizar_obstaculos(bloquear=((1, 1),)), ())
        self.assertEqual(self.sesion.version, 1)
        self.assertEqual(self.sesion.vecinos((1, 1)), ())

    def test_sesiones_no_comparten_obstaculos(self):
        otra = SesionNavegacion(self.mapa)
        self.sesion.actualizar_obstaculos(bloquear=((1, 1),))
        self.assertTrue(otra.transitable((1, 1)))
        self.assertTrue(self.mapa.transitable((1, 1)))

    def test_heuristica_octil_consistente(self):
        destino = (2, 2)
        self.assertAlmostEqual(distancia_octil((0, 0), destino), 2 * sqrt(2))
        self.assertEqual(distancia_octil(destino, destino), 0)
        for origen in self.mapa.posiciones_transitables():
            for vecino, costo in self.sesion.vecinos(origen):
                self.assertLessEqual(distancia_octil(origen, destino),
                                     costo + distancia_octil(vecino, destino) + 1e-12)
