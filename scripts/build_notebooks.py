"""Genera los notebooks de análisis (se ejecutan después con nbconvert)."""
from pathlib import Path
import nbformat as nbf

NB = Path(__file__).resolve().parents[1] / "notebooks"

SETUP = '''import duckdb, pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
MARTS, IMG = ROOT / "data" / "marts", ROOT / "docs" / "img"
IMG.mkdir(parents=True, exist_ok=True)
con = duckdb.connect()
for t in ["fct_matches", "fct_standings_by_matchday", "fct_final_standings", "mart_home_advantage", "mart_comebacks"]:
    con.execute(f"create view {t} as select * from '{MARTS / (t + '.parquet')}'")
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .3, "font.size": 11})
q = lambda sql: con.execute(sql).df()'''


def notebook(name, cells):
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbf.write(nb, NB / name)


# --------------------------------------------------------------------------
notebook("01_ventaja_local.ipynb", [
    ("md", """# 1. ¿Cuánto vale jugar en casa en LaLiga?

**Pregunta:** ¿qué ventaja da jugar como local y qué pasó cuando los estadios se quedaron vacíos por la COVID-19?

Entre junio de 2020 y junio de 2021 LaLiga se jugó sin público. Es un experimento natural: mismo campeonato, mismos equipos, pero sin afición. Si la ventaja local se debe sobre todo al público, debería reducirse en esos partidos.

Se usan solo temporadas terminadas (se excluye la temporada en curso)."""),
    ("code", SETUP),
    ("md", "## Ventaja local por temporada"),
    ("code", '''by_season = q("""
    select season,
           sum(matches) as partidos,
           sum(home_win_rate * matches) / sum(matches) as victoria_local,
           sum(draw_rate * matches) / sum(matches)     as empate,
           sum(away_win_rate * matches) / sum(matches) as victoria_visitante,
           sum(avg_home_points * matches) / sum(matches) - sum(avg_away_points * matches) / sum(matches) as ventaja_puntos
    from mart_home_advantage
    where season < (select max(season) from mart_home_advantage)  -- solo temporadas terminadas
    group by season order by season""")
by_season.style.format({"victoria_local": "{:.1%}", "empate": "{:.1%}", "victoria_visitante": "{:.1%}", "ventaja_puntos": "{:+.2f}"})'''),
    ("md", "## Con público frente a sin público"),
    ("code", '''groups = q("""
    select case when is_behind_closed_doors then 'Sin público' else 'Con público' end as grupo,
           count(*) as partidos,
           avg((outcome = 'local')::int)     as victoria_local,
           avg((outcome = 'empate')::int)    as empate,
           avg((outcome = 'visitante')::int) as victoria_visitante,
           avg(case outcome when 'local' then 3 when 'empate' then 1 else 0 end)
         - avg(case outcome when 'visitante' then 3 when 'empate' then 1 else 0 end) as ventaja_puntos,
           avg(home_goals) - avg(away_goals) as ventaja_goles
    from fct_matches
    where season < (select max(season) from fct_matches)  -- solo temporadas terminadas
    group by 1 order by 1""")
groups.style.format({"victoria_local": "{:.1%}", "empate": "{:.1%}", "victoria_visitante": "{:.1%}",
                     "ventaja_puntos": "{:+.2f}", "ventaja_goles": "{:+.2f}"})'''),
    ("md", """### ¿Es una diferencia real o puede ser casualidad?

Usamos un test de diferencia de proporciones sobre el % de victorias locales. Solo hay unos 450 partidos sin público, así que conviene comprobarlo."""),
    ("code", '''import math
a, b = groups.set_index("grupo").loc["Con público"], groups.set_index("grupo").loc["Sin público"]
p1, n1, p2, n2 = a.victoria_local, a.partidos, b.victoria_local, b.partidos
p = (p1 * n1 + p2 * n2) / (n1 + n2)
z = (p1 - p2) / math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
p_value = math.erfc(abs(z) / math.sqrt(2))
print(f"Victoria local con público: {p1:.1%} (n={n1:.0f})")
print(f"Victoria local sin público: {p2:.1%} (n={n2:.0f})")
print(f"Diferencia: {(p1 - p2) * 100:.1f} puntos porcentuales · z = {z:.2f} · p-valor = {p_value:.3f}")'''),
    ("code", '''fig, ax = plt.subplots(figsize=(10, 4.5))
cols = ["#d9822b" if s in ("2019-20", "2020-21") else "#2b6cb0" for s in by_season.season]
ax.bar(by_season.season, by_season.victoria_local, color=cols)
ax.axhline(by_season.victoria_local.mean(), color="#555", ls="--", lw=1)
ax.set_ylim(0, .6); ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
ax.set_title("% de partidos ganados por el equipo local en LaLiga", loc="left", fontweight="bold")
ax.text(len(by_season) - .5, by_season.victoria_local.mean() + .01, "media", ha="right", color="#555")
ax.set_xlabel("Naranja: temporadas con partidos sin público (COVID-19)")
plt.xticks(rotation=45, ha="right"); plt.tight_layout()
fig.savefig(IMG / "ventaja_local.png", dpi=150); plt.show()'''),
    ("md", """## Conclusiones

- Jugar en casa da ventaja en todas las temporadas: con público, el local gana el **46,6 %** de los partidos y el visitante el 28,4 %.
- Sin público (490 partidos), la victoria local baja al **41,4 %** y el margen medio de goles del local casi se reduce a la mitad (de +0,41 a +0,22).
- La diferencia es estadísticamente significativa al 5 % (p ≈ 0,03), pero por poco. La ventaja **se reduce, no desaparece**: parte de ella viene de otros factores (no viajar, conocer el campo, rutinas).
- Prudencia: esos partidos coinciden con un calendario anómalo (partidos cada tres días tras el parón), que también pudo influir."""),
])

