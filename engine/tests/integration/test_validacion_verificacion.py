"""Validación y verificación sobre datasets pequeños escritos en disco."""

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from npc_nav.application import validar_dataset, verificar_benchmark
from npc_nav.cli.main import main
from npc_nav.infrastructure import RepositorioDataset
from npc_nav.infrastructure.exportadores import guardar_csv, guardar_json


class DatasetTemporal(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.raiz = Path(temporal.name)

    def escribir(self, nombre, texto):
        ruta = self.raiz / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding='utf-8')

    @property
    def repo(self):
        return RepositorioDataset(self.raiz)


class ValidacionTests(DatasetTemporal):
    def test_rechaza_datos_incoherentes(self):
        self.escribir('maps/mini.map', 'type octile\nheight 2\nwidth 2\nmap\n.@\n@.\n')
        for escenario in ('0 otro.map 2 2 0 0 0 0 0',
                          '0 mini.map 3 2 0 0 0 0 0',
                          '0 mini.map 2 2 0 0 1 0 1',
                          '0 mini.map 2 2 0 0 1 1 1.41421356'):
            self.escribir('scenarios/mini.map.scen', f'version 1\n{escenario}\n')
            with self.subTest(escenario=escenario), self.assertRaises(ValueError):
                validar_dataset(self.repo)

    def test_rechaza_cota_de_costo_imposible(self):
        self.escribir('maps/mini.map', 'type octile\nheight 2\nwidth 2\nmap\n..\n..\n')
        self.escribir('scenarios/mini.map.scen', 'version 1\n0 mini.map 2 2 0 0 1 1 1\n')
        with self.assertRaises(ValueError):
            validar_dataset(self.repo)

    def test_rechaza_mapas_sin_escenarios(self):
        self.escribir('maps/mini.map', 'type octile\nheight 1\nwidth 1\nmap\n.\n')
        with self.assertRaises(ValueError):
            validar_dataset(self.repo)


class VerificacionTests(DatasetTemporal):
    def setUp(self):
        super().setUp()
        self.escribir('maps/mini.map', 'type octile\nheight 2\nwidth 2\nmap\n..\n..\n')
        self.escribir('scenarios/mini.map.scen', 'version 1\n0 mini.map 2 2 0 0 1 1 1.41421356\n'
                                                 '0 mini.map 2 2 0 0 1 1 2\n')

    def test_detecta_costo_no_optimo_y_guarda_evidencia(self):
        reporte, filas = verificar_benchmark(self.repo, 'astar')
        self.assertEqual((reporte['correctos'], reporte['fallidos']), (1, 1))
        self.assertEqual(reporte['estado'], 'fallido')
        self.assertEqual(filas[1]['estado'], 'costo_referencia_diferente')
        guardar_json(self.raiz / 'salida/resumen.json', reporte)
        guardar_csv(self.raiz / 'salida/casos.csv', filas)
        self.assertEqual(json.loads((self.raiz / 'salida/resumen.json').read_text())['total_casos'], 2)
        with (self.raiz / 'salida/casos.csv').open(encoding='utf-8', newline='') as archivo:
            self.assertEqual(len(list(csv.DictReader(archivo))), 2)

    def test_tolerancia_invalida(self):
        for tolerancia in (0, -1, float('nan'), float('inf')):
            with self.subTest(tolerancia=tolerancia), self.assertRaises(ValueError):
                verificar_benchmark(self.repo, tolerancia=tolerancia)

    def test_cli_verificar_y_buscar(self):
        salida = self.raiz / 'resultados'
        destino = self.raiz / 'caso.json'
        with redirect_stdout(io.StringIO()):
            codigo_verificar = main(['--data-dir', str(self.raiz), 'verificar',
                                     '--algoritmo', 'dijkstra', '--output-dir', str(salida)])
            codigo_buscar = main(['--data-dir', str(self.raiz), 'buscar', '--mapa', 'mini',
                                  '--traza', '--output', str(destino)])
        self.assertEqual(codigo_verificar, 1)   # el segundo caso tiene un óptimo publicado erróneo
        self.assertTrue((salida / 'resumen.json').exists())
        self.assertEqual(codigo_buscar, 0)
        contenido = json.loads(destino.read_text(encoding='utf-8'))
        self.assertEqual(contenido['resultado']['estado'], 'encontrada')
        self.assertTrue(contenido['resultado']['traza'])
