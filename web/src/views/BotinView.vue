<script setup lang="ts">
/**
 * Mochila 0/1: el motor llena la tabla de programación dinámica y elige el botín;
 * aquí se muestra la tabla fila por fila, la reconstrucción y el contraste con el voraz.
 */
import { computed, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { api, ErrorApi } from '../core/api'
import { cargarComplementarios, motor } from '../core/motor'
import type { ComplementarioInfo, ObjetoBotin, SeleccionBotin } from '../core/types'
import PseudocodePanel from '../features/pseudocodigo/PseudocodePanel.vue'
import PasoAPaso from '../features/reproduccion/PasoAPaso.vue'
import { usePasos } from '../features/reproduccion/usePasos'
import AnimatedNumber from '../shared/AnimatedNumber.vue'
import Icon from '../shared/Icon.vue'

const MAX_OBJETOS = 25
const capacidad = ref(20)
const objetos = ref<ObjetoBotin[]>([])
const seleccion = shallowRef<SeleccionBotin | null>(null)
const info = shallowRef<ComplementarioInfo | null>(null)
const cargando = ref(true)
const error = ref('')
let ticket = 0
let espera = 0

const n = computed(() => seleccion.value?.objetos.length ?? 0)
/** Un paso por fila de la tabla y uno más para la reconstrucción. */
const pasos = usePasos(computed(() => (seleccion.value ? n.value + 1 : 0)), 650)

async function calcular(ejemplo = false) {
  const mio = ++ticket
  cargando.value = true
  error.value = ''
  try {
    const [resultado, catalogo] = await Promise.all([
      api.botin(ejemplo ? { capacidad: capacidad.value } : { capacidad: capacidad.value, objetos: objetos.value }),
      cargarComplementarios(),
    ])
    if (mio !== ticket) return
    info.value = catalogo.find((c) => c.clave === 'mochila') ?? null
    seleccion.value = resultado
    if (ejemplo) objetos.value = resultado.objetos.map((o) => ({ ...o }))
    pasos.reiniciar()
    pasos.reproducir()
  } catch (e) {
    if (mio !== ticket) return
    error.value = e instanceof ErrorApi ? e.message : 'Ocurrió un error inesperado.'
  } finally {
    if (mio === ticket) cargando.value = false
  }
}

/** Los cambios en la lista se envían al motor tras una pausa breve. */
function programar() {
  window.clearTimeout(espera)
  espera = window.setTimeout(() => {
    const validos = objetos.value.every((o) => o.nombre.trim() && o.peso >= 1 && o.peso <= 100 && o.valor >= 0)
    if (validos && objetos.value.length) void calcular()
  }, 450)
}
onBeforeUnmount(() => window.clearTimeout(espera))

function agregar() {
  if (objetos.value.length >= MAX_OBJETOS) return
  objetos.value.push({ nombre: `Objeto ${objetos.value.length + 1}`, peso: 3, valor: 10 })
  programar()
}
function quitar(i: number) {
  if (objetos.value.length <= 1) return
  objetos.value.splice(i, 1)
  programar()
}
function restaurar() {
  capacidad.value = 20
  void calcular(true)
}

const tabla = computed(() => seleccion.value?.tabla ?? [])
const maximo = computed(() => Math.max(1, ...(tabla.value[tabla.value.length - 1] ?? [1])))
const filasVisibles = computed(() => Math.min(pasos.indice.value, n.value))
const reconstruyendo = computed(() => !!seleccion.value && pasos.indice.value > n.value)
const enCamino = computed(() => {
  const s = new Set<string>()
  if (reconstruyendo.value) for (const [i, c] of seleccion.value!.reconstruccion) s.add(`${i},${c}`)
  return s
})
const mostrarNumeros = computed(() => (seleccion.value?.capacidad ?? 0) <= 30)

function estiloCelda(i: number, c: number) {
  if (i > filasVisibles.value) return { background: 'transparent' }
  const v = tabla.value[i][c] / maximo.value
  return { background: `rgba(106, 63, 216, ${0.05 + v * 0.5})`, color: v > 0.62 ? '#fff' : 'var(--ink-2)' }
}
const llevado = (i: number, c: number) => i > 0 && i <= filasVisibles.value && tabla.value[i][c] !== tabla.value[i - 1][c]

const elegidosPD = computed(() => new Set(seleccion.value?.optima.elegidos ?? []))
const elegidosVoraz = computed(() => new Set(seleccion.value?.voraz.elegidos ?? []))

const lineaActiva = computed(() => {
  if (!seleccion.value) return 0
  if (pasos.indice.value === 0) return 1
  if (pasos.terminada.value) return 10
  return reconstruyendo.value ? 9 : 6
})
const conteos = computed(() => {
  const c: Record<number, number> = {}
  const s = seleccion.value
  if (!s || pasos.indice.value === 0) return c
  const filas = filasVisibles.value
  const W = s.capacidad + 1
  c[1] = 1
  c[2] = filas
  c[3] = filas * W
  c[4] = filas * W
  let llevados = 0
  for (let i = 1; i <= filas; i++) for (let k = 0; k < W; k++) if (s.tabla[i][k] !== s.tabla[i - 1][k]) llevados++
  c[5] = filas * W
  c[6] = llevados
  if (reconstruyendo.value) {
    c[7] = 1
    c[8] = s.objetos.length
    c[9] = s.optima.elegidos.length
    c[10] = 1
  }
  return c
})

const narracion = computed(() => {
  const s = seleccion.value
  if (!s) return ''
  if (pasos.indice.value === 0) return `Fila 0: sin objetos, el mejor valor es 0 para cualquier capacidad de 0 a ${s.capacidad}.`
  if (reconstruyendo.value) {
    return `Reconstrucción desde la esquina (${s.objetos.length}, ${s.capacidad}): donde el valor cambia respecto a la fila de arriba, el objeto se lleva y se resta su peso. Botín óptimo: ${s.optima.valor} de oro con ${s.optima.peso} de ${s.capacidad} kg.`
  }
  const i = filasVisibles.value
  const o = s.objetos[i - 1]
  return `Fila ${i} — ${o.nombre} (${o.peso} kg, ${o.valor} de oro): para cada capacidad c se elige el mayor entre no llevarlo (la celda de arriba) y llevarlo (${o.valor} + la celda de arriba ${o.peso} columnas a la izquierda). Las celdas con punto lo llevan.`
})

const diferencia = computed(() => (seleccion.value ? seleccion.value.optima.valor - seleccion.value.voraz.valor : 0))

onMounted(() => calcular(true))
</script>

<template>
  <section class="lab">
    <header class="lab-cabecera rise" style="--i: 0">
      <div>
        <h1 class="display pagina-titulo">Botín <em>con programación dinámica</em></h1>
        <p class="pagina-sub">Mochila 0/1: qué objetos carga el NPC sin pasar su peso máximo. La tabla guarda la mejor respuesta de cada subproblema.</p>
      </div>
      <label class="capacidad">
        <span class="eyebrow">Capacidad</span>
        <input v-model.number="capacidad" type="range" min="1" max="60" @change="programar" />
        <strong class="num">{{ capacidad }} kg</strong>
      </label>
    </header>

    <div class="lab-cuerpo">
      <article class="card lab-principal rise" style="--i: 1">
        <div class="lab-barra">
          <PasoAPaso :pasos="pasos" :total="n + 1" etiqueta="Fila" />
          <span class="lab-pista">tabla[i][c] = mejor valor con los i primeros objetos y capacidad c</span>
        </div>

        <div class="lab-lienzo tabla-marco">
          <div v-if="seleccion" class="tabla" :style="{ gridTemplateColumns: `minmax(120px, 160px) repeat(${seleccion.capacidad + 1}, minmax(0, 1fr))` }">
            <span class="esquina">objeto \ c</span>
            <span v-for="c in seleccion.capacidad + 1" :key="`c${c}`" class="encabezado num">{{ mostrarNumeros || (c - 1) % 5 === 0 ? c - 1 : '' }}</span>
            <template v-for="(fila, i) in tabla" :key="i">
              <span class="rotulo" :class="{ activa: i === filasVisibles && !reconstruyendo, elegido: reconstruyendo && i > 0 && elegidosPD.has(i - 1) }">
                <i class="num">{{ i }}</i>{{ i === 0 ? 'sin objetos' : seleccion.objetos[i - 1].nombre }}
              </span>
              <span
                v-for="(valor, c) in fila"
                :key="c"
                class="celda num"
                :class="{ camino: enCamino.has(`${i},${c}`), lleva: llevado(i, c) }"
                :style="estiloCelda(i, c)"
                :title="`tabla[${i}][${c}] = ${valor}`"
              >{{ mostrarNumeros && i <= filasVisibles ? valor : '' }}</span>
            </template>
          </div>
          <Transition name="lab-fundido">
            <div v-if="cargando" class="lab-velo">
              <span class="lab-spinner" />{{ motor.estado === 'listo' ? 'Llenando la tabla…' : 'Despertando el motor…' }}
            </div>
          </Transition>
          <Transition name="lab-fundido">
            <div v-if="error" class="lab-error glass" role="alert">{{ error }}</div>
          </Transition>
        </div>

        <p class="lab-narracion" aria-live="polite">{{ narracion }}</p>
      </article>

      <aside class="lab-lateral">
        <article class="card lab-metricas rise" style="--i: 2">
          <header class="card-title">
            <span class="badge-icon"><Icon name="mochila" :size="16" /></span>
            Programación dinámica frente a voraz
          </header>
          <div v-if="seleccion" class="duelo">
            <div class="contendiente pd">
              <span class="eyebrow">Programación dinámica</span>
              <strong class="display num"><AnimatedNumber :value="seleccion.optima.valor" /></strong>
              <span class="barra"><i :style="{ width: `${(seleccion.optima.peso / Math.max(1, seleccion.capacidad)) * 100}%` }" /></span>
              <small class="num">{{ seleccion.optima.peso }} / {{ seleccion.capacidad }} kg · {{ seleccion.optima.elegidos.length }} objetos</small>
            </div>
            <div class="contendiente voraz">
              <span class="eyebrow">Voraz por valor/peso</span>
              <strong class="display num"><AnimatedNumber :value="seleccion.voraz.valor" /></strong>
              <span class="barra"><i :style="{ width: `${(seleccion.voraz.peso / Math.max(1, seleccion.capacidad)) * 100}%` }" /></span>
              <small class="num">{{ seleccion.voraz.peso }} / {{ seleccion.capacidad }} kg · {{ seleccion.voraz.elegidos.length }} objetos</small>
            </div>
          </div>
          <p v-if="seleccion" class="lab-nota">
            <template v-if="diferencia > 0">El voraz toma primero lo más denso y deja espacio sin usar: pierde {{ diferencia }} de oro. La PD prueba todas las capacidades y garantiza el óptimo en O(n·W).</template>
            <template v-else>Con estos datos el voraz coincide con el óptimo, pero no está garantizado: pruebe otra capacidad.</template>
            Motor: {{ seleccion.tiempo_ms.toFixed(3) }} ms.
          </p>
        </article>

        <article class="card rise" style="--i: 3">
          <header class="card-title">
            <span class="badge-icon"><Icon name="resultados" :size="16" /></span>
            Objetos
            <span class="acciones-objetos">
              <button type="button" class="btn mini" :disabled="objetos.length >= MAX_OBJETOS" @click="agregar">Agregar</button>
              <button type="button" class="btn mini" @click="restaurar">Ejemplo</button>
            </span>
          </header>
          <table class="objetos">
            <thead>
              <tr><th>Objeto</th><th>kg</th><th>Oro</th><th>Oro/kg</th><th>PD</th><th>Voraz</th><th /></tr>
            </thead>
            <tbody>
              <tr v-for="(o, i) in objetos" :key="i">
                <td><input v-model="o.nombre" maxlength="40" aria-label="Nombre" @input="programar" /></td>
                <td><input v-model.number="o.peso" type="number" min="1" max="100" aria-label="Peso" class="num" @input="programar" /></td>
                <td><input v-model.number="o.valor" type="number" min="0" aria-label="Valor" class="num" @input="programar" /></td>
                <td class="num densidad">{{ o.peso ? (o.valor / o.peso).toFixed(1) : '—' }}</td>
                <td><span v-if="elegidosPD.has(i)" class="marca pd" title="La programación dinámica lo lleva">✓</span></td>
                <td><span v-if="elegidosVoraz.has(i)" class="marca voraz" title="El voraz lo lleva">✓</span></td>
                <td><button type="button" class="quitar" aria-label="Quitar objeto" :disabled="objetos.length <= 1" @click="quitar(i)">×</button></td>
              </tr>
            </tbody>
          </table>
        </article>

        <PseudocodePanel
          v-if="info"
          class="rise"
          style="--i: 4"
          :nombre="info.nombre"
          :lineas="info.pseudocodigo"
          :activa="lineaActiva"
          :conteos="conteos"
        />
      </aside>
    </div>
  </section>
</template>

<style scoped>
.capacidad { display: flex; align-items: center; gap: 12px; padding: 8px 16px; border-radius: 999px; background: #fff; border: 1px solid var(--line); }
.capacidad input { width: 180px; accent-color: var(--violet); }
.capacidad strong { min-width: 48px; font-size: 14px; }

.tabla-marco { overflow: auto; padding: 14px; background: #fff; border: 1px solid var(--line); }
.tabla { display: grid; gap: 2px; min-width: 520px; font-size: 10.5px; }
.esquina, .encabezado { color: var(--ink-4); text-align: center; padding-bottom: 2px; }
.esquina { text-align: left; font-size: 10px; }
.rotulo { display: flex; align-items: center; gap: 6px; padding: 0 6px; border-radius: 6px; color: var(--ink-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: background 0.25s, color 0.25s; }
.rotulo i { font-style: normal; color: var(--ink-4); min-width: 14px; }
.rotulo.activa { background: var(--violet-soft); color: var(--violet); font-weight: 600; }
.rotulo.elegido { background: #f8dcd8; color: #8c281c; font-weight: 600; }
.celda {
  position: relative; display: grid; place-items: center; min-height: 22px; border-radius: 4px;
  transition: background 0.35s var(--ease-out), box-shadow 0.25s;
}
.celda.lleva::after { content: ''; position: absolute; top: 3px; right: 3px; width: 4px; height: 4px; border-radius: 50%; background: var(--gold); }
.celda.camino { box-shadow: inset 0 0 0 2px #c0392b; }

.duelo { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.contendiente { display: grid; gap: 6px; padding: 12px 14px; border-radius: 16px; }
.contendiente.pd { background: var(--violet-soft); }
.contendiente.voraz { background: var(--cream); }
.contendiente strong { font-size: 36px; font-weight: 400; line-height: 1; letter-spacing: -0.03em; }
.contendiente small { color: var(--ink-3); font-size: 11px; }
.barra { height: 6px; border-radius: 6px; background: rgba(255, 255, 255, 0.8); overflow: hidden; }
.barra i { display: block; height: 100%; border-radius: 6px; transition: width 0.6s var(--ease-out); }
.pd .barra i { background: var(--violet); }
.voraz .barra i { background: var(--gold); }

.acciones-objetos { display: flex; gap: 6px; margin-left: auto; }
.btn.mini { padding: 4px 11px; font-size: 11.5px; }
.objetos { width: 100%; border-collapse: collapse; font-size: 12px; }
.objetos th { padding: 4px 4px 6px; color: var(--ink-3); font-size: 10.5px; font-weight: 500; text-align: left; border-bottom: 1px solid var(--line); }
.objetos td { padding: 3px 4px; }
.objetos tr + tr td { border-top: 1px solid var(--line); }
.objetos input { width: 100%; padding: 4px 6px; border: 1px solid transparent; border-radius: 8px; background: transparent; font: inherit; }
.objetos input:hover, .objetos input:focus { border-color: var(--line-strong); background: #fff; outline: none; }
.objetos input[type='number'] { width: 52px; }
.densidad { color: var(--ink-3); }
.marca { display: inline-grid; place-items: center; width: 20px; height: 20px; border-radius: 50%; font-size: 11px; }
.marca.pd { background: var(--violet-soft); color: var(--violet); }
.marca.voraz { background: var(--cream); color: #6b4c0d; }
.quitar { width: 22px; height: 22px; border-radius: 50%; color: var(--ink-4); }
.quitar:hover:not(:disabled) { background: #f8dcd8; color: #8c281c; }
</style>
