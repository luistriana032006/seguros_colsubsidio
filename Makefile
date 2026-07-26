PYTHON ?= python3

.PHONY: help install setup db datos entrenar motor server dashboard app mcp run clean

help: ## Muestra esta ayuda
	@echo "Motor de recomendación de seguros — comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Instala las dependencias de requirements.txt
	$(PYTHON) -m pip install -r requirements.txt

setup: install db ## Primer arranque: instala dependencias y crea data/motor.db

db: ## Crea/actualiza data/motor.db (catálogo + tablas) -- ver scripts/crear_db.py
	$(PYTHON) scripts/crear_db.py

datos: ## Regenera data/sintetico/datos_sinteticos.csv (5.000 perfiles sintéticos)
	$(PYTHON) scripts/generar_datos_sinteticos.py

entrenar: ## Recalcula data/modelos/pesos_hipotesis.json a partir de los datos sintéticos
	$(PYTHON) scripts/entrenar_motor.py

motor: ## Corre motor.py -- 3 casos de prueba por consola
	$(PYTHON) motor.py

server: ## Levanta la API FastAPI del motor (puerto 8000, docs en /docs)
	$(PYTHON) server.py

dashboard: ## Levanta el dashboard de métricas en vivo (puerto 8502)
	$(PYTHON) -m streamlit run dashboard.py --server.port 8502

app: ## Levanta la demo Streamlit de prueba manual del motor (puerto 8501)
	$(PYTHON) -m streamlit run app.py --server.port 8501

mcp: ## Levanta el servidor MCP (stdio) para que un LLM lo use como herramienta
	$(PYTHON) mcp_server.py

run: ## Levanta server + dashboard + app juntos (./iniciar.sh)
	./iniciar.sh

clean: ## Borra cachés de Python (__pycache__, *.pyc) -- no toca data/motor.db
	find . -type d -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} +
	find . -type f -name "*.pyc" -not -path "./.git/*" -delete

.DEFAULT_GOAL := help
