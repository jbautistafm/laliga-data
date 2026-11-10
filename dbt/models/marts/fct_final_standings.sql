-- Clasificación tras la última jornada disponible de cada temporada.
with last_md as (
    select season, max(matchday) as matchday
    from {{ ref('fct_standings_by_matchday') }}
    group by season
)

select s.*,
       s.matchday as last_matchday,
       count(*) over (partition by s.season) as teams
from {{ ref('fct_standings_by_matchday') }} s
join last_md using (season, matchday)
