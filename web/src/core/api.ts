import type {
  AlgoritmoInfo, Consulta, Ejecucion, Evidencia, MapaDetalle, MapaResumen, PaginaEscenarios,
} from './types'

export const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ErrorApi extends Error {
  readonly estado: number

  constructor(message: string, estado: number) {
    super(message)
    this.estado = estado
  }
}

async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  let respuesta: Response
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, {
      ...init,
      headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    })
  } catch {
    throw new ErrorApi('No se pudo conectar con el motor.', 0)
  }
  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`
    try {
      const cuerpo = await respuesta.json()
      if (typeof cuerpo.detail === 'string') detalle = cuerpo.detail
    } catch {
      /* cuerpo sin JSON */
    }
    throw new ErrorApi(detalle, respuesta.status)
  }
  return respuesta.json() as Promise<T>
}

const enviar = (cuerpo: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(cuerpo) })

export const api = {
  health: () => pedir<{ estado: string; version: string }>('/health'),
  algoritmos: () => pedir<AlgoritmoInfo[]>('/algoritmos'),
  mapas: () => pedir<MapaResumen[]>('/mapas'),
  mapa: (nombre: string) => pedir<MapaDetalle>(`/mapas/${encodeURIComponent(nombre)}`),
  escenarios: (nombre: string, desde = 0, limite = 100) =>
    pedir<PaginaEscenarios>(
      `/mapas/${encodeURIComponent(nombre)}/escenarios?desde=${desde}&limite=${limite}`,
    ),
  buscar: (consulta: Consulta & { algoritmo: string }) =>
    pedir<Ejecucion>('/buscar', enviar(consulta)),
  comparar: (consulta: Consulta & { algoritmos?: string[] }) =>
    pedir<Ejecucion[]>('/comparar', enviar(consulta)),
  evidencia: (clave: string) => pedir<Evidencia>(`/evidencia/${encodeURIComponent(clave)}`),
}
