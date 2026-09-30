"""Los tres mapas reales reproducen las cifras publicadas en el informe TB1."""

import unittest

from npc_nav.application import estadisticas_grafo, validar_dataset
from npc_nav.infrastructure import RepositorioDataset

# mapa: (alto, ancho, vértices, aristas, componentes, escenarios)
INFORME_TB1 = {
    'den011d': (167, 247, 14506, 52710, 1, 750),
    'brc201d': (388, 391, 25645, 92042, 167, 2090),
    'brc100d': (492, 512, 31023, 115524, 1, 1360),
}


class DatasetRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = RepositorioDataset()

    def test_estadisticas_del_informe(self):
        for nombre, (alto, ancho, vertices, aristas, componentes, _) in INFORME_TB1.items():
            with self.subTest(mapa=nombre):
                datos = estadisticas_grafo(self.repo.mapa(nombre))
                self.assertEqual((datos['alto'], datos['ancho']), (alto, ancho))
                self.assertEqual((datos['vertices'], datos['aristas'], datos['componentes']),
                                 (vertices, aristas, componentes))

    def test_dataset_real_valida_4200_consultas(self):
        reporte = validar_dataset(self.repo)
        self.assertEqual(reporte['total_escenarios'], 4200)
        self.assertEqual({m['mapa']: (m['componentes'], m['escenarios']) for m in reporte['mapas']},
                         {f'{n}.map': (d[4], d[5]) for n, d in INFORME_TB1.items()})

    def test_repositorio_lista_y_normaliza_nombres(self):
        self.assertEqual(self.repo.listar_mapas(), sorted(INFORME_TB1))
        self.assertEqual(self.repo.mapa('den011d.map'), self.repo.mapa('den011d'))
        with self.assertRaises(ValueError):
            self.repo.escenario('den011d', 750)
