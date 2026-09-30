"""Aplicación: casos de uso que combinan dominio y algoritmos.

No lee archivos por sí misma: recibe un repositorio de datos (inyección de
dependencias) y devuelve estructuras que la API, el CLI o Unity presentan.
"""

from .analisis import construir_grafo, estadisticas_grafo
from .busqueda import (Ejecucion, EventoBusqueda, MetricasBusqueda, comparar_algoritmos,
                       ejecutar_busqueda)
from .evidencia import consultar_evidencia
from .validacion import validar_dataset
from .verificacion import verificar_benchmark

__all__ = ['consultar_evidencia', 'construir_grafo', 'estadisticas_grafo', 'Ejecucion', 'EventoBusqueda',
           'MetricasBusqueda', 'comparar_algoritmos', 'ejecutar_busqueda',
           'validar_dataset', 'verificar_benchmark']
