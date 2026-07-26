# Motor de Recomendación de Seguros — Colsubsidio

Dado el perfil de una persona, recomienda hasta 3 productos de seguros de Colsubsidio,
ordenados por qué tan bien encajan, cada uno con su score, su nivel de confianza y la
razón concreta por la que se le ofrece. No es un modelo de caja negra: cada recomendación
se puede rastrear hasta la hipótesis de negocio exacta que la disparó, y queda registrada
en una base de datos consultable.

## Contenido

- [Qué hace, en una frase](#qué-hace-en-una-frase)
- [Demo en video](#demo-en-video)
- [Arquitectura](#arquitectura)
- [Cómo funciona el motor](#cómo-funciona-el-motor--motorpy)
- [Instalación y arranque rápido](#instalación-y-arranque-rápido)
- [Las formas de usar el motor](#las-formas-de-usar-el-motor)
- [Reentrenamiento con datos reales](#reentrenamiento-con-datos-reales)
- [Cumplimiento regulatorio](#cumplimiento-regulatorio)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Contrato de datos](#contrato-de-datos)
- [Documentación relacionada](#documentación-relacionada)
- [Regla crítica](#regla-crítica)

## Qué hace, en una frase

Recibe 14 campos de un perfil (necesidad declarada, edad, ciudad, salario, vivienda,
dependientes, mascota, vehículo, etc.), evalúa hipótesis de negocio pesadas
estadísticamente, y devuelve las 3 mejores opciones — nunca un solo producto, para que
el bot conversacional o el asesor tengan margen de elegir cómo presentarlas.

## Demo en video

Video explicando el dashboard del proyecto (métricas en vivo, pesos de las hipótesis,
reentrenamiento en un clic): **[ver video](https://drive.google.com/file/d/1UwDAmCy4KrYyLUwtD033HElANaB5Mqhp/view?usp=sharing)**

## Arquitectura

```
                         ┌──────────────────────────┐
                         │   apuntes/*.md            │
                         │   hipótesis + pesos       │  ← las escribe/firma un humano
                         └────────────┬─────────────┘
                                      │
  perfil de usuario                  ▼
  ────────────────────►        motor.py
  (bot, app, curl, LLM)     recomendar() / registrar()
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
               app.py            server.py         mcp_server.py
          (Streamlit, prueba   (FastAPI, HTTP    (stdio, tool call
           manual + dashboards) para el bot)       para un LLM)
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
                               data/motor.db (SQLite)
                          catalogo · usuarios · recomendaciones
                                      │
                                      ▼
              dashboards/metricas.py / dashboards/pesos.py (en vivo)
```

## Cómo funciona el motor — `motor.py`

`recomendar(perfil: dict) -> dict` corre en capas:

1. **Validación de entrada** — si falta un campo obligatorio o alguno llegó con un
   valor inválido, devuelve `{"error": true, "campos_faltantes": [...], "campos_invalidos": [...], "mensaje": "..."}`
   sin lanzar excepción. Contrato completo: `apuntes/contrato_campos_motor.md`.
2. **Elegibilidad dura** — descarta productos que la persona no puede tener por edad
   (datos reales de las pólizas Chubb), antes de calcular ninguna propensión.
3. **Evaluación de las 6 necesidades** (salud, familia, hogar, movilidad, mascotas,
   crédito) — no solo la que declaró el usuario. Cada hipótesis que se cumple suma su
   **peso entrenado** al score del producto que predice. Los productos de la necesidad
   declarada reciben además un bonus fijo (+0.30), para que domine el ranking sin tapar
   por completo otras opciones relevantes.
4. **Selección final** — junta los candidatos de las 6 necesidades en un solo universo,
   descarta los que quedan por debajo de un piso mínimo (0.10) reemplazándolos por el
   respaldo de su categoría, deduplica (si un producto sale de más de una necesidad se
   queda con el score mayor) y toma los 3 mejores. Cada recomendación trae su razón
   citando la hipótesis exacta que la disparó.

Los pesos salen de `data/modelos/pesos_hipotesis.json` (`scripts/entrenar_motor.py`); si
ese archivo no existe, el motor sigue funcionando con un set de pesos fijos de respaldo
— nunca deja de responder por falta de modelo entrenado.

`motor.registrar(perfil, resultado, canal)` guarda cada perfil y cada resultado en
`data/motor.db` (SQLite). Nunca lanza excepción: si la base no está disponible, el motor
sigue recomendando igual, solo no queda registro.

## Instalación y arranque rápido

```bash
git clone <url-del-repo>
cd seguros_colsubsidio
make setup   # instala dependencias + crea data/motor.db
make run     # levanta la API (8000) + la app unificada (8501)
```

`make help` lista todos los comandos disponibles:

| Comando | Qué hace |
|---|---|
| `make setup` | Primer arranque: instala dependencias + crea la base |
| `make run` | Levanta `server.py` + `app.py` juntos (Ctrl+C detiene los dos) |
| `make server` | Solo la API HTTP (puerto 8000) |
| `make app` | Solo la app unificada — prueba manual + métricas + pesos (puerto 8501) |
| `make dashboard` | Solo el dashboard de métricas, standalone (puerto 8502) |
| `make pesos` | Solo el dashboard de pesos, standalone (puerto 8503) |
| `make mcp` | El servidor MCP (stdio) |
| `make motor` | Corre `motor.py` suelto — 3 casos de prueba por consola |
| `make datos` | Regenera los 5.000 perfiles sintéticos |
| `make entrenar` | Recalcula los pesos de las hipótesis (sintético + real) |
| `make db` | Crea/actualiza `data/motor.db` sin tocar lo que ya haya |
| `make clean` | Borra cachés de Python |

## Las formas de usar el motor

El mismo `motor.py` se consume de cuatro maneras distintas, según quién lo necesite:

| Interfaz | Para quién | Cómo |
|---|---|---|
| `import motor` | Código Python directo | `motor.recomendar(perfil)` |
| `app.py` | Probar el motor a mano, y ver métricas/pesos en la misma página | `make app` → `localhost:8501`, 3 pestañas: Probar el motor / Métricas / Pesos |
| `server.py` | El bot de Nicolás, vía HTTP | `make server` → `POST localhost:8000/recomendar` (`/docs` para probarlo desde el navegador) |
| `mcp_server.py` | Un LLM, como tool call directo (sin HTTP) | `make mcp`, herramienta `recomendar_seguro` — ver `apuntes/PARA_NICOLAS.md` |

`dashboards/dashboard.py` y `dashboards/dashboard_pesos.py` no son formas de *usar* el
motor — son de solo lectura sobre `data/motor.db` y `data/modelos/pesos_hipotesis.json`.
Viven también como pestañas dentro de `app.py` (comparten la misma lógica vía
`dashboards/metricas.py`/`dashboards/pesos.py`, no la duplican) y además corren como
páginas independientes si alguien solo necesita esa vista.

- **Métricas** (`dashboards/metricas.py`): total de recomendaciones, confianza, producto
  y necesidad más frecuentes, distribución por producto/confianza/canal, hipótesis más
  activadas, actividad por hora (en hora de Colombia), últimas 10 recomendaciones.
  Auto-refresco cada 10s.
- **Pesos** (`dashboards/pesos.py`): fecha del último entrenamiento, peso actual de cada
  hipótesis por necesidad (con barra de progreso y nivel por color), ranking global top 10,
  hipótesis débiles (peso < 0.3 o soporte < 10), comparación contra el entrenamiento
  anterior, y un botón para **reentrenar en un clic** sin tocar la terminal.
  Auto-refresco cada 30s.

## Reentrenamiento con datos reales

`scripts/entrenar_motor.py` calcula el peso de cada hipótesis como frecuencia
condicional, combinando **dos fuentes**:

- `data/sintetico/datos_sinteticos.csv` — 5.000 perfiles base.
- `data/motor.db` (`usuarios` JOIN `recomendaciones`) — perfiles reales que ya pasaron
  por `motor.recomendar()` + `motor.registrar()`, sin importar si llegaron por `app.py`,
  `server.py` o `mcp_server.py`.

Los datos reales pesan **3 veces más** que los sintéticos en la fórmula, porque son
comportamiento real, no generado. Antes de cada entrenamiento se respalda el modelo
anterior en `data/modelos/pesos_hipotesis_anterior.json`, así la pestaña de Pesos puede
mostrar qué cambió. Se puede disparar por consola (`make entrenar`) o desde el botón
"Reentrenar ahora" de la pestaña de Pesos — ninguno de los dos requiere reiniciar nada.

## Cumplimiento regulatorio

Las hipótesis de negocio (qué condición predice qué producto) las escribe y firma un
humano — el motor calcula el peso estadístico de cada una, nunca decide una regla nueva
por su cuenta. Cada recomendación queda registrada con el perfil que entró, las
hipótesis que se activaron y el producto que salió. Eso da la trazabilidad y el control
humano sobre el dato que exigen la **Ley 1266** y la **Ley 1581** de tratamiento de
datos personales en Colombia.

## Estructura del proyecto

```
├── motor.py                    Motor de recomendación (recomendar, registrar)
├── server.py                   API FastAPI — POST /recomendar, GET /salud
├── mcp_server.py                Servidor MCP — herramienta recomendar_seguro
├── app.py                      App Streamlit unificada (prueba + métricas + pesos)
├── dashboards/
│   ├── dashboard.py                  Wrapper standalone de metricas.py
│   ├── dashboard_pesos.py            Wrapper standalone de pesos.py
│   ├── metricas.py                   Lógica del dashboard de métricas (compartida)
│   └── pesos.py                      Lógica del dashboard de pesos (compartida)
├── comun/
│   ├── colores.py                    Paleta de marca Colsubsidio (azul/amarillo/grafito)
│   └── zona_horaria.py               Conversión UTC → hora de Colombia para las vistas
├── .streamlit/config.toml      Tema visual (colores de marca), versionado
├── Makefile                    Punto de entrada único (make help)
├── requirements.txt
├── scripts/
│   ├── generar_datos_sinteticos.py   Genera data/sintetico/datos_sinteticos.csv
│   ├── entrenar_motor.py             Calcula data/modelos/pesos_hipotesis.json
│   └── crear_db.py                   Crea/migra el esquema de data/motor.db
├── data/
│   ├── raw/           Dataset original (no tocar)
│   ├── sintetico/     5.000 perfiles sintéticos (entrada de entrenamiento)
│   ├── catalogo/      Catálogo de 24 productos
│   ├── modelos/       pesos_hipotesis.json + pesos_hipotesis_anterior.json
│   └── motor.db       SQLite: catalogo, usuarios, recomendaciones (no versionado)
└── apuntes/
    ├── Hipotesis_Generales_Seguros.md   Hipótesis fuente (las escribe un humano)
    ├── contrato_campos_motor.md         Contrato de campos de recomendar()
    ├── PARA_NICOLAS.md                  Guía de integración (HTTP + MCP)
    ├── bitacora_sesiones.md             Historial de sesiones de trabajo
    └── deprecados/                      Documentación del marco anterior (ignorada en git)
```

## Contrato de datos

Los 14 campos que espera `recomendar()`, sus tipos y valores válidos están en
`apuntes/contrato_campos_motor.md` — es la fuente de verdad, no se duplica acá.
Resumen: `necesidad`, `edad`, `ciudad`, `rango_salarial`, `tipo_vivienda`,
`tiene_dependientes`, `num_dependientes`, `estado_civil`, `usa_drogueria`,
`usa_hoteles`, `usa_agencias`, `tiene_mascota`, `tipo_mascota`, `tipo_vehiculo`.
`server.py` y `mcp_server.py` además esperan `id_interno` (UUID) e `id_contacto`
(correo/teléfono, o `null`) para poder registrar quién es el usuario.

## Documentación relacionada

| Documento | Para qué |
|---|---|
| `apuntes/Hipotesis_Generales_Seguros.md` | Hipótesis de negocio fuente, con su razonamiento |
| `apuntes/contrato_campos_motor.md` | Contrato exacto de campos de entrada/salida del motor |
| `apuntes/PARA_NICOLAS.md` | Cómo conectar el bot al motor, vía HTTP o MCP |
| `apuntes/bitacora_sesiones.md` | Historial de decisiones de cada sesión de trabajo |

## Regla crítica

Las hipótesis las escribe un humano. El motor las consume, no las inventa.
