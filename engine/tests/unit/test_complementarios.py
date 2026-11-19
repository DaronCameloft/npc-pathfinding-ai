"""Kruskal, Edmonds-Karp y mochila 0/1 contrastados con oráculos de fuerza bruta."""

import unittest
from itertools import combinations
from random import Random

from npc_nav.algorithms import COMPLEMENTARIOS, edmonds_karp, kruskal, mochila
from npc_nav.algorithms.ufds import UFDS


class _Grabador:
    def __init__(self):
        self.pasos = []

    def paso(self, linea, **datos):
        self.pasos.append((linea, datos))


def _es_arbol(n, aristas):
    conjuntos = UFDS()
    for v in range(n):
        conjuntos.agregar(v)
    return all(conjuntos.unir(u, v) for u, v, _ in aristas) and conjuntos.num_conjuntos == 1


def _grafo_aleatorio(rnd, n, probabilidad):
    return [(u, v, rnd.randint(1, 20)) for u, v in combinations(range(n), 2)
            if rnd.random() < probabilidad]


class PseudocodigoTests(unittest.TestCase):
    def test_cada_complementario_tiene_pseudocodigo_numerado_sin_saltos(self):
        for info in COMPLEMENTARIOS.values():
            with self.subTest(algoritmo=info.clave):
                numeros = [l.numero for l in info.pseudocodigo]
                self.assertGreaterEqual(len(numeros), 8)
                self.assertEqual(numeros, list(range(1, len(numeros) + 1)))

    def test_los_avisos_apuntan_a_lineas_que_hacen_lo_que_dicen(self):
        texto = {clave: {l.numero: l.texto for l in info.pseudocodigo}
                 for clave, info in COMPLEMENTARIOS.items()}
        grabador = _Grabador()
        kruskal(range(3), [(0, 1, 1), (1, 2, 1), (0, 2, 1)], grabador)
        for linea, datos in grabador.pasos:
            self.assertIn('árbol' if datos['aceptada'] else 'ciclo', texto['kruskal'][linea])
        grabador = _Grabador()
        edmonds_karp({'s': {'t': 1}}, 's', 't', grabador)
        self.assertEqual([linea for linea, _ in grabador.pasos], [8, 9])
        self.assertIn('flujo +=', texto['edmonds_karp'][8])
        self.assertIn('corte', texto['edmonds_karp'][9])
        grabador = _Grabador()
        mochila([1], [1], 1, grabador)
        self.assertIn('llevarlo', texto['mochila'][6])
        self.assertIn('llevar el objeto', texto['mochila'][9])
        self.assertEqual([linea for linea, _ in grabador.pasos], [6, 9])


class KruskalTests(unittest.TestCase):
    def test_coincide_con_el_arbol_minimo_por_fuerza_bruta(self):
        rnd = Random(7)
        for _ in range(40):
            n = rnd.randint(2, 6)
            aristas = _grafo_aleatorio(rnd, n, 0.8)
            arboles = [sum(w for *_, w in sub) for sub in combinations(aristas, n - 1)
                       if _es_arbol(n, sub)]
            resultado = kruskal(range(n), aristas)
            if not arboles:
                self.assertGreater(resultado.componentes, 1)
                continue
            self.assertEqual(resultado.componentes, 1)
            self.assertEqual(len(resultado.arbol), n - 1)
            self.assertTrue(_es_arbol(n, resultado.arbol))
            self.assertEqual(resultado.costo, min(arboles))

    def test_grafo_no_conexo_da_un_bosque(self):
        resultado = kruskal('abcd', [('a', 'b', 2), ('c', 'd', 3)])
        self.assertEqual(resultado.componentes, 2)
        self.assertEqual(resultado.costo, 5)

    def test_descarta_la_arista_que_cierra_un_ciclo(self):
        grabador = _Grabador()
        resultado = kruskal('abcd', [('a', 'b', 1), ('b', 'c', 2), ('a', 'c', 3), ('c', 'd', 4)],
                            grabador)
        self.assertEqual([d['aceptada'] for _, d in grabador.pasos], [True, True, False, True])
        self.assertEqual(resultado.costo, 7)


