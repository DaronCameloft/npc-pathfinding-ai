"""Check the Unity demo inputs against the real Python engine.

By default, calls the application directly. Add --api http://127.0.0.1:8000
to exercise the real HTTP contract. It never starts or modifies the server.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from npc_nav.application.busqueda import ejecutar_busqueda
from npc_nav.domain.sesion import SesionNavegacion
from npc_nav.infrastructure.repositorio import RepositorioDataset


def run(api: str | None = None) -> dict:
    manifest = json.loads((ROOT / "unity/Arcadia/Assets/StreamingAssets/Arcadia/demo.json")
                          .read_text(encoding="utf-8"))
    repo = RepositorioDataset(ROOT / "engine/data")
    terrain = repo.mapa(manifest["map"])
    start, goal = tuple(manifest["start"]), tuple(manifest["goal"])
    gate = [tuple(p) for p in manifest["gate_cells"]]
    seal = [tuple(p) for p in manifest["sealed_passage_cells"]]

    def search(origin, blocked=(), algorithm="astar"):
        session = SesionNavegacion(terrain)
        session.actualizar_obstaculos(bloquear=blocked)
        if api:
            body = json.dumps({"mapa": manifest["map"], "algoritmo": algorithm,
                               "inicio": origin, "destino": goal,
                               "bloqueadas": blocked, "traza": False}).encode("utf-8")
            request = Request(api.rstrip("/") + "/buscar", data=body,
                              headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=20) as response:
                result = json.load(response)
        else:
            result = asdict(ejecutar_busqueda(session, algorithm, origin, goal))
        route = [tuple(p) for p in result["ruta"]]
        if result["estado"] == "encontrada":
            assert route[0] == tuple(origin) and route[-1] == goal
            assert math.isclose(session.costo_ruta(route), result["costo"], abs_tol=1e-8)
            assert not set(route).intersection(blocked)
        else:
            assert result["estado"] == "sin_ruta" and not route and result["costo"] is None
        return result

    initial = search(start)
    closed = search(start, gate)
    assert initial["estado"] == closed["estado"] == "encontrada"
    assert closed["costo"] > initial["costo"]
    assert closed["ruta"] != initial["ruta"]

    current = tuple(initial["ruta"][12])
    moving_replan = search(current, gate)
    oracle = search(current, gate, "dijkstra")
    assert moving_replan["estado"] == "encontrada"
    assert math.isclose(moving_replan["costo"], oracle["costo"], abs_tol=1e-8)

    no_route = search(start, seal)
    assert no_route["estado"] == "sin_ruta"
    reopened = search(start)
    assert reopened["ruta"] == initial["ruta"]
    assert math.isclose(reopened["costo"], initial["costo"], abs_tol=1e-8)

    return {
        "status": "passed",
        "transport": api or "direct Python application",
        "map": manifest["map"],
        "scenario_index": manifest["scenario_index"],
        "initial": {"moves": len(initial["ruta"]) - 1, "cost": initial["costo"]},
        "gate_closed": {"moves": len(closed["ruta"]) - 1, "cost": closed["costo"]},
        "moving_replan": {"from": current, "moves": len(moving_replan["ruta"]) - 1,
                          "cost": moving_replan["costo"], "matches_dijkstra": True},
        "sealed_passage": no_route["estado"],
        "reopened": "original route restored",
        "checks": ["route endpoints", "all steps legal", "octile cost",
                   "blocked cells avoided", "replan from current position",
                   "Dijkstra cost reference", "no-route response", "unblock recovery"],
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", help="Optional running engine base URL")
    parser.add_argument("--output", type=Path, help="Optional JSON evidence file")
    args = parser.parse_args()
    result = run(args.api)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
