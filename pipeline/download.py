"""Descarga los resultados de LaLiga desde openfootball/football.json.

- Las temporadas cerradas solo se descargan una vez.
- La temporada en curso se vuelve a descargar siempre.
- Al final se genera data/processed/matches.csv con un partido por fila.

Uso:  python pipeline/download.py
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/openfootball/football.json/master/{season}/es.1.json"
FIRST_SEASON = 2012  # primera temporada con datos completos en openfootball
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_CSV = ROOT / "data" / "processed" / "matches.csv"


def season_label(start_year: int) -> str:
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def current_season_start(today: date | None = None) -> int:
    today = today or date.today()
    # La temporada empieza en agosto: de julio a diciembre es "este año", el resto "el año pasado".
    return today.year if today.month >= 7 else today.year - 1


def fetch(season: str) -> dict | None:
    url = BASE_URL.format(season=season)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise


def parse_score(score) -> tuple[int | None, int | None, int | None, int | None]:
    """El campo score aparece de dos formas: {"ft": [h, a], "ht": [h, a]} o [h, a]."""
    if score is None:
        return None, None, None, None
    if isinstance(score, list):
        return score[0], score[1], None, None
    ft = score.get("ft") or [None, None]
    ht = score.get("ht") or [None, None]
    return ft[0], ft[1], ht[0], ht[1]


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    current = current_season_start()

    for year in range(FIRST_SEASON, current + 1):
        season = season_label(year)
        path = RAW_DIR / f"es1_{season}.json"
        if path.exists() and year < current:
            continue
        data = fetch(season)
        if data is None:
            print(f"[aviso] {season}: no disponible todavía")
            continue
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[ok] {season}: {len(data['matches'])} partidos")

    rows = []
    for path in sorted(RAW_DIR.glob("es1_*.json")):
        season = path.stem.removeprefix("es1_")
        for m in json.loads(path.read_text(encoding="utf-8"))["matches"]:
            ft_h, ft_a, ht_h, ht_a = parse_score(m.get("score"))
            rows.append({
                "season": season,
                "matchday": int(m["round"].split()[-1]),
                "match_date": m["date"],
                "kickoff_time": m.get("time"),
                "home_team_raw": m["team1"],
                "away_team_raw": m["team2"],
                "home_goals": ft_h,
                "away_goals": ft_a,
                "home_goals_ht": ht_h,
                "away_goals_ht": ht_a,
            })

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] {len(rows)} partidos escritos en {OUT_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
