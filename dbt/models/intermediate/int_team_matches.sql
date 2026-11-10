-- Dos filas por partido jugado: una desde el punto de vista de cada equipo.
with played as (
    select * from {{ ref('stg_matches') }} where is_played
),

both_sides as (
    select match_id, season, season_start_year, matchday, match_date, is_behind_closed_doors,
           home_team as team, away_team as opponent, 'local' as venue,
           home_goals as goals_for, away_goals as goals_against,
           home_goals_ht as goals_for_ht, away_goals_ht as goals_against_ht
    from played
    union all
    select match_id, season, season_start_year, matchday, match_date, is_behind_closed_doors,
           away_team, home_team, 'visitante',
           away_goals, home_goals,
           away_goals_ht, home_goals_ht
    from played
)

select
    *,
    case when goals_for > goals_against then 'V'
         when goals_for = goals_against then 'E'
         else 'D' end as result,
    case when goals_for > goals_against then 3
         when goals_for = goals_against then 1
         else 0 end as points,
    case when goals_for_ht is null then null
         when goals_for_ht > goals_against_ht then 'V'
         when goals_for_ht = goals_against_ht then 'E'
         else 'D' end as result_ht
from both_sides
