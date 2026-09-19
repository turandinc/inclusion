"""JSON veri dosyalarini yukler ve onbellege alir."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

VERI_DIZINI = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=None)
def yukle(ad: str) -> dict:
    """data/<ad>.json dosyasini okur. Sonuc onbellege alinir."""
    yol = VERI_DIZINI / f"{ad}.json"
    if not yol.exists():
        raise FileNotFoundError(f"Veri dosyasi bulunamadi: {yol}")
    with yol.open(encoding="utf-8") as f:
        return json.load(f)
