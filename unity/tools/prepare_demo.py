"""Export the original terrain and a deterministic Unity demonstration manifest.

Run with the engine virtual environment from any directory. This exports terrain
and scenario inputs only: Unity must request every playable route from Python.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from npc_nav.infrastructure.repositorio import RepositorioDataset


def prepare() -> dict:
    repo = RepositorioDataset(ROOT / "engine" / "data")
    terrain = repo.mapa("den011d")
    scenario = repo.escenario("den011d", 124)
    output = ROOT / "unity" / "Arcadia" / "Assets" / "StreamingAssets" / "Arcadia"
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "title": "Arcadia — El jardín de los guardianes",
        "map": "den011d",
        "scenario_index": 124,
        "algorithm": "astar",
        "api_url": "http://127.0.0.1:8000",
        "start": list(scenario.inicio),
        "goal": list(scenario.destino),
        "gate_cells": [[row, 99] for row in range(87, 95)],
        "sealed_passage_cells": [[88, 102], [89, 102]],
        "camera_focus": {"x": 107.5, "y": 0.0, "z": 98.0},
        "showcase_bounds": {
            "min_row": 80, "max_row": 115,
            "min_column": 84, "max_column": 132,
        },
        "cell_size": 1.0,
        "coordinate_convention": "[row,column] -> Unity (x=column,y=0,z=row)",
        "terrain_source": "engine/data/maps/den011d.map",
        "terrain_sha256": hashlib.sha256(repo.ruta_mapa("den011d").read_bytes()).hexdigest(),
        "terrain_usage": "Visual fallback only. Routes always come from the running engine.",
    }
    (output / "demo.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "den011d.json").write_text(
        json.dumps({"nombre": "den011d", "alto": terrain.alto,
                    "ancho": terrain.ancho, "filas": list(terrain.celdas)},
                   ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(prepare(), indent=2, ensure_ascii=False))
