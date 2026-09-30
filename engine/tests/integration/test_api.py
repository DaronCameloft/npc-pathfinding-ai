"""API HTTP: contrato de los endpoints sobre el dataset real."""

import unittest

try:
    from fastapi.testclient import TestClient
except ImportError:            # instalación sin el extra [api]
    TestClient = None


@unittest.skipIf(TestClient is None, 'fastapi no está instalado (extra [api])')
class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Fuera del try: un error al importar la API debe fallar, no saltar las pruebas.
        from npc_nav.api.main import app
        cls.cliente = TestClient(app)

    def buscar(self, **cuerpo):
        return self.cliente.post('/buscar', json={'mapa': 'den011d', **cuerpo})

    def test_health(self):
        respuesta = self.cliente.get('/health')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['estado'], 'ok')

    def test_catalogo_de_algoritmos(self):
        datos = self.cliente.get('/algoritmos').json()
        self.assertEqual([a['clave'] for a in datos], ['bfs', 'dijkstra', 'voraz', 'astar'])
        self.assertEqual({a['clave'] for a in datos if a['garantiza_optimo']},
                         {'dijkstra', 'astar'})

    def test_catalogo_incluye_pseudocodigo_numerado(self):
        astar = next(a for a in self.cliente.get('/algoritmos').json() if a['clave'] == 'astar')
        self.assertEqual([l['numero'] for l in astar['pseudocodigo']], list(range(1, 11)))
        self.assertEqual(astar['pseudocodigo'][2]['nivel'], 1)
        self.assertIn('menor f', astar['pseudocodigo'][2]['texto'])

    def test_evidencia_de_verificacion_de_astar(self):
        self.assertIn('astar', [a['clave'] for a in self.cliente.get('/evidencia').json()['algoritmos']])
        datos = self.cliente.get('/evidencia/astar').json()
        self.assertEqual((datos['total_casos'], datos['correctos'], datos['fallidos']), (4200, 4200, 0))
        self.assertLess(datos['error_maximo'], 1e-5)
        self.assertEqual(sum(m['escenarios'] for m in datos['mapas']), 4200)
        self.assertEqual(len(datos['puntos']['costo']), 4200)

    def test_evidencia_inexistente_es_404(self):
        self.assertEqual(self.cliente.get('/evidencia/no_existe').status_code, 404)

    def test_lista_de_mapas(self):
        datos = {m['nombre']: m for m in self.cliente.get('/mapas').json()}
        self.assertEqual(set(datos), {'brc100d', 'brc201d', 'den011d'})
        self.assertEqual(sum(m['vertices'] for m in datos.values()), 71174)
        self.assertEqual(datos['den011d']['escenarios'], 750)

    def test_terreno_del_mapa(self):
        datos = self.cliente.get('/mapas/den011d').json()
        self.assertEqual((datos['alto'], datos['ancho']), (167, 247))
        self.assertEqual(len(datos['filas']), 167)
        self.assertTrue(all(len(fila) == 247 for fila in datos['filas']))

    def test_escenarios_paginados(self):
        datos = self.cliente.get('/mapas/den011d/escenarios',
                                 params={'desde': 375, 'limite': 2}).json()
        self.assertEqual(datos['total'], 750)
        self.assertEqual([e['indice'] for e in datos['escenarios']], [375, 376])
        self.assertEqual(datos['escenarios'][0]['inicio'], [75, 61])
        self.assertAlmostEqual(datos['escenarios'][0]['optimo'], 148.25483398)

    def test_buscar_astar_caso_375(self):
        datos = self.buscar(caso=375, algoritmo='astar').json()
        self.assertEqual(datos['estado'], 'encontrada')
        self.assertAlmostEqual(datos['costo'], 148.2548, places=4)
        self.assertEqual(datos['metricas']['nodos_expandidos'], 2080)
        self.assertEqual(datos['ruta'][0], [75, 61])
        self.assertEqual(datos['ruta'][-1], [128, 175])
        self.assertEqual(datos['traza'], [])

    def test_buscar_con_traza(self):
        datos = self.buscar(caso=375, traza=True).json()
        expandidos = [e for e in datos['traza'] if e['tipo'] == 'expandido']
        self.assertEqual(len(expandidos), datos['metricas']['nodos_expandidos'])
        self.assertEqual(datos['traza'][0]['posicion'], [75, 61])
        lineas = {l['numero'] for l in next(a for a in self.cliente.get('/algoritmos').json()
                                            if a['clave'] == 'astar')['pseudocodigo']}
        self.assertTrue({e['linea'] for e in datos['traza']} <= lineas)
        self.assertEqual({e['linea'] for e in datos['traza']}, {1, 3, 9})

    def test_buscar_por_extremos(self):
        datos = self.buscar(inicio=[75, 61], destino=[128, 175]).json()
        self.assertAlmostEqual(datos['costo'], 148.2548, places=4)

    def test_comparar_los_cuatro_algoritmos(self):
        datos = self.cliente.post('/comparar', json={'mapa': 'den011d', 'caso': 375}).json()
        costos = {e['algoritmo']: e['costo'] for e in datos}
        self.assertEqual(list(costos), ['bfs', 'dijkstra', 'voraz', 'astar'])
        self.assertAlmostEqual(costos['astar'], costos['dijkstra'])
        self.assertGreater(costos['voraz'], costos['astar'] + 1)
        expandidos = {e['algoritmo']: e['metricas']['nodos_expandidos'] for e in datos}
        self.assertLess(expandidos['astar'], expandidos['dijkstra'])

    def test_comparar_un_subconjunto(self):
        datos = self.cliente.post('/comparar', json={
            'mapa': 'den011d', 'caso': 375, 'algoritmos': ['astar', 'voraz']}).json()
        self.assertEqual([e['algoritmo'] for e in datos], ['astar', 'voraz'])

    def test_un_bloqueo_cambia_la_ruta(self):
        base = self.buscar(caso=375).json()
        celda = base['ruta'][40]
        bloqueada = self.buscar(caso=375, bloqueadas=[celda]).json()
        self.assertEqual(bloqueada['estado'], 'encontrada')
        self.assertNotIn(celda, bloqueada['ruta'])
        self.assertGreaterEqual(bloqueada['costo'], base['costo'])
        self.assertEqual(bloqueada['version_mapa'], 1)
        # la API no guarda estado: la siguiente petición sin bloqueos vuelve a la ruta original
        self.assertEqual(self.buscar(caso=375).json()['ruta'], base['ruta'])

    def test_mapa_o_algoritmo_inexistente_es_404(self):
        self.assertEqual(self.cliente.get('/mapas/no_existe').status_code, 404)
        self.assertEqual(self.cliente.get('/mapas/no_existe/escenarios').status_code, 404)
        self.assertEqual(self.buscar(caso=0, algoritmo='no_existe').status_code, 404)
        respuesta = self.cliente.post('/buscar', json={'mapa': 'no_existe', 'caso': 0})
        self.assertEqual(respuesta.status_code, 404)

    def test_consultas_invalidas_son_422_con_mensaje(self):
        respuesta = self.buscar(caso=99999)
        self.assertEqual(respuesta.status_code, 422)
        self.assertIn('fuera del rango', respuesta.json()['detail'])
        respuesta = self.buscar(inicio=[0, 0], destino=[75, 61])
        self.assertEqual(respuesta.status_code, 422)
        self.assertIn('no es una celda transitable', respuesta.json()['detail'])
        respuesta = self.buscar(caso=375, bloqueadas=[[0, 0]])
        self.assertEqual(respuesta.status_code, 422)
        self.assertIn('Obstáculo', respuesta.json()['detail'])

    def test_bloquear_un_extremo_es_422(self):
        respuesta = self.buscar(caso=375, bloqueadas=[[75, 61]])
        self.assertEqual(respuesta.status_code, 422)

    def test_indicar_caso_y_extremos_a_la_vez_es_422(self):
        self.assertEqual(self.buscar(caso=1, inicio=[75, 61], destino=[128, 175])
                         .status_code, 422)
        self.assertEqual(self.buscar().status_code, 422)

    def test_cors_permite_el_dashboard_local(self):
        respuesta = self.cliente.get('/health', headers={'Origin': 'http://localhost:5173'})
        self.assertEqual(respuesta.headers['access-control-allow-origin'],
                         'http://localhost:5173')

    def test_traza_se_comprime(self):
        respuesta = self.cliente.post('/buscar', json={'mapa': 'den011d', 'caso': 375,
                                                       'traza': True},
                                      headers={'Accept-Encoding': 'gzip'})
        self.assertEqual(respuesta.headers.get('content-encoding'), 'gzip')


if __name__ == '__main__':
    unittest.main()
