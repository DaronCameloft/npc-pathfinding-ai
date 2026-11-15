"""API de navegación dinámica: /simular sin estado y /sesiones con estado (D* Lite)."""

import unittest

try:
    from fastapi.testclient import TestClient
except ImportError:            # instalación sin el extra [api]
    TestClient = None

# den011d, caso 124: el escenario de la demo Arcadia en Unity.
INICIO, DESTINO = [106, 123], [107, 92]


@unittest.skipIf(TestClient is None, 'fastapi no está instalado (extra [api])')
class ApiNavegacionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from npc_nav.api.main import app
        cls.cliente = TestClient(app)

    def abrir(self, **cuerpo):
        respuesta = self.cliente.post('/sesiones', json={'mapa': 'den011d', 'caso': 124, **cuerpo})
        self.assertEqual(respuesta.status_code, 201, respuesta.text)
        return respuesta.json()

    def test_sesion_completa_con_bloqueo_en_la_ruta(self):
        estado = self.abrir()
        self.assertEqual((estado['inicio'], estado['destino']), (INICIO, DESTINO))
        self.assertEqual(estado['guia'], 'astar')
        self.assertEqual([p['motivo'] for p in estado['nuevas']], ['inicial', 'inicial'])
        self.assertAlmostEqual(estado['vigentes']['astar']['costo'], 51.355339, places=5)
        self.assertAlmostEqual(estado['vigentes']['dstar_lite']['costo'], 51.355339, places=5)

        id = estado['id']
        estado = self.cliente.post(f'/sesiones/{id}/avanzar', json={'pasos': 5}).json()
        self.assertEqual(len(estado['recorrido']), 6)
        adelante = estado['ruta_restante'][5]
        estado = self.cliente.post(f'/sesiones/{id}/obstaculos',
                                   json={'bloquear': [adelante], 'traza': True}).json()
        astar, dstar = estado['nuevas']
        self.assertTrue(astar['ruta_afectada'])
        self.assertAlmostEqual(astar['costo'], dstar['costo'])
        self.assertEqual(astar['posicion'], estado['posicion'])
        self.assertNotIn(adelante, dstar['ruta'])
        self.assertLess(dstar['metricas']['nodos_expandidos'], astar['metricas']['nodos_expandidos'])
        self.assertTrue(dstar['traza'])
        self.assertEqual(estado['bloqueadas'], [adelante])

        self.assertEqual(self.cliente.get(f'/sesiones/{id}').json()['version_mapa'], 1)
        self.assertEqual(self.cliente.delete(f'/sesiones/{id}').status_code, 204)
        self.assertEqual(self.cliente.get(f'/sesiones/{id}').status_code, 404)

    def test_errores_de_sesion(self):
        self.assertEqual(self.cliente.get('/sesiones/no-existe').status_code, 404)
        estado = self.abrir(algoritmos=['dstar_lite'])
        respuesta = self.cliente.post(f"/sesiones/{estado['id']}/obstaculos",
                                      json={'bloquear': [estado['posicion']]})
        self.assertEqual(respuesta.status_code, 422)
        respuesta = self.cliente.post('/sesiones', json={'mapa': 'den011d', 'caso': 124,
                                                         'algoritmos': ['xyz']})
        self.assertEqual(respuesta.status_code, 404)

    def test_simular_es_reproducible(self):
        cuerpo = {'mapa': 'den011d', 'caso': 124,
                  'cambios': [{'paso': 4, 'bloquear': [[106, 117], [107, 117], [105, 117]]},
                              {'paso': 10, 'liberar': [[106, 117]]}]}
        a = self.cliente.post('/simular', json=cuerpo).json()
        b = self.cliente.post('/simular', json=cuerpo).json()
        self.assertTrue(a['llegado'])
        self.assertTrue(a['costos_coinciden'])
        self.assertEqual(a['recorrido'], b['recorrido'])
        self.assertEqual(a['recorrido'][0], INICIO)
        self.assertEqual(a['recorrido'][-1], DESTINO)
        self.assertEqual([r['algoritmo'] for r in a['resumen']], ['astar', 'dstar_lite'])
        self.assertEqual({r['replanificaciones'] for r in a['resumen']}, {2})


if __name__ == '__main__':
    unittest.main()
