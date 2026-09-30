"""El pseudocódigo del docstring y las líneas que reporta la traza deben coincidir."""

import re
import unittest

from npc_nav.algorithms import ALGORITMOS
from npc_nav.algorithms.pseudocodigo import leer_pseudocodigo
from npc_nav.application import ejecutar_busqueda
from npc_nav.domain import Mapa, SesionNavegacion


class LecturaTests(unittest.TestCase):
    def test_lee_numero_texto_y_sangria(self):
        lineas = leer_pseudocodigo(
            'Titulo\n\nPseudocódigo\n------------\n'
            ' 1. iniciar\n 2. mientras haya nodos:\n 3.     tomar uno\n'
            '10. terminar\n\nPropiedades\n-----------\n- 9. esto no cuenta\n')
        self.assertEqual([(l.numero, l.texto, l.nivel) for l in lineas],
                         [(1, 'iniciar', 0), (2, 'mientras haya nodos:', 0),
                          (3, 'tomar uno', 1), (10, 'terminar', 0)])

    def test_sin_seccion_no_hay_lineas(self):
        self.assertEqual(leer_pseudocodigo('Sin pseudocódigo'), ())


class CatalogoTests(unittest.TestCase):
    def test_cada_algoritmo_tiene_pseudocodigo_numerado_sin_saltos(self):
        for info in ALGORITMOS.values():
            with self.subTest(algoritmo=info.clave):
                numeros = [l.numero for l in info.pseudocodigo]
                self.assertGreaterEqual(len(numeros), 8)
                self.assertEqual(numeros, list(range(1, len(numeros) + 1)))

    def test_la_traza_apunta_a_lineas_que_hacen_lo_que_dicen(self):
        sesion = SesionNavegacion(Mapa('abierto.map', ('.....', '.@@@.', '.....')))
        for info in ALGORITMOS.values():
            texto = {l.numero: l.texto for l in info.pseudocodigo}
            with self.subTest(algoritmo=info.clave):
                traza = ejecutar_busqueda(sesion, info.clave, (0, 0), (2, 4),
                                          con_traza=True).traza
                self.assertTrue(traza)
                for evento in traza:
                    self.assertIn(evento.linea, texto)
                    esperado = r'extraer|desencolar' if evento.tipo == 'expandido' else r'insert|encol'
                    self.assertRegex(texto[evento.linea], esperado)
                self.assertEqual(traza[0].linea, 1)


if __name__ == '__main__':
    unittest.main()
