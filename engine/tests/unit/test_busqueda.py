"""Caso de uso de ejecución: métricas, traza y validación de la consulta."""

import unittest

from npc_nav.algorithms import ALGORITMOS
from npc_nav.application import comparar_algoritmos, ejecutar_busqueda
from npc_nav.domain import Mapa, SesionNavegacion


class EjecutarBusquedaTests(unittest.TestCase):
    def setUp(self):
        self.sesion = SesionNavegacion(Mapa('abierto.map', ('....', '....', '....')))

    def test_traza_opcional_y_resultados_deterministas(self):
        for clave in ALGORITMOS:
            with self.subTest(algoritmo=clave):
                sin_traza = ejecutar_busqueda(self.sesion, clave, (0, 0), (2, 3))
                con_traza = ejecutar_busqueda(self.sesion, clave, (0, 0), (2, 3), con_traza=True)
                self.assertEqual(sin_traza.traza, ())
                self.assertEqual((sin_traza.ruta, sin_traza.costo),
                                 (con_traza.ruta, con_traza.costo))
                self.assertEqual(con_traza.traza[0].posicion, (0, 0))
                self.assertEqual(con_traza.traza[-1].tipo, 'expandido')
                self.assertEqual(con_traza.traza[-1].posicion, (2, 3))
                expandidos = [e for e in con_traza.traza if e.tipo == 'expandido']
                descubiertos = {e.posicion for e in con_traza.traza if e.tipo == 'frontera'}
                self.assertEqual(len(expandidos), con_traza.metricas.nodos_expandidos)
                self.assertEqual(len(descubiertos), con_traza.metricas.nodos_descubiertos)

    def test_estado_y_version(self):
        ejecucion = ejecutar_busqueda(self.sesion, 'astar', (0, 0), (2, 3))
        self.assertEqual((ejecucion.estado, ejecucion.version_mapa), ('encontrada', 0))
        self.sesion.actualizar_obstaculos(bloquear=((1, 1),))
        self.assertEqual(ejecutar_busqueda(self.sesion, 'astar', (0, 0), (2, 3)).version_mapa, 1)

    def test_sin_ruta(self):
        sesion = SesionNavegacion(Mapa('islas.map', ('.@', '@.')))
        ejecucion = ejecutar_busqueda(sesion, 'dijkstra', (0, 0), (1, 1))
        self.assertEqual((ejecucion.estado, ejecucion.ruta, ejecucion.costo), ('sin_ruta', (), None))

    def test_extremos_invalidos_y_algoritmo_desconocido(self):
        sesion = SesionNavegacion(Mapa('mini.map', ('.@', '..')))
        for inicio, destino in (((0, 1), (1, 1)), ((0, 0), (9, 9))):
            with self.subTest(inicio=inicio, destino=destino), self.assertRaises(ValueError):
                ejecutar_busqueda(sesion, 'astar', inicio, destino)
        with self.assertRaises(ValueError):
            ejecutar_busqueda(sesion, 'dstar', (0, 0), (1, 1))

    def test_comparar_usa_la_misma_consulta(self):
        ejecuciones = comparar_algoritmos(self.sesion, list(ALGORITMOS), (0, 0), (2, 3))
        self.assertEqual([e.algoritmo for e in ejecuciones], list(ALGORITMOS))
        self.assertTrue(all(e.ruta[0] == (0, 0) and e.ruta[-1] == (2, 3) for e in ejecuciones))
