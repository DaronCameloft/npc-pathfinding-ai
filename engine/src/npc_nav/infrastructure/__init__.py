"""Infraestructura: lectura del dataset Moving AI y exportación de resultados."""

from .evidencia import RepositorioEvidencia, carpeta_resultados
from .movingai import leer_escenarios, leer_mapa
from .repositorio import RepositorioDataset, carpeta_datos

__all__ = ['leer_mapa', 'leer_escenarios', 'RepositorioDataset', 'carpeta_datos',
           'RepositorioEvidencia', 'carpeta_resultados']
