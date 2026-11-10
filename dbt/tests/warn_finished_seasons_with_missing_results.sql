-- Aviso (no error): temporadas ya terminadas a las que les faltan resultados
-- en la fuente. Sirve para detectar huecos en los datos de openfootball.
{{ config(severity='warn') }}

select season, count(*) filter (where not is_played) as missing_results
from {{ ref('stg_matches') }}
group by season
having max(match_date) < current_date
   and count(*) filter (where not is_played) > 0
