#!/usr/bin/env bash
# Arranca la demo del motor de recomendación (Streamlit + motor.py).
# No hay backend FastAPI en este repo por decisión de tiempo (ver CLAUDE.MD,
# decisión #5) — "el backend" hoy es esta app Streamlit.
#
# Uso:  ./iniciar.sh
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

echo "Levantando la demo en http://localhost:8501 ..."
exec python3 -m streamlit run app.py "$@"
