"""Lectura validada del formato Moving AI: mapas octile (.map) y escenarios v1 (.scen).

Formato oficial: https://www.movingai.com/benchmarks/formats.html
Los .scen guardan coordenadas (x, y) = (columna, fila); aquí se convierten a
(fila, columna).
"""

from pathlib import Path

from ..domain.escenario import Escenario
from ..domain.mapa import Mapa


def leer_mapa(ruta: str | Path) -> Mapa:
    ruta = Path(ruta)
    lineas = ruta.read_text(encoding='utf-8-sig').splitlines()
    try:
        if len(lineas) < 4 or lineas[0].split() != ['type', 'octile']:
            raise ValueError('Se requiere una cabecera type octile')
        dimensiones = []
        for linea, clave in zip(lineas[1:3], ('height', 'width')):
            partes = linea.split()
            if len(partes) != 2 or partes[0] != clave:
                raise ValueError(f'Cabecera {clave} inválida')
            dimensiones.append(int(partes[1]))
        alto, ancho = dimensiones
        if alto <= 0 or ancho <= 0 or lineas[3].strip() != 'map':
            raise ValueError('Dimensiones o marcador map inválidos')
        if len(lineas[4:]) != alto:
            raise ValueError(f'Se esperaban {alto} filas de terreno')
        if any(len(fila) != ancho for fila in lineas[4:]):
            raise ValueError(f'Se esperaban {ancho} columnas por fila')
        return Mapa(ruta.name, tuple(lineas[4:]))
    except ValueError as error:
        raise ValueError(f'{ruta}: {error}') from error


def leer_escenarios(ruta: str | Path) -> tuple[Escenario, ...]:
    ruta = Path(ruta)
    lineas = ruta.read_text(encoding='utf-8-sig').splitlines()
    if not lineas or lineas[0].split() not in (['version', '1'], ['version', '1.0']):
        raise ValueError(f'{ruta}: se requiere version 1 o version 1.0')
    casos = []
    for numero, linea in enumerate(lineas[1:], start=2):
        partes = linea.split()
        if not partes:
            continue
        try:
            if len(partes) != 9:
                raise ValueError('Se requieren nueve campos')
            casos.append(Escenario(
                bucket=int(partes[0]), mapa=partes[1],
                ancho=int(partes[2]), alto=int(partes[3]),
                inicio=(int(partes[5]), int(partes[4])),
                destino=(int(partes[7]), int(partes[6])),
                optimo=float(partes[8]),
            ))
        except ValueError as error:
            raise ValueError(f'{ruta}, línea {numero}: {error}') from error
    if not casos:
        raise ValueError(f'{ruta}: no contiene escenarios')
    return tuple(casos)
