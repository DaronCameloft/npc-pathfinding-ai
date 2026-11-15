"""Registro de sesiones de la API: expiración por inactividad y límite de sesiones."""

import unittest

try:
    from npc_nav.api.sesiones import RegistroSesiones
except ImportError:            # instalación sin el extra [api]
    RegistroSesiones = None


class Reloj:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


@unittest.skipIf(RegistroSesiones is None, 'fastapi no está instalado (extra [api])')
class RegistroSesionesTests(unittest.TestCase):
    def test_expira_por_inactividad(self):
        reloj = Reloj()
        registro = RegistroSesiones(inactividad_s=10, reloj=reloj)
        sesion = registro.abrir('m', navegacion=None)
        reloj.t = 9
        self.assertIs(registro.obtener(sesion.id), sesion)     # el uso renueva el plazo
        reloj.t = 18
        self.assertIs(registro.obtener(sesion.id), sesion)
        reloj.t = 29
        self.assertIsNone(registro.obtener(sesion.id))

    def test_descarta_la_menos_usada(self):
        registro = RegistroSesiones(maximo=2, reloj=Reloj())
        a, b = registro.abrir('m', None), registro.abrir('m', None)
        registro.obtener(a.id)
        c = registro.abrir('m', None)
        self.assertEqual(len(registro), 2)
        self.assertIsNone(registro.obtener(b.id))
        self.assertIsNotNone(registro.obtener(a.id))
        self.assertTrue(registro.cerrar(c.id))
        self.assertFalse(registro.cerrar(c.id))


if __name__ == '__main__':
    unittest.main()
