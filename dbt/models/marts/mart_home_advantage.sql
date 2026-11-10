-- Ventaja de jugar en casa por temporada, separando los partidos sin público.
select
    season,
    season_start_year,
    is_behind_closed_doors,
    count(*)                                                  as matches,
    avg(case when outcome = 'local' then 1.0 else 0 end)      as home_win_rate,
    avg(case when outcome = 'empate' then 1.0 else 0 end)     as draw_rate,
    avg(case when outcome = 'visitante' then 1.0 else 0 end)  as away_win_rate,
    avg(home_goals)                                           as avg_home_goals,
    avg(away_goals)                                           as avg_away_goals,
    avg(case outcome when 'local' then 3 when 'empate' then 1 else 0 end)     as avg_home_points,
    avg(case outcome when 'visitante' then 3 when 'empate' then 1 else 0 end) as avg_away_points
from {{ ref('fct_matches') }}
group by 1, 2, 3
