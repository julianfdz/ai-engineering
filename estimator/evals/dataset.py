# ── Julián · Sesión 5 · Golden dataset ────────────────────────────────────────
#
#   Cada caso es una transcripción con lo que esperamos de la respuesta. Sirve para
#   comparar versiones del sistema con números, no con impresiones.
#
#   · Casi todo son rangos (coste, semanas, nº de fases): el modelo varía entre ejecuciones.
#   · También fija qué términos y tecnologías deben salir, y si el caso es «Out of scope».
#   · expected_tier permite comprobar qué audiencia ha resuelto el sistema en ese caso.
#   · Los 16 casos viven en golden_dataset.json, versionados junto al código.
# ──────────────────────────────────────────────────────────────────────────────

"""Typed golden cases + JSON loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


ProjectTypeStr = Literal["mobile_app", "web_saas", "internal_tool", "data_pipeline"]
DetailLevelStr = Literal["summary", "medium", "detailed"]
OutputFormatStr = Literal["phases_table", "line_items", "narrative"]
TierStr = Literal["auto", "executive", "pm", "developer", "default"]


class GoldenCase(BaseModel):
    """One transcript + the expected envelope around the model's reply.

    Most checks are loose ranges instead of exact equality: an LLM has
    legitimate latitude in how it scopes a phase. The goal is to catch
    obvious regressions (out-of-budget, missing tech, wrong tier), not to
    pin every digit.
    """

    id: str = Field(min_length=3, max_length=64)
    transcript: str = Field(min_length=20, max_length=80_000)
    project_type: ProjectTypeStr
    detail_level: DetailLevelStr = "medium"
    output_format: OutputFormatStr = "phases_table"
    tier: TierStr = "auto"

    expected_out_of_scope: bool = False
    expected_in_summary: list[str] = Field(default_factory=list)
    expected_technologies_any_of: list[str] = Field(default_factory=list)
    expected_phase_count_range: tuple[int, int] | None = None
    expected_cost_range_eur: tuple[int, int] | None = None
    expected_duration_weeks_range: tuple[int, int] | None = None
    expected_tier: TierStr | None = None  # asserted against last_resolved_tier


_DEFAULT_PATH = Path(__file__).resolve().parent / "golden_dataset.json"


def load_dataset(path: Path | str | None = None) -> list[GoldenCase]:
    target = Path(path) if path else _DEFAULT_PATH
    raw = json.loads(target.read_text(encoding="utf-8"))
    return [GoldenCase.model_validate(entry) for entry in raw]
