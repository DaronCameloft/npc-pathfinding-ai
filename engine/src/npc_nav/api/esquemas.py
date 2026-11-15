"""Modelos de entrada de la API. Las posiciones son [fila, columna]."""

from pydantic import BaseModel, Field, model_validator

Celda = tuple[int, int]


class ConsultaBase(BaseModel):
    mapa: str
    caso: int | None = Field(None, ge=0, description='Índice del escenario del .scen')
    inicio: Celda | None = None
    destino: Celda | None = None
    traza: bool = False
    bloqueadas: list[Celda] = Field(default_factory=list,
                                    description='Celdas bloqueadas para esta petición')

    @model_validator(mode='after')
    def _origen_y_destino(self) -> 'ConsultaBase':
        por_caso = self.caso is not None
        por_extremos = self.inicio is not None and self.destino is not None
        if por_caso == por_extremos:
            raise ValueError('Indique `caso` o bien `inicio` y `destino`, pero no ambos')
        return self


class PeticionBuscar(ConsultaBase):
    algoritmo: str = 'astar'


class PeticionComparar(ConsultaBase):
    algoritmos: list[str] = Field(default_factory=list,
                                  description='Vacío = todos los del catálogo')


class PeticionSesion(ConsultaBase):
    """Abre una navegación dinámica: un NPC y uno o más planificadores sincronizados."""
    algoritmos: list[str] = Field(default_factory=lambda: ['astar', 'dstar_lite'],
                                  description='El primero es el guía: el NPC sigue su ruta')


class CambioObstaculos(BaseModel):
    bloquear: list[Celda] = Field(default_factory=list)
    liberar: list[Celda] = Field(default_factory=list)


class PeticionObstaculos(CambioObstaculos):
    traza: bool = False


class PeticionAvanzar(BaseModel):
    pasos: int = Field(1, ge=0, le=100_000)


class CambioEnPaso(CambioObstaculos):
    paso: int = Field(..., ge=0, description='Movimientos del NPC antes del cambio')


class PeticionSimular(PeticionSesion):
    cambios: list[CambioEnPaso] = Field(default_factory=list, max_length=500)
