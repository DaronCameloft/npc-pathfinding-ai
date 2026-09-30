# ADR 0002 — Algoritmos en su propia carpeta, sin instrumentación

- **Estado:** aceptada
- **Fecha:** 2026-09-29

## Contexto

La evaluación exige que cada integrante explique el código de los algoritmos. En la versión anterior, A* mezclaba la búsqueda con cronómetros, contadores, grabación de eventos, CLI y exportación a JSON en un mismo archivo, lo que dificultaba seguirlo.

## Decisión

1. Los algoritmos viven en `engine/src/npc_nav/algorithms/`, al primer nivel del paquete. Conceptualmente son servicios del dominio, pero se les da visibilidad propia a propósito.
2. Un archivo por algoritmo, con docstring que contiene referencia, pseudocódigo numerado y complejidad; los comentarios del código repiten la numeración.
3. Todos comparten la firma `algoritmo(grafo, inicio, destino, observador) -> ResultadoBusqueda`.
4. La medición se hace desde `application/` mediante observadores inyectados (patrón *Observer*).

## Consecuencias

- El código de cada algoritmo cabe en una pantalla y coincide con el pseudocódigo del informe.
- La comparación es justa: todos se miden con el mismo mecanismo.
- Agregar un algoritmo es crear un archivo y registrarlo en `catalogo.py`; las pruebas de contrato lo cubren automáticamente.
- Medir con traza requiere una segunda ejecución; se acepta porque los algoritmos son deterministas y así el tiempo reportado nunca incluye la grabación.
