"""Pseudocódigo numerado de cada algoritmo, leído de su propio docstring.

El docstring del módulo es la única fuente: el código, el informe y el dashboard
muestran el mismo texto. Se toma la sección «Pseudocódigo», entre su subrayado y
la sección siguiente, y de cada línea numerada se extrae el número, el texto y
la sangría (cada 4 espacios de sangría es un nivel de anidación).
"""

import re
import sys
from dataclasses import dataclass

_LINEA = re.compile(r'^\s*(\d+)\.( +)(\S.*)$')
_ESPACIOS_POR_NIVEL = 4


@dataclass(frozen=True)
class LineaPseudocodigo:
    numero: int
    texto: str
    nivel: int


def leer_pseudocodigo(docstring: str) -> tuple[LineaPseudocodigo, ...]:
    """Extrae las líneas numeradas de la sección «Pseudocódigo» de un docstring."""
    lineas, dentro = [], False
    for linea in docstring.splitlines():
        if linea.strip() == 'Pseudocódigo':
            dentro = True
            continue
        if not dentro or set(linea.strip()) == {'-'} or not linea.strip():
            continue
        if linea.strip() == 'Propiedades':
            break
        encontrada = _LINEA.match(linea)
        if encontrada:
            numero, espacios, texto = encontrada.groups()
            lineas.append(LineaPseudocodigo(int(numero), texto.rstrip(),
                                            (len(espacios) - 1) // _ESPACIOS_POR_NIVEL))
    return tuple(lineas)


def pseudocodigo_de(funcion) -> tuple[LineaPseudocodigo, ...]:
    """Pseudocódigo del módulo en el que está definida `funcion`."""
    return leer_pseudocodigo(sys.modules[funcion.__module__].__doc__ or '')