# --------------------------------------------------------------------------
notebook("02_remontadas.ipynb", [
    ("md", """# 2. ¿Qué equipos ganan y pierden partidos en la segunda parte?

**Pregunta:** si los partidos terminaran en el descanso, ¿cómo cambiaría la clasificación? ¿Qué equipos remontan más y cuáles dejan escapar ventajas?

Comparamos los puntos reales de cada equipo con los que tendría si el resultado del minuto 45 fuera el final.

*Limitación: a unos 25-40 partidos por temporada les falta el resultado al descanso en la fuente; se excluyen de este análisis.*"""),
    ("code", SETUP),
    ("md", "## En toda la liga: ¿cuánto se mantiene el resultado del descanso?"),
    ("code", '''q("""
    select outcome_ht as al_descanso,
           count(*) as partidos,
           avg((outcome = 'local')::int)     as acaba_victoria_local,
           avg((outcome = 'empate')::int)    as acaba_empate,
           avg((outcome = 'visitante')::int) as acaba_victoria_visitante
    from fct_matches where outcome_ht is not null group by 1 order by 1
""").style.format({c: "{:.1%}" for c in ["acaba_victoria_local", "acaba_empate", "acaba_victoria_visitante"]})'''),
    ("md", "## Por equipo (equipos con al menos 5 temporadas en Primera desde 2012-13)"),
    ("code", '''teams = q("""
    select team as equipo,
           count(distinct season) as temporadas,
           sum(matches_with_ht) as partidos,
           sum(comebacks) as remontadas,
           sum(losing_at_ht) as perdiendo_al_descanso,
           sum(comebacks) / sum(losing_at_ht) as pct_remonta,
           sum(blown_leads) as ventajas_perdidas,
           sum(winning_at_ht) as ganando_al_descanso,
           sum(blown_leads) / sum(winning_at_ht) as pct_pierde_ventaja,
           38.0 * sum(second_half_points_delta) / sum(matches_with_ht) as puntos_2a_parte_por_temporada
    from mart_comebacks group by team having count(distinct season) >= 5
    order by puntos_2a_parte_por_temporada desc""")
teams.style.format({"pct_remonta": "{:.0%}", "pct_pierde_ventaja": "{:.0%}", "puntos_2a_parte_por_temporada": "{:+.1f}"})'''),
    ("code", '''t = teams.sort_values("puntos_2a_parte_por_temporada")
fig, ax = plt.subplots(figsize=(9, 7))
ax.barh(t.equipo, t.puntos_2a_parte_por_temporada,
        color=["#2f855a" if v > 0 else "#c53030" for v in t.puntos_2a_parte_por_temporada])
ax.axvline(0, color="#333", lw=.8)
ax.set_title("Puntos ganados (+) o perdidos (−) en la segunda parte\\npor temporada de 38 partidos, desde 2012-13",
             loc="left", fontweight="bold")
ax.set_xlabel("Puntos reales − puntos si el partido acabara en el descanso")
plt.tight_layout(); fig.savefig(IMG / "segunda_parte.png", dpi=150); plt.show()'''),
    ("md", """## Conclusiones

- El resultado del descanso pesa mucho: el local que gana al descanso acaba ganando el **80 %** de las veces; el visitante que va ganando, el **68 %**.
- Barcelona (+16,9), Atlético (+15,9) y Real Madrid (+15,2) suman unos 15-17 puntos por temporada en las segundas partes. Además casi nunca dejan escapar una ventaja (entre el 7 % y el 14 % de las veces).
- En el otro extremo, Deportivo (−5,4), Valladolid (−4,3) y Elche (−3,1) pierden puntos tras el descanso de forma sistemática.
- Remontar se parece más a un reflejo de la calidad de la plantilla que a un rasgo de "carácter". Un siguiente paso sería controlar por el nivel del rival."""),
])

