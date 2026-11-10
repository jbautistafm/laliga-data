-- Qué pasa después del descanso: puntos ganados o perdidos respecto al
-- resultado del minuto 45, por equipo y temporada.
with tm as (
    select * from {{ ref('int_team_matches') }} where result_ht is not null
)

select
    season,
    team,
    count(*)                                                        as matches_with_ht,
    count(*) filter (where result_ht = 'D')                         as losing_at_ht,
    count(*) filter (where result_ht = 'D' and result <> 'D')       as comebacks,
    count(*) filter (where result_ht = 'V')                         as winning_at_ht,
    count(*) filter (where result_ht = 'V' and result <> 'V')       as blown_leads,
    sum(points)                                                     as points,
    sum(case result_ht when 'V' then 3 when 'E' then 1 else 0 end)  as points_if_ended_at_ht,
    sum(points) - sum(case result_ht when 'V' then 3 when 'E' then 1 else 0 end) as second_half_points_delta
from tm
group by 1, 2
