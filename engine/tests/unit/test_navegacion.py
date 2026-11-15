"""Navegación dinámica: un NPC, los mismos cambios para A* y D* Lite."""

import unittest
from dataclasses import asdict

from npc_nav.application import CambioProgramado, NavegacionDinamica, simular_navegacion
from npc_nav.domain import Mapa

ABIERTO = Mapa('abierto.map', ('.......',
                               '.......',
                               '.......',
                               '.......',
                               '.......'))


class NavegacionDinamicaTests(unittest.TestCase):
    def test_plan_inicial_igual_para_ambos(self):
        nav = NavegacionDinamica(ABIERTO, (2, 0), (2, 6))
        self.assertEqual(nav.algoritmos, ('astar', 'dstar_lite'))
        costos = {c: p.costo for c, p in nav.vigentes.items()}
        self.assertEqual(costos, {'astar': 6, 'dstar_lite': 6})
        self.assertEqual(nav.ruta_restante()[0], (2, 0))
        self.assertTrue(all(p.motivo == 'inicial' for p in nav.historial))

    def test_avanzar_y_replanificar_desde_la_posicion_actual(self):
        nav = NavegacionDinamica(ABIERTO, (2, 0), (2, 6))
        self.assertEqual(nav.avanzar(2), 2)
        self.assertEqual(nav.posicion, (2, 2))
        self.assertEqual(nav.distancia_recorrida, 2)
        nuevas = nav.cambiar_obstaculos(bloquear=[(1, 3), (2, 3), (3, 3)])
        self.assertEqual([p.algoritmo for p in nuevas], ['astar', 'dstar_lite'])
        for plan in nuevas:
            self.assertEqual((plan.motivo, plan.posicion, plan.ruta[0]), ('obstaculos', (2, 2), (2, 2)))
            self.assertTrue(plan.ruta_afectada)
            self.assertEqual(plan.celdas_cambiadas, ((1, 3), (2, 3), (3, 3)))
        self.assertAlmostEqual(nuevas[0].costo, nuevas[1].costo)
        self.assertEqual(nav.ruta_restante()[0], (2, 2))

    def test_cambio_lejano_no_afecta_la_ruta(self):
        nav = NavegacionDinamica(ABIERTO, (2, 0), (2, 6))
        nuevas = nav.cambiar_obstaculos(bloquear=[(0, 0)])
        self.assertFalse(any(p.ruta_afectada for p in nuevas))
        self.assertEqual(nav.cambiar_obstaculos(bloquear=[(0, 0)]), [])   # sin cambios

    def test_no_bloquea_al_npc_ni_al_destino(self):
        nav = NavegacionDinamica(ABIERTO, (2, 0), (2, 6))
        for celda in ((2, 0), (2, 6)):
            with self.assertRaises(ValueError):
                nav.cambiar_obstaculos(bloquear=[celda])

    def test_destino_encerrado_y_reabierto(self):
        nav = NavegacionDinamica(ABIERTO, (2, 0), (2, 6))
        muro = [(f, 5) for f in range(5)]
        nuevas = nav.cambiar_obstaculos(bloquear=muro)
        self.assertEqual({p.estado for p in nuevas}, {'sin_ruta'})
        self.assertEqual(nav.avanzar(3), 0)              # sin ruta, el NPC espera
        nuevas = nav.cambiar_obstaculos(liberar=[(2, 5)])
        self.assertEqual({p.estado for p in nuevas}, {'encontrada'})

    def test_traza_no_altera_el_estado_de_dstar(self):
        con = NavegacionDinamica(ABIERTO, (2, 0), (2, 6), con_traza=True)
        sin = NavegacionDinamica(ABIERTO, (2, 0), (2, 6))
        for nav in (con, sin):
            nav.avanzar(1)
            nav.cambiar_obstaculos(bloquear=[(2, 3)], con_traza=nav is con)
        for clave in ('astar', 'dstar_lite'):
            a, b = con.vigentes[clave], sin.vigentes[clave]
            self.assertEqual((a.ruta, a.costo, a.metricas.nodos_expandidos),
                             (b.ruta, b.costo, b.metricas.nodos_expandidos))
            self.assertTrue(a.traza)
            expandidos = sum(1 for e in a.traza if e.tipo == 'expandido')
            self.assertEqual(expandidos, a.metricas.nodos_expandidos)

    def test_algoritmos_validos(self):
        with self.assertRaises(ValueError):
            NavegacionDinamica(ABIERTO, (2, 0), (2, 6), algoritmos=[])
        with self.assertRaises(ValueError):
            NavegacionDinamica(ABIERTO, (2, 0), (2, 6), algoritmos=['astar', 'astar'])
        with self.assertRaises(ValueError):
            NavegacionDinamica(ABIERTO, (2, 0), (2, 6), algoritmos=['inexistente'])


class SimulacionTests(unittest.TestCase):
    def test_recorrido_completo_con_cambios_programados(self):
        cambios = [CambioProgramado(2, bloquear=((1, 3), (2, 3), (3, 3))),
                   CambioProgramado(3, liberar=((2, 3),)),
                   CambioProgramado(4, bloquear=((0, 0),))]
        resultado = simular_navegacion(ABIERTO, (2, 0), (2, 6), cambios)
        self.assertTrue(resultado.llegado)
        self.assertTrue(resultado.costos_coinciden)
        self.assertEqual((resultado.recorrido[0], resultado.recorrido[-1]), ((2, 0), (2, 6)))
        self.assertEqual([r.replanificaciones for r in resultado.resumen], [3, 3])
        self.assertEqual(resultado.bloqueadas, ((0, 0), (1, 3), (3, 3)))
        asdict(resultado)   # serializable para la API

    def test_omite_bloqueos_sobre_el_npc(self):
        resultado = simular_navegacion(ABIERTO, (2, 0), (2, 6),
                                       [CambioProgramado(1, bloquear=((2, 1), (0, 6)))])
        self.assertNotIn((2, 1), resultado.bloqueadas)
        self.assertTrue(resultado.llegado)


if __name__ == '__main__':
    unittest.main()
