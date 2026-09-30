"""Lectura y presentación de la evidencia de verificación."""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from npc_nav.application import consultar_evidencia
from npc_nav.infrastructure import RepositorioEvidencia

RESUMEN = {
    'estado': 'aprobado', 'algoritmo': 'A*', 'clave_algoritmo': 'astar', 'garantiza_optimo': True,
    'fecha_utc': '2026-09-30T00:00:00+00:00', 'total_casos': 3, 'correctos': 3, 'fallidos': 0,
    'tolerancia_absoluta': 1e-5, 'criterio': 'c', 'medicion': 'm',
    'entorno': {'python': '3.13'}, 'sha256_codigo': {'astar.py': 'abc'},
    'mapas': [{'mapa': 'uno.map', 'escenarios': 2}, {'mapa': 'dos.map', 'escenarios': 1}],
}
COLUMNAS = ['mapa', 'indice_caso', 'bucket', 'inicio_fila', 'inicio_columna', 'destino_fila',
            'destino_columna', 'costo_referencia', 'costo_obtenido', 'pasos_ruta', 'error_absoluto',
            'estado', 'nodos_expandidos', 'nodos_descubiertos', 'max_frontera', 'tiempo_ms']


def escribir(carpeta: Path):
    destino = carpeta / 'astar'
    destino.mkdir()
    (destino / 'resumen.json').write_text(json.dumps(RESUMEN), encoding='utf-8')
    filas = [
        ['uno.map', 0, 0, 1, 1, 2, 2, 1.41421356, 1.4142135623, 1, 1e-9, 'ok', 2, 9, 8, 0.05],
        ['uno.map', 1, 0, 1, 1, 5, 1, 4.0, 4.0, 4, 0.0, 'ok', 5, 12, 6, 0.07],
        ['dos.map', 0, 1, 0, 0, 9, 9, 12.7279, 12.7279, 9, 3e-8, 'ok', 20, 40, 15, 0.2],
    ]
    with (destino / 'casos.csv').open('w', newline='', encoding='utf-8') as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(COLUMNAS)
        escritor.writerows(filas)


class EvidenciaTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        escribir(Path(self.temporal.name))
        self.repo = RepositorioEvidencia(self.temporal.name)

    def test_lista_los_algoritmos_con_evidencia(self):
        self.assertEqual(self.repo.algoritmos(), ['astar'])
        self.assertEqual(RepositorioEvidencia(Path(self.temporal.name) / 'no_existe').algoritmos(), [])

    def test_lee_los_casos_con_tipos(self):
        casos = self.repo.casos('astar')
        self.assertEqual(len(casos), 3)
        self.assertIsInstance(casos[0]['nodos_expandidos'], int)
        self.assertAlmostEqual(casos[2]['costo_referencia'], 12.7279)

    def test_sin_evidencia_lanza_error(self):
        with self.assertRaises(FileNotFoundError):
            self.repo.resumen('bfs')
        with self.assertRaises(FileNotFoundError):
            self.repo.resumen('..')

    def test_presenta_cifras_tabla_y_puntos(self):
        datos = consultar_evidencia(self.repo, 'astar')
        self.assertEqual((datos['total_casos'], datos['correctos'], datos['fallidos']), (3, 3, 0))
        self.assertEqual(datos['estados'], {'ok': 3})
        self.assertAlmostEqual(datos['error_maximo'], 3e-8)
        self.assertEqual([m['mapa'] for m in datos['mapas']], ['uno', 'dos'])
        puntos = datos['puntos']
        self.assertEqual(puntos['mapas'], ['uno', 'dos'])
        self.assertEqual(puntos['mapa'], [0, 0, 1])
        self.assertEqual(puntos['expandidos'], [2, 5, 20])
        self.assertEqual(len(puntos['costo']), len(puntos['tiempo_ms']), 3)


if __name__ == '__main__':
    unittest.main()
