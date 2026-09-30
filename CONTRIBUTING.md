# Cómo trabajamos

## Ramas (Git Flow)

| Rama | Uso |
|---|---|
| `main` | Producción: lo que está desplegado y lo que se entrega. Solo recibe merges desde `develop` (o `hotfix/*`). |
| `develop` | Integración del trabajo terminado. Base de todas las ramas de trabajo. |
| `feature/<nombre>` | Un avance concreto. Sale de `develop` y vuelve a `develop` por Pull Request. |
| `hotfix/<nombre>` | Corrección urgente sobre `main`; se integra en `main` y en `develop`. |

Nombres **en inglés**, en minúsculas y con guiones: `feature/engine-api`, `feature/web-dashboard`, `feature/dstar-lite`, `feature/unity-client`.

```powershell
git checkout develop
git pull
git checkout -b feature/web-dashboard
# ... commits ...
git push -u origin feature/web-dashboard
# Pull Request feature/web-dashboard → develop, revisión de otro integrante, merge
```

Entrega o despliegue: Pull Request `develop → main`.

## Commits

Formato de una sola línea, **en inglés**, en minúsculas, en imperativo, sin punto final, sin cuerpo y sin líneas `Co-Authored-By`:

```
type(scope): description
```

| Tipo | Cuándo |
|---|---|
| `feat` | Funcionalidad nueva |
| `fix` | Corrección de un error |
| `refactor` | Cambio de estructura sin cambiar el comportamiento |
| `test` | Pruebas nuevas o corregidas |
| `docs` | Documentación e informe |
| `chore` | Configuración, dependencias, mantenimiento |
| `perf` | Mejora de rendimiento |
| `ci` | Integración continua |

Scopes: `engine`, `algorithms`, `api`, `web`, `unity`, `data`, `results`, `docs`, `ci`, `repo`.

Ejemplos:

```
chore(repo): set up monorepo structure and migrate engine
feat(algorithms): add d* lite with incremental replanning
feat(web): replay search trace on canvas
fix(api): return 404 for unknown map
test(algorithms): check dijkstra against oracle
docs(docs): document search event contract
```

## Antes de abrir un Pull Request

- `python -m unittest discover -s tests -t .` pasa desde `engine/`.
- Si cambió un algoritmo, se regeneró su evidencia con `npc-nav verificar --algoritmo <clave>`.
- Las cifras citadas en el informe provienen de archivos en `engine/results/`.
- Cada integrante puede explicar el código que integra: la sustentación incluye preguntas individuales.
