-- Partidos jugados con su resultado (1X2), al descanso y al final.
select
    match_id, season, season_start_year, matchday, match_date,
    home_team, away_team,
    home_goals, away_goals, home_goals_ht, away_goals_ht,
    home_goals + away_goals as total_goals,
    case when home_goals > away_goals then 'local'
         when home_goals = away_goals then 'empate'
         else 'visitante' end as outcome,
    case when home_goals_ht is null then null
         when home_goals_ht > away_goals_ht then 'local'
         when home_goals_ht = away_goals_ht then 'empate'
         else 'visitante' end as outcome_ht,
    is_behind_closed_doors
from {{ ref('stg_matches') }}
where is_played
