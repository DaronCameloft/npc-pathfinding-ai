import type { EventoBusqueda, Posicion } from '../../core/types'

const CRITERIO: Record<string, string> = {
  astar: 'de menor f = g + h',
  dijkstra: 'de menor costo acumulado g',
  voraz: 'de menor h (la que parece más cercana al destino)',
  bfs: 'más antigua de la cola (FIFO)',
}

const celda = (p: Posicion) => `(${p[0]}, ${p[1]})`
const n2 = (x: number) => x.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

/** Una frase en español que explica el evento actual de la traza. */
export function narrar(algoritmo: string, evento: EventoBusqueda | undefined): string {
  if (!evento) return 'Pulsa reproducir para ver cómo explora el algoritmo, celda por celda.'
  const { posicion: p, g, h, padre } = evento
  if (evento.tipo === 'frontera') {
    return padre
      ? `Descubre ${celda(p)} desde ${celda(padre)}: costo acumulado g = ${n2(g)}. Entra a la frontera.`
      : `El inicio ${celda(p)} entra a la frontera con g = 0.`
  }
  const criterio = CRITERIO[algoritmo] ?? 'siguiente'
  const detalle = algoritmo === 'astar' ? `g = ${n2(g)}, h = ${n2(h)}, f = ${n2(g + h)}` : `g = ${n2(g)}`
  return `Expande ${celda(p)}, la celda ${criterio}: ${detalle}.`
}
