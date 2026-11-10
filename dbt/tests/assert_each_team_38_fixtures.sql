-- Cada equipo debe tener 38 partidos en el calendario de cada temporada.
with sides as (
    select season, home_team as team from {{ ref('stg_matches') }}
    union all
    select season, away_team from {{ ref('stg_matches') }}
)
select season, team, count(*) as fixtures
from sides
group by 1, 2
having count(*) <> 38
