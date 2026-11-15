"""D* Lite en los mapas reales: mismo costo que A* y mucho menos trabajo al replanificar."""

import unittest

from npc_nav.algorithms import DStarLite, astar
from npc_nav.application import experimento_dinamico
from npc_nav.domain import SesionNavegacion
from npc_nav.infrastructure import RepositorioDataset


class _Contador:
    def __init__(self):
        self.expandidos = 0

    def frontera(self, *args):
        pass

    def expandido(self, *args):
        self.expandidos += 1


class DStarLiteRealTests(unittest.TestCase):
    def test_bloqueo_en_la_ruta_de_den011d(self):
        repo = RepositorioDataset()
        caso = repo.escenario('den011d', 375)
        sesion = SesionNavegacion(repo.mapa('den011d'))
        planificador = DStarLite(sesion, caso.inicio, caso.destino)
        ruta = planificador.planificar().ruta
        self.assertAlmostEqual(sesion.costo_ruta(ruta), caso.optimo, places=5)

        posicion = ruta[len(ruta) // 10]
        cambiadas = sesion.actualizar_obstaculos(bloquear=(ruta[len(ruta) // 5],))
        incremental, completo = _Contador(), _Contador()
        replan = planificador.replanificar(posicion, cambiadas, incremental)
        referencia = astar(sesion, posicion, caso.destino, completo)
        self.assertAlmostEqual(replan.costo, referencia.costo)
        self.assertLess(incremental.expandidos * 10, completo.expandidos)

    def test_experimento_dinamico_reproducible(self):
        repo = RepositorioDataset()
        a, filas = experimento_dinamico(repo, 'den011d', casos=3, eventos=3, semilla=7)
        b, _ = experimento_dinamico(repo, 'den011d', casos=3, eventos=3, semilla=7)
        self.assertTrue(a['costos_coinciden'])
        self.assertEqual(a['escenarios'], b['escenarios'])
        self.assertEqual(a['planificaciones_comparadas'], b['planificaciones_comparadas'])
        self.assertEqual({f['algoritmo'] for f in filas}, {'astar', 'dstar_lite'})
        self.assertLess(a['proporcion_expandidos_replanificacion'], 1)


if __name__ == '__main__':
    unittest.main()
