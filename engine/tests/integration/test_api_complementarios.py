"""API de los algoritmos complementarios sobre el dataset real."""

import unittest

try:
    from fastapi.testclient import TestClient
except ImportError:            # instalación sin el extra [api]
    TestClient = None


@unittest.skipIf(TestClient is None, 'fastapi no está instalado (extra [api])')
class ApiComplementariosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from npc_nav.api.main import app
        cls.cliente = TestClient(app)

    def test_catalogo_aparte_de_los_algoritmos_de_ruta(self):
        datos = self.cliente.get('/complementarios').json()
        self.assertEqual([a['clave'] for a in datos], ['kruskal', 'edmonds_karp', 'mochila'])
        self.assertTrue(all(a['pseudocodigo'] and a['caso_de_uso'] for a in datos))
        rutas = [a['clave'] for a in self.cliente.get('/algoritmos').json()]
        self.assertNotIn('kruskal', rutas)

    def test_patrullaje_con_puntos_sorteados(self):
        datos = self.cliente.post('/patrullaje', json={'mapa': 'den011d', 'cantidad': 5}).json()
        self.assertEqual(len(datos['puntos']), 5)
        self.assertEqual(len(datos['arbol']), 4)
        self.assertEqual(datos['componentes'], 1)
        self.assertLess(datos['costo_arbol'], datos['costo_candidatas'])
        self.assertAlmostEqual(sum(t['costo'] for t in datos['arbol']), datos['costo_arbol'])

    def test_patrullaje_rechaza_puntos_en_muros(self):
        respuesta = self.cliente.post('/patrullaje', json={'mapa': 'den011d', 'puntos': [[0, 0], [1, 1]]})
        self.assertEqual(respuesta.status_code, 422)

    def test_pasillo_de_den011d(self):
        cuerpo = {'mapa': 'den011d', 'zona': [24, 156, 71, 203], 'direccion': 'vertical'}
        datos = self.cliente.post('/pasillo', json=cuerpo).json()
        self.assertEqual(datos['flujo_maximo'], 3)
        self.assertEqual(len(datos['corte']), 3)
        self.assertEqual(len(datos['caminos']), 3)
        cerrado = self.cliente.post('/pasillo', json={**cuerpo, 'bloqueadas': datos['corte']}).json()
        self.assertEqual(cerrado['flujo_maximo'], 0)

    def test_pasillo_demasiado_grande(self):
        respuesta = self.cliente.post('/pasillo', json={'mapa': 'den011d', 'zona': [0, 0, 100, 100]})
        self.assertEqual(respuesta.status_code, 422)

    def test_botin_de_ejemplo_y_propio(self):
        datos = self.cliente.post('/botin', json={}).json()
        self.assertGreater(datos['optima']['valor'], datos['voraz']['valor'])
        self.assertEqual(len(datos['tabla']), len(datos['objetos']) + 1)
        propio = self.cliente.post('/botin', json={'capacidad': 6, 'objetos': [
            {'nombre': 'a', 'peso': 3, 'valor': 4}, {'nombre': 'b', 'peso': 4, 'valor': 5},
            {'nombre': 'c', 'peso': 2, 'valor': 3}]}).json()
        self.assertEqual(propio['optima']['elegidos'], [1, 2])


if __name__ == '__main__':
    unittest.main()
