"""Dashboard de LaLiga Analytics.

Lee las tablas exportadas en data/marts/*.parquet (generadas por el pipeline).
Ejecutar:  streamlit run app/streamlit_app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

MARTS = Path(__file__).resolve().parents[1] / "data" / "marts"

st.set_page_config(page_title="LaLiga Analytics", page_icon="⚽", layout="wide")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_parquet(MARTS / f"{name}.parquet")


matches = load("fct_matches")
standings = load("fct_standings_by_matchday")
home = load("mart_home_advantage")

seasons = sorted(standings["season"].unique(), reverse=True)

st.title("⚽ LaLiga Analytics")
last_date = pd.to_datetime(matches["match_date"]).max().date()
st.caption(
    f"{len(matches):,} partidos desde 2012-13 · último partido registrado: {last_date} · "
    "datos: openfootball (dominio público)".replace(",", ".")
)

tab_table, tab_evo, tab_h2h, tab_home = st.tabs(
    ["Clasificación", "Evolución", "Cara a cara", "Ventaja de jugar en casa"]
)

# --- Clasificación -----------------------------------------------------------
with tab_table:
    c1, c2 = st.columns([1, 3])
    season = c1.selectbox("Temporada", seasons, key="season_table")
    s = standings[standings["season"] == season]
    max_md = int(s["matchday"].max())
    md = c2.slider("Tras la jornada", 1, max_md, max_md) if max_md > 1 else max_md
    table = (
        s[s["matchday"] == md]
        .sort_values("position")
        .loc[:, ["position", "team", "played", "points", "wins", "draws", "losses",
                 "goals_for", "goals_against", "goal_difference"]]
        .rename(columns={
            "position": "Pos", "team": "Equipo", "played": "PJ", "points": "Pts",
            "wins": "G", "draws": "E", "losses": "P", "goals_for": "GF",
            "goals_against": "GC", "goal_difference": "DG",
        })
    )
    st.dataframe(table, hide_index=True, width="stretch", height=740)
    st.caption("Desempate por diferencia de goles. LaLiga usa antes el enfrentamiento directo, "
               "así que con empates a puntos el orden puede diferir del oficial.")

# --- Evolución ---------------------------------------------------------------
with tab_evo:
    season = st.selectbox("Temporada", seasons, key="season_evo")
    s = standings[standings["season"] == season]
    final = s[s["matchday"] == s["matchday"].max()].sort_values("position")
    teams = st.multiselect("Equipos", final["team"].tolist(), default=final["team"].head(4).tolist())
    fig = px.line(
        s[s["team"].isin(teams)].sort_values(["team", "matchday"]),
        x="matchday", y="position", color="team", markers=True,
        labels={"matchday": "Jornada", "position": "Posición", "team": "Equipo"},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_yaxes(autorange="reversed", dtick=1)
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width="stretch")

# --- Cara a cara -------------------------------------------------------------
with tab_h2h:
    all_teams = sorted(set(matches["home_team"]) | set(matches["away_team"]))
    c1, c2 = st.columns(2)
    a = c1.selectbox("Equipo A", all_teams, index=all_teams.index("Real Madrid"))
    b = c2.selectbox("Equipo B", all_teams, index=all_teams.index("Barcelona"))
    h2h = matches[
        ((matches["home_team"] == a) & (matches["away_team"] == b))
        | ((matches["home_team"] == b) & (matches["away_team"] == a))
    ].sort_values("match_date", ascending=False)
    if a == b or h2h.empty:
        st.info("Elige dos equipos distintos que se hayan enfrentado en LaLiga desde 2012-13.")
    else:
        def winner(r):
            if r.home_goals == r.away_goals:
                return "Empate"
            return r.home_team if r.home_goals > r.away_goals else r.away_team
        h2h = h2h.assign(ganador=h2h.apply(winner, axis=1))
        counts = h2h["ganador"].value_counts()
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Victorias {a}", int(counts.get(a, 0)))
        m2.metric("Empates", int(counts.get("Empate", 0)))
        m3.metric(f"Victorias {b}", int(counts.get(b, 0)))
        st.dataframe(
            h2h.assign(resultado=h2h["home_goals"].astype(str) + "-" + h2h["away_goals"].astype(str))
            .loc[:, ["season", "match_date", "home_team", "resultado", "away_team"]]
            .rename(columns={"season": "Temporada", "match_date": "Fecha",
                             "home_team": "Local", "resultado": "Resultado", "away_team": "Visitante"}),
            hide_index=True, width="stretch",
        )

# --- Ventaja local -----------------------------------------------------------
with tab_home:
    agg = (
        home.assign(grupo=home["is_behind_closed_doors"].map({True: "Sin público", False: "Con público"}))
        .groupby(["season", "grupo"], as_index=False)
        .apply(lambda g: pd.Series({
            "partidos": g["matches"].sum(),
            "victoria_local": (g["home_win_rate"] * g["matches"]).sum() / g["matches"].sum(),
        }), include_groups=False)
    )
    fig = px.bar(
        agg, x="season", y="victoria_local", color="grupo", barmode="group",
        labels={"season": "Temporada", "victoria_local": "% victorias locales", "grupo": ""},
        color_discrete_map={"Con público": "#2b6cb0", "Sin público": "#dd6b20"},
        category_orders={"season": sorted(agg["season"].unique())},
    )
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")
    st.markdown(
        "Los partidos **sin público** son los jugados entre junio de 2020 y junio de 2021 por la COVID-19. "
        "El análisis completo está en `notebooks/01_ventaja_local.ipynb`."
    )
