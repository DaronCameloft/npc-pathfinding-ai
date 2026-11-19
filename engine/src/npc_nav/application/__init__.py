"""Aplicación: casos de uso que combinan dominio y algoritmos.

No lee archivos por sí misma: recibe un repositorio de datos (inyección de
dependencias) y devuelve estructuras que la API, el CLI o Unity presentan.
"""

from .analisis import construir_grafo, estadisticas_grafo
from .botin import BOTIN_DE_EJEMPLO, Objeto, SeleccionBotin, elegir_botin
from .busqueda import (Ejecucion, EventoBusqueda, MetricasBusqueda, comparar_algoritmos,
                       ejecutar_busqueda)
from .evidencia import consultar_evidencia
from .experimentos import experimento_dinamico
from .navegacion import (CambioProgramado, NavegacionDinamica, Planificacion, ResultadoSimulacion,
                         ResumenAlgoritmo, resumir, simular_navegacion)
from .pasillo import AnalisisPasillo, analizar_pasillo
from .patrullaje import RedPatrullaje, puntos_de_interes, red_de_patrullaje
from .validacion import validar_dataset
from .verificacion import verificar_benchmark

__all__ = ['BOTIN_DE_EJEMPLO', 'Objeto', 'SeleccionBotin', 'elegir_botin', 'AnalisisPasillo',
           'analizar_pasillo', 'RedPatrullaje', 'puntos_de_interes', 'red_de_patrullaje',
           'CambioProgramado', 'NavegacionDinamica', 'Planificacion', 'ResultadoSimulacion',
           'ResumenAlgoritmo', 'resumir', 'simular_navegacion', 'experimento_dinamico', 'consultar_evidencia', 'construir_grafo', 'estadisticas_grafo', 'Ejecucion', 'EventoBusqueda',
           'MetricasBusqueda', 'comparar_algoritmos', 'ejecutar_busqueda',
           'validar_dataset', 'verificar_benchmark']
