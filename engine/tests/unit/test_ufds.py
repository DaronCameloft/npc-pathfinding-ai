"""UFDS: uniones, representantes y regiones conectadas."""

import unittest

from npc_nav.algorithms import UFDS, regiones_conectadas


class UFDSTests(unittest.TestCase):
    def test_uniones_y_conteo_de_conjuntos(self):
        ufds = UFDS()
        for x in 'abcde':
            ufds.agregar(x)
        self.assertEqual(ufds.num_conjuntos, 5)
        self.assertTrue(ufds.unir('a', 'b'))
        self.assertTrue(ufds.unir('b', 'c'))
        self.assertFalse(ufds.unir('a', 'c'))
        self.assertTrue(ufds.mismo_conjunto('a', 'c'))
        self.assertFalse(ufds.mismo_conjunto('a', 'd'))
        self.assertEqual(ufds.num_conjuntos, 3)
        self.assertEqual(ufds.tamano[ufds.encontrar('a')], 3)

    def test_regiones_de_una_lista_de_adyacencia(self):
        grafo = {1: [2], 2: [1, 3], 3: [2], 4: [5], 5: [4], 6: []}
        _, tamanos = regiones_conectadas(grafo)
        self.assertEqual(tamanos, [3, 2, 1])
