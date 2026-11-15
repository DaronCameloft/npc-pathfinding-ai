"""Registro en memoria de las navegaciones dinámicas abiertas por los clientes.

D* Lite necesita conservar su estado entre cambios, así que la API guarda cada
`NavegacionDinamica` bajo un identificador. Es estado de proceso: si el servidor
se reinicia (Render se duerme tras ~15 min) las sesiones se pierden y el cliente
recibe 404 y debe crear otra. Se descartan las inactivas y, si hay demasiadas,
la menos usada.
"""

from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from uuid import uuid4

from ..application import NavegacionDinamica


@dataclass
class SesionAbierta:
    id: str
    mapa: str
    navegacion: NavegacionDinamica
    ultimo_uso: float


class RegistroSesiones:
    def __init__(self, *, maximo: int = 64, inactividad_s: float = 30 * 60, reloj=monotonic):
        self._sesiones: OrderedDict[str, SesionAbierta] = OrderedDict()
        self._maximo, self._inactividad, self._reloj = maximo, inactividad_s, reloj
        self.candado = Lock()
        """Las rutas síncronas de FastAPI corren en hilos: una operación a la vez."""

    def __len__(self) -> int:
        return len(self._sesiones)

    def _purgar(self) -> None:
        limite = self._reloj() - self._inactividad
        for clave in [c for c, s in self._sesiones.items() if s.ultimo_uso < limite]:
            del self._sesiones[clave]
        while len(self._sesiones) > self._maximo:
            self._sesiones.popitem(last=False)

    def abrir(self, mapa: str, navegacion: NavegacionDinamica) -> SesionAbierta:
        sesion = SesionAbierta(uuid4().hex, mapa, navegacion, self._reloj())
        self._sesiones[sesion.id] = sesion
        self._purgar()
        return sesion

    def obtener(self, id: str) -> SesionAbierta | None:
        self._purgar()
        sesion = self._sesiones.get(id)
        if sesion is not None:
            sesion.ultimo_uso = self._reloj()
            self._sesiones.move_to_end(id)
        return sesion

    def cerrar(self, id: str) -> bool:
        return self._sesiones.pop(id, None) is not None
