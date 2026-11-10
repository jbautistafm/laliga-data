-- Cada temporada debe tener 380 partidos en el calendario (20 equipos, ida y vuelta).
select season, count(*) as fixtures
from {{ ref('stg_matches') }}
group by season
having count(*) <> 380
