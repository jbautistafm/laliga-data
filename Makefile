.PHONY: all data transform export app

all: data transform export

data:        ## Descarga los partidos
	python pipeline/download.py

transform:   ## Construye y prueba los modelos SQL
	cd dbt && dbt build --profiles-dir .

export:      ## Exporta las tablas finales a Parquet
	python pipeline/export_marts.py

app:         ## Arranca el dashboard
	streamlit run app/streamlit_app.py