def _corte_minimo_por_fuerza_bruta(capacidades, nodos, s, t):
    otros = [v for v in nodos if v not in (s, t)]
    mejor = float('inf')
    for k in range(len(otros) + 1):
        for lado in combinations(otros, k):
            lado = {s, *lado}
            mejor = min(mejor, sum(c for u, salientes in capacidades.items() if u in lado
                                   for v, c in salientes.items() if v not in lado))
    return mejor


class EdmondsKarpTests(unittest.TestCase):
    def test_ejemplo_de_cormen(self):
        red = {'s': {'v1': 16, 'v2': 13}, 'v1': {'v3': 12}, 'v2': {'v1': 4, 'v4': 14},
               'v3': {'v2': 9, 't': 20}, 'v4': {'v3': 7, 't': 4}}
        self.assertEqual(edmonds_karp(red, 's', 't').valor, 23)

    def test_flujo_maximo_igual_al_corte_minimo_por_fuerza_bruta(self):
        rnd = Random(11)
        for _ in range(40):
            n = rnd.randint(2, 7)
            red = {}
            for u in range(n):
                for v in range(n):
                    if u != v and (v, u) not in {(a, b) for a in red for b in red[a]} \
                            and rnd.random() < 0.45:
                        red.setdefault(u, {})[v] = rnd.randint(1, 9)
            resultado = edmonds_karp(red, 0, n - 1)
            self.assertEqual(resultado.valor, _corte_minimo_por_fuerza_bruta(red, range(n), 0, n - 1))
            self.assertIn(0, resultado.lado_fuente)
            self.assertNotIn(n - 1, resultado.lado_fuente)
            for (u, v), unidades in resultado.flujo.items():          # capacidad
                self.assertLessEqual(unidades, red[u][v])
            for v in range(1, n - 1):                                  # conservación
                entra = sum(f for (a, b), f in resultado.flujo.items() if b == v)
                sale = sum(f for (a, b), f in resultado.flujo.items() if a == v)
                self.assertEqual(entra, sale)

    def test_sin_camino_el_flujo_es_cero(self):
        resultado = edmonds_karp({'s': {'a': 3}, 'b': {'t': 3}}, 's', 't')
        self.assertEqual(resultado.valor, 0)
        self.assertEqual(resultado.lado_fuente, {'s', 'a'})

    def test_fuente_igual_al_sumidero_es_invalida(self):
        with self.assertRaises(ValueError):
            edmonds_karp({}, 'x', 'x')


class MochilaTests(unittest.TestCase):
    def test_coincide_con_la_fuerza_bruta(self):
        rnd = Random(3)
        for _ in range(60):
            n = rnd.randint(1, 8)
            pesos = [rnd.randint(1, 10) for _ in range(n)]
            valores = [rnd.randint(0, 30) for _ in range(n)]
            capacidad = rnd.randint(0, 30)
            mejor = max(sum(valores[i] for i in sub)
                        for k in range(n + 1) for sub in combinations(range(n), k)
                        if sum(pesos[i] for i in sub) <= capacidad)
            resultado = mochila(pesos, valores, capacidad)
            self.assertEqual(resultado.valor, mejor)
            self.assertEqual(sum(valores[i] for i in resultado.elegidos), mejor)
            self.assertLessEqual(sum(pesos[i] for i in resultado.elegidos), capacidad)
            self.assertEqual(len(resultado.tabla), n + 1)
            self.assertEqual(len(resultado.tabla[0]), capacidad + 1)

    def test_datos_invalidos(self):
        with self.assertRaises(ValueError):
            mochila([1, 2], [3], 5)
        with self.assertRaises(ValueError):
            mochila([1], [3], -1)


if __name__ == '__main__':
    unittest.main()
