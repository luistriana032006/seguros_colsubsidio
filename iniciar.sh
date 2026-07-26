#!/usr/bin/env bash
# Arranca los tres procesos del proyecto:
#   - server.py    API FastAPI del motor (puerto 8000, docs en /docs)
#   - dashboard.py Landing de métricas, lee data/motor.db en vivo (puerto 8502)
#   - app.py       Demo Streamlit para probar el motor a mano (puerto 8501)
#
# Uso:  ./iniciar.sh
# Ctrl+C detiene los tres procesos juntos.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# Evita el prompt interactivo de bienvenida de Streamlit ("Email:") que
# aparece la primera vez que se corre en una máquina y bloquea la terminal
# esperando input. Streamlit lo activa cuando no existe este archivo de
# credenciales, sin importar variables de entorno — hay que crearlo.
mkdir -p ~/.streamlit
if [ ! -f ~/.streamlit/credentials.toml ]; then
  printf '[general]\nemail = ""\n' > ~/.streamlit/credentials.toml
fi

echo "Verificando dependencias..."
python3 -m pip install -q -r requirements.txt

PIDS=()
detener_todo() {
  echo ""
  echo "Deteniendo procesos..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap detener_todo EXIT INT TERM

echo "Levantando el servidor del motor en http://localhost:8000 (docs en http://localhost:8000/docs) ..."
python3 server.py &
PIDS+=("$!")

echo "Levantando el dashboard de métricas en http://localhost:8502 ..."
python3 -m streamlit run dashboard.py --server.port 8502 &
PIDS+=("$!")

echo "Levantando la demo en http://localhost:8501 ..."
python3 -m streamlit run app.py --server.port 8501 &
PIDS+=("$!")

wait
