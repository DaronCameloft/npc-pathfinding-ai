"""Lectores del formato Moving AI: entradas dañadas se rechazan antes de buscar."""

import tempfile
import unittest
from pathlib import Path

from npc_nav.infrastructure import leer_escenarios, leer_mapa


class LectoresTests(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.raiz = Path(temporal.name)

    def escribir(self, nombre, texto):
        ruta = self.raiz / nombre
        ruta.write_text(texto, encoding='utf-8')
        return ruta

    def test_mapa_valido(self):
        mapa = leer_mapa(self.escribir('ok.map', 'type octile\nheight 2\nwidth 3\nmap\n.@.\nGT.\n'))
        self.assertEqual((mapa.nombre, mapa.alto, mapa.ancho), ('ok.map', 2, 3))
        self.assertEqual(list(mapa.posiciones_transitables()), [(0, 0), (0, 2), (1, 0), (1, 2)])

    def test_mapa_rechaza_cabecera_dimensiones_filas_y_terreno_invalidos(self):
        casos = ('', 'type grid\nheight 1\nwidth 1\nmap\n.',
                 'type octile\nheight 0\nwidth 1\nmap\n',
                 'type octile\nheight 1\nwidth 2\nmap\n.',
                 'type octile\nheight 1\nwidth 1\nmap\n.\n.',
                 'type octile\nheight 1\nwidth 1\nmap\nX')
        for texto in casos:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                leer_mapa(self.escribir('invalido.map', texto))

    def test_escenario_convierte_xy_en_fila_columna(self):
        for version in ('1', '1.0'):
            caso, = leer_escenarios(self.escribir('caso.scen',
                f'version {version}\n0 mapa.map 5 3 4 1 2 2 2.41421356\n'))
            self.assertEqual(caso.inicio, (1, 4))
            self.assertEqual(caso.destino, (2, 2))

    def test_escenarios_rechazan_version_costos_y_coordenadas_invalidos(self):
        casos = ('version 2\n0 mapa.map 2 2 0 0 1 1 1.414',
                 'version 1\n', 'version 1\n0 mapa.map 2',
                 'version 1\n0 mapa.map 2 2 0 0 1 1 nan',
                 'version 1\n0 mapa.map 2 2 0 0 1 1 inf',
                 'version 1\n0 mapa.map 2 2 0 0 1 1 -1',
                 'version 1\n0 mapa.map 2 2 0 0 2 1 1')
        for texto in casos:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                leer_escenarios(self.escribir('invalido.scen', texto))
