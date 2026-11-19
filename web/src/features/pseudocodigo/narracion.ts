import type { EventoBusqueda, Posicion } from '../../core/types'

const CRITERIO: Record<string, string> = {
  astar: 'de menor f = g + h',
  dijkstra: 'de menor costo acumulado g',
  voraz: 'de menor h (la que parece más cercana al destino)',
  bfs: 'más antigua de la cola (FIFO)',
}

/** D* Lite busca desde la meta: `g` es el costo HASTA la meta y puede ser infinito. */
function narrarDStarLite(evento: EventoBusqueda): string {
  const { posicion: p, g, linea } = evento
  const valor = g === null ? '∞' : n2(g)
  if (evento.tipo === 'frontera') {
    if (linea === 1) return `D* Lite empieza en la meta ${celda(p)}: rhs = 0 y entra a la cola. Busca hacia atrás, hasta el NPC.`
    if (linea === 7) return `${celda(p)} sale con una clave vieja: se reinserta con su clave actual (rhs = ${valor}).`
    return `${celda(p)} queda inconsistente (rhs = ${valor} ≠ g) y entra a la cola.`
  }
  return g === null
    ? `${celda(p)} empeoró: g pasa a ∞ y sus vecinas que dependían de ella se recalculan.`
    : `Extrae ${celda(p)}, la de menor clave, y la hace consistente: g = rhs = ${valor} hasta la meta.`
}

const celda = (p: Posicion) => `(${p[0]}, ${p[1]})`
const n2 = (x: number) => x.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

/** Una frase en español que explica el evento actual de la traza. */
export function narrar(algoritmo: string, evento: EventoBusqueda | undefined): string {
  if (!evento) return 'Pulsa reproducir para ver cómo explora el algoritmo, celda por celda.'
  if (algoritmo === 'dstar_lite') return narrarDStarLite(evento)
  const { posicion: p, h, padre } = evento
  const g = evento.g ?? 0
  if (evento.tipo === 'frontera') {
    return padre
      ? `Descubre ${celda(p)} desde ${celda(padre)}: costo acumulado g = ${n2(g)}. Entra a la frontera.`
      : `El inicio ${celda(p)} entra a la frontera con g = 0.`
  }
  const criterio = CRITERIO[algoritmo] ?? 'siguiente'
  const detalle = algoritmo === 'astar' ? `g = ${n2(g)}, h = ${n2(h)}, f = ${n2(g + h)}` : `g = ${n2(g)}`
  return `Expande ${celda(p)}, la celda ${criterio}: ${detalle}.`
}
