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
  /** Conserva su estado entre cambios del mapa y busca desde la meta hacia el NPC (D* Lite). */
  incremental: boolean
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
  /** null = infinito (D* Lite al invalidar una celda). */
  g: number | null
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

export interface EvidenciaMapa {
  mapa: string
  alto: number
  ancho: number
  vertices: number
  aristas: number
  componentes: number
  escenarios: number
  correctos: number
  optimos: number
  fallidos: number
  error_maximo: number | null
  tiempo_mediana_ms: number
  tiempo_p95_ms: number
  nodos_expandidos_mediana: number
}

/** Resultado de `npc-nav verificar` para un algoritmo. */
export interface Evidencia {
  estado: string
  algoritmo: string
  clave_algoritmo: string
  garantiza_optimo: boolean
  fecha_utc: string
  total_casos: number
  correctos: number
  fallidos: number
  tolerancia_absoluta: number
  criterio: string
  medicion: string
  entorno: { python: string; plataforma: string; procesador: string }
  sha256_codigo: Record<string, string>
  error_maximo: number | null
  estados: Record<string, number>
  mapas: EvidenciaMapa[]
  /** Series paralelas: un punto por escenario. */
  puntos: { mapas: string[]; mapa: number[]; costo: number[]; expandidos: number[]; tiempo_ms: number[] }
}

/* ── Algoritmos complementarios ─────────────────────────────────────────── */

export interface ComplementarioInfo {
  clave: 'kruskal' | 'edmonds_karp' | 'mochila'
  nombre: string
  tecnica: string
  complejidad: string
  referencia: string
  caso_de_uso: string
  pseudocodigo: LineaPseudocodigo[]
}

export interface Tramo {
  desde: number
  hasta: number
  costo: number
  ruta: Posicion[]
}

export interface DecisionKruskal {
  desde: number
  hasta: number
  costo: number
  aceptada: boolean
  linea: number
}

export interface RedPatrullaje {
  mapa: string
  puntos: Posicion[]
  candidatas: Tramo[]
  sin_ruta: [number, number][]
  decisiones: DecisionKruskal[]
  arbol: Tramo[]
  costo_arbol: number
  costo_candidatas: number
  componentes: number
  tiempo_rutas_ms: number
  tiempo_kruskal_ms: number
}

export type Direccion = 'horizontal' | 'vertical'

export interface Aumento {
  celdas: Posicion[]
  flujo: number
}

export interface AnalisisPasillo {
  mapa: string
  zona: [number, number, number, number]
  direccion: Direccion
  entradas: Posicion[]
  salidas: Posicion[]
  celdas: number
  flujo_maximo: number
  caminos: Posicion[][]
  corte: Posicion[]
  aumentos: Aumento[]
  bloqueadas: Posicion[]
  tiempo_ms: number
}

export interface ObjetoBotin {
  nombre: string
  peso: number
  valor: number
}

export interface Carga {
  elegidos: number[]
  peso: number
  valor: number
}

export interface SeleccionBotin {
  objetos: ObjetoBotin[]
  capacidad: number
  optima: Carga
  voraz: Carga
  tabla: number[][]
  reconstruccion: [number, number][]
  tiempo_ms: number
}
