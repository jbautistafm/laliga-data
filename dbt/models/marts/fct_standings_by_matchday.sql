-- Clasificación acumulada de cada equipo tras cada jornada.
-- Desempate: puntos, diferencia de goles y goles a favor. LaLiga usa el
-- enfrentamiento directo antes que la diferencia de goles, así que en casos
-- de empate a puntos la posición puede diferir de la oficial.
with matchdays as (
    select distinct season, matchday from {{ ref('int_team_matches') }}
),

teams as (
    select distinct season, team from {{ ref('int_team_matches') }}
),

grid as (
    select t.season, t.team, m.matchday
    from teams t join matchdays m using (season)
),

cumulative as (
    select
        g.season, g.team, g.matchday,
        count(tm.match_id)                         as played,
        coalesce(sum(tm.points), 0)                as points,
        count(*) filter (where tm.result = 'V')    as wins,
        count(*) filter (where tm.result = 'E')    as draws,
        count(*) filter (where tm.result = 'D')    as losses,
        coalesce(sum(tm.goals_for), 0)             as goals_for,
        coalesce(sum(tm.goals_against), 0)         as goals_against
    from grid g
    left join {{ ref('int_team_matches') }} tm
        on tm.season = g.season and tm.team = g.team and tm.matchday <= g.matchday
    group by 1, 2, 3
)

select
    *,
    goals_for - goals_against as goal_difference,
    rank() over (
        partition by season, matchday
        order by points desc, goals_for - goals_against desc, goals_for desc
    ) as position
from cumulative
