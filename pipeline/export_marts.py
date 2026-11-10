"""Exporta las tablas finales de DuckDB a Parquet para el dashboard y los notebooks.

Así el dashboard no necesita dbt ni la base de datos: solo lee data/marts/*.parquet.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "laliga.duckdb"
OUT = ROOT / "data" / "marts"
TABLES = [
    "fct_matches",
    "fct_standings_by_matchday",
    "fct_final_standings",
    "mart_home_advantage",
    "mart_comebacks",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    for t in TABLES:
        path = OUT / f"{t}.parquet"
        con.execute(f"copy (select * from {t}) to '{path}' (format parquet)")
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        print(f"[ok] {t}: {n} filas -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
