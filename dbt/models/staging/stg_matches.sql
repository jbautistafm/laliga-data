-- Un partido por fila, con nombres de equipo normalizados y un identificador estable.
with source as (
    select * from {{ source('raw', 'matches') }}
),

names as (
    select * from {{ ref('team_names') }}
)

select
    s.season || '-' || lpad(cast(s.matchday as varchar), 2, '0') || '-' || h.team || '-' || a.team as match_id,
    s.season,
    cast(left(s.season, 4) as integer)                  as season_start_year,
    cast(s.matchday as integer)                         as matchday,
    cast(s.match_date as date)                          as match_date,
    h.team                                              as home_team,
    a.team                                              as away_team,
    cast(s.home_goals as integer)                       as home_goals,
    cast(s.away_goals as integer)                       as away_goals,
    cast(s.home_goals_ht as integer)                    as home_goals_ht,
    cast(s.away_goals_ht as integer)                    as away_goals_ht,
    s.home_goals is not null                            as is_played,
    -- Partidos sin público por la COVID-19: desde la reanudación (junio 2020)
    -- hasta el final de la temporada 2020-21.
    cast(s.match_date as date) between date '2020-06-01' and date '2021-06-30' as is_behind_closed_doors
from source s
left join names h on s.home_team_raw = h.team_raw
left join names a on s.away_team_raw = a.team_raw
