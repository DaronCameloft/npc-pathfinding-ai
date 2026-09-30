/** Contrato de datos con la API del motor. Las posiciones son [fila, columna]. */

export type Posicion = [number, number]

export interface LineaPseudocodigo {
  numero: number
  texto: string
  nivel: number
}

export interface AlgoritmoInfo {
  clave: string
  nombre: string
  garantiza_optimo: boolean
  tecnica: string
  complejidad: string
  referencia: string
  pseudocodigo: LineaPseudocodigo[]
}

export interface MapaResumen {
  nombre: string
  alto: number
  ancho: number
  vertices: number
  escenarios: number
}

export interface MapaDetalle {
  nombre: string
  alto: number
  ancho: number
  filas: string[]
}

export interface Escenario {
  indice: number
  bucket: number
  inicio: Posicion
  destino: Posicion
  optimo: number
}

export interface PaginaEscenarios {
  mapa: string
  total: number
  desde: number
  limite: number
  escenarios: Escenario[]
}

export interface EventoBusqueda {
  tipo: 'frontera' | 'expandido'
  posicion: Posicion
  g: number
  h: number
  padre: Posicion | null
  linea: number
}

export interface MetricasBusqueda {
  nodos_expandidos: number
  nodos_descubiertos: number
  max_frontera: number
  tiempo_ms: number
}

export interface Ejecucion {
  algoritmo: string
  estado: 'encontrada' | 'sin_ruta'
  ruta: Posicion[]
  costo: number | null
  version_mapa: number
  metricas: MetricasBusqueda
  traza: EventoBusqueda[]
}

export interface Consulta {
  mapa: string
  caso?: number
  inicio?: Posicion
  destino?: Posicion
  traza?: boolean
  bloqueadas?: Posicion[]
}