# --------------------------------------------------------------------------
notebook("03_primeras_jornadas.ipynb", [
    ("md", """# 3. ¿Cuánto dicen las primeras 10 jornadas del final de la liga?

**Pregunta:** tras 10 de 38 jornadas, ¿podemos fiarnos de la clasificación? ¿Quién está arriba en octubre, sigue arriba en mayo?

Usamos las temporadas completas desde 2012-13. Excluimos la temporada en curso y la 2024-25, a la que le falta la última jornada en la fuente."""),
    ("code", SETUP),
    ("code", '''pairs = q("""
    with final as (
        select season, team, position as final_pos from fct_final_standings
        where last_matchday = 38 and season not in ('2024-25')
    )
    select s.season, s.matchday, s.team, s.position, f.final_pos
    from fct_standings_by_matchday s join final f using (season, team)""")
print(pairs.season.nunique(), "temporadas completas")'''),
    ("md", "## Correlación entre la posición en cada jornada y la posición final"),
    ("code", '''corr = (pairs.groupby("matchday")
        .apply(lambda g: g["position"].rank().corr(g["final_pos"].rank()), include_groups=False)
        .rename("spearman").reset_index())
print(corr[corr.matchday.isin([1, 5, 10, 15, 19, 25, 30])].to_string(index=False))'''),
    ("md", "## Tras la jornada 10: ¿se mantienen arriba y abajo?"),
    ("code", '''md10 = pairs[pairs.matchday == 10]
rows = []
for name, cond_now, cond_final in [
    ("Top 4 en la J10 → acaba top 4 (Champions)", md10.position <= 4, md10.final_pos <= 4),
    ("Top 1 en la J10 → acaba campeón", md10.position == 1, md10.final_pos == 1),
    ("Descenso en la J10 → acaba descendiendo", md10.position >= 18, md10.final_pos >= 18),
]:
    sel = md10[cond_now]
    rows.append({"situación": name, "casos": len(sel), "se_cumple": cond_final[cond_now].mean()})
pd.DataFrame(rows).style.format({"se_cumple": "{:.0%}"})'''),
    ("code", '''fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(corr.matchday, corr.spearman, color="#2b6cb0", lw=2.5)
ax.scatter([10], corr.loc[corr.matchday == 10, "spearman"], color="#d9822b", zorder=3, s=60)
v10 = corr.loc[corr.matchday == 10, "spearman"].iloc[0]
ax.annotate(f"Jornada 10: {v10:.2f}", (10, v10), xytext=(13, v10 - .12),
            arrowprops=dict(arrowstyle="->", color="#555"))
ax.set_ylim(0, 1); ax.set_xlim(1, 38)
ax.set_xlabel("Jornada"); ax.set_ylabel("Correlación (Spearman)")
ax.set_title("¿Cuánto se parece la clasificación de cada jornada a la final?", loc="left", fontweight="bold")
plt.tight_layout(); fig.savefig(IMG / "primeras_jornadas.png", dpi=150); plt.show()'''),
    ("md", """## Conclusiones

- Tras la jornada 10 la clasificación ya se parece bastante a la final: correlación de **0,78** (en la jornada 1 es 0,41 y en la 19, 0,88).
- El **79 %** de los equipos que están en puestos de Champions en la jornada 10 acaban ahí.
- Pero el líder de la jornada 10 solo acaba campeón en **6 de 13** temporadas, y solo el **54 %** de los equipos en descenso en la jornada 10 acaba bajando. Hay mucho margen para reaccionar.

*Nota:* la posición se calcula con desempate por diferencia de goles, no por enfrentamiento directo como hace LaLiga. Afecta poco a estas conclusiones."""),
])
print("notebooks generados")
