"""D* Lite con estado: tras cada cambio debe dar el costo mínimo del mapa vigente."""

import random
import unittest

from npc_nav.algorithms import DStarLite
from npc_nav.domain import Mapa, SesionNavegacion

from .test_algoritmos import costo_oraculo


def sesion_abierta(alto, ancho, densidad, rng):
    filas = [''.join('@' if rng.random() < densidad else '.' for _ in range(ancho))
             for _ in range(alto)]
    filas[0] = '.' + filas[0][1:]
    filas[-1] = filas[-1][:-1] + '.'
    return SesionNavegacion(Mapa('aleatorio.map', tuple(filas)))


class DStarLiteIncrementalTests(unittest.TestCase):
    def test_bloquear_la_ruta_obliga_a_rodear(self):
        sesion = SesionNavegacion(Mapa('abierto.map', ('...', '...', '...')))
        planificador = DStarLite(sesion, (1, 0), (1, 2))
        self.assertEqual(planificador.planificar().costo, 2)
        cambiadas = sesion.actualizar_obstaculos(bloquear=((1, 1),))
        resultado = planificador.replanificar((1, 0), cambiadas)
        self.assertEqual(resultado.costo, 4)
        self.assertNotIn((1, 1), resultado.ruta)
        cambiadas = sesion.actualizar_obstaculos(liberar=((1, 1),))
        self.assertEqual(planificador.replanificar((1, 0), cambiadas).costo, 2)

    def test_cierre_total_y_reapertura(self):
        sesion = SesionNavegacion(Mapa('pasillo.map', ('.....',)))
        planificador = DStarLite(sesion, (0, 0), (0, 4))
        planificador.planificar()
        cambiadas = sesion.actualizar_obstaculos(bloquear=((0, 2),))
        self.assertFalse(planificador.replanificar((0, 1), cambiadas).encontrada)
        cambiadas = sesion.actualizar_obstaculos(liberar=((0, 2),))
        resultado = planificador.replanificar((0, 1), cambiadas)
        self.assertEqual((resultado.ruta[0], resultado.costo), ((0, 1), 3))

    def test_diagonal_invalidada_por_una_esquina(self):
        # Bloquear (0, 1) prohíbe la diagonal (0, 0) → (1, 1) sin tocar sus extremos.
        sesion = SesionNavegacion(Mapa('esquina.map', ('..', '..')))
        planificador = DStarLite(sesion, (0, 0), (1, 1))
        self.assertAlmostEqual(planificador.planificar().costo, 2 ** 0.5)
        cambiadas = sesion.actualizar_obstaculos(bloquear=((0, 1),))
        self.assertEqual(planificador.replanificar((0, 0), cambiadas).ruta,
                         ((0, 0), (1, 0), (1, 1)))

    def test_secuencias_aleatorias_coinciden_con_el_oraculo(self):
        """El NPC avanza por su ruta y el mapa cambia; cada costo se compara con Dijkstra."""
        rng = random.Random(20261114)
        comprobaciones = 0
        for numero in range(60):
            sesion = sesion_abierta(12, 12, 0.22, rng)
            inicio, meta = (0, 0), (11, 11)
            if costo_oraculo(sesion, inicio, meta) is None:
                continue
            planificador = DStarLite(sesion, inicio, meta)
            resultado = planificador.planificar()
            posicion = inicio
            for cambio in range(8):
                # avanzar unos pasos por la ruta vigente
                if resultado.encontrada:
                    posicion = resultado.ruta[min(rng.randint(0, 3), len(resultado.ruta) - 1)]
                libres = [(f, c) for f in range(12) for c in range(12)
                          if sesion.mapa.transitable((f, c)) and (f, c) not in (posicion, meta)]
                bloquear = set(rng.sample(libres, 3))
                if resultado.encontrada and len(resultado.ruta) > 2:
                    bloquear.add(resultado.ruta[len(resultado.ruta) // 2])
                bloquear -= {posicion, meta}
                liberar = set(rng.sample(sorted(sesion.bloqueadas), min(2, len(sesion.bloqueadas))))
                cambiadas = sesion.actualizar_obstaculos(bloquear=bloquear - liberar, liberar=liberar)
                resultado = planificador.replanificar(posicion, cambiadas)
                esperado = costo_oraculo(sesion, posicion, meta)
                with self.subTest(mapa=numero, cambio=cambio):
                    if esperado is None:
                        self.assertFalse(resultado.encontrada)
                    else:
                        self.assertEqual(resultado.ruta[0], posicion)
                        self.assertEqual(resultado.ruta[-1], meta)
                        self.assertAlmostEqual(sesion.costo_ruta(resultado.ruta), resultado.costo)
                        self.assertAlmostEqual(resultado.costo, esperado)
                comprobaciones += 1
                if posicion == meta:
                    break
        self.assertGreater(comprobaciones, 300)

    def test_clonar_no_comparte_estado(self):
        sesion = SesionNavegacion(Mapa('abierto.map', ('....', '....', '....')))
        original = DStarLite(sesion, (0, 0), (2, 3))
        original.planificar()
        copia = original.clonar()
        cambiadas = sesion.actualizar_obstaculos(bloquear=((1, 1), (1, 2)))
        a = original.replanificar((0, 0), cambiadas)
        b = copia.replanificar((0, 0), cambiadas)
        self.assertEqual((a.ruta, a.costo), (b.ruta, b.costo))
        self.assertIsNot(original.g, copia.g)

    def test_orden_de_uso(self):
        sesion = SesionNavegacion(Mapa('uno.map', ('..',)))
        planificador = DStarLite(sesion, (0, 0), (0, 1))
        with self.assertRaises(RuntimeError):
            planificador.replanificar((0, 0), ())
        planificador.planificar()
        with self.assertRaises(RuntimeError):
            planificador.planificar()


if __name__ == '__main__':
    unittest.main()
