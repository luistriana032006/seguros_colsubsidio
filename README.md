# Motor de Recomendación de Seguros

Dado el perfil de una persona, recomienda hasta 3 productos de seguros de Colsubsidio,
ordenados por qué tan bien encajan, cada uno con su score, su nivel de confianza y la
razón concreta por la que se le ofrece. No es un modelo de caja negra: cada recomendación
se puede rastrear hasta la hipótesis de negocio exacta que la disparó.

## Qué hace, en una frase

Recibe 14 campos de un perfil (necesidad declarada, edad, ciudad, salario, vivienda,
dependientes, mascota, vehículo, etc.), evalúa un conjunto de hipótesis SI/ENTONCES
pesadas estadísticamente, y devuelve las 3 mejores opciones de esa necesidad — nunca
un solo producto, para que el bot conversacional o el asesor tengan margen de elegir
cómo presentarlas.

## Cómo funciona por dentro — `motor.py`

`recomendar(perfil: dict) -> dict` corre en tres capas:

1. **Validación de entrada** — si falta un campo obligatorio o alguno llegó con un
   valor inválido, devuelve `{"error": true, "campos_faltantes": [...], "campos_invalidos": [...], "mensaje": "..."}`
   sin lanzar excepción. Contrato completo: `apuntes/contrato_campos_motor.md`.
2. **Elegibilidad dura** — descarta productos que la persona no puede tener por edad
   (datos reales de las pólizas Chubb), antes de calcular ninguna propensión.
3. **Hipótesis de propensión** — evalúa reglas SI/ENTONCES específicas de la
   `necesidad` declarada (salud, familia, hogar, movilidad, mascotas o crédito).
   Cada hipótesis que se cumple suma su **peso entrenado** al score del producto
   que predice. Los pesos salen de `data/modelos/pesos_hipotesis.json`
   (`scripts/entrenar_motor.py`, calculados como frecuencia condicional sobre
   los 5.000 perfiles sintéticos); si ese archivo no existe, el motor sigue
   funcionando con un set de pesos fijos de respaldo.
4. **Selección final** — ordena todos los candidatos con score > 0 y se queda con
   los 3 mejores. Si la necesidad no junta 3 candidatos reales, completa las
   posiciones que faltan con productos de respaldo de **otras** categorías
   (marcados con score 0 y confianza baja, para que se distingan de una señal real).

Las hipótesis en sí (qué condición dispara qué producto) las escribió el equipo a
partir de `apuntes/Hipotesis_Generales_Seguros.md` — **el motor las consume, no las
inventa.** Lo único que aprende de los datos es el peso numérico de cada una.

`motor.registrar(perfil, resultado, canal)` guarda cada perfil y cada resultado en
`data/motor.db` (SQLite) — es lo que alimenta el dashboard de métricas. Nunca lanza
excepción: si la base no está disponible, el motor sigue recomendando igual, solo
no queda registro.

## Cómo correrlo

Todo pasa por el `Makefile` — `make help` lista todo, `make setup` es el primer
arranque (instala dependencias + crea `data/motor.db`).

| Comando | Qué hace |
|---|---|
| `make setup` | Primer arranque: instala dependencias + crea la base |
| `make run` | Levanta server + dashboard + app juntos (Ctrl+C detiene los tres) |
| `make server` | Solo la API HTTP (puerto 8000) |
| `make dashboard` | Solo el dashboard de métricas (puerto 8502) |
| `make app` | Solo la demo de prueba manual (puerto 8501) |
| `make mcp` | El servidor MCP (stdio) |
| `make motor` | Corre `motor.py` suelto — 3 casos de prueba por consola |
| `make datos` | Regenera los 5.000 perfiles sintéticos |
| `make entrenar` | Recalcula los pesos de las hipótesis |
| `make db` | Crea/actualiza `data/motor.db` sin tocar lo que ya haya |
| `make clean` | Borra cachés de Python |

## Las 4 formas de usar el motor

El mismo `motor.py` se consume de cuatro maneras distintas, según quién lo necesite:

| Interfaz | Para quién | Cómo |
|---|---|---|
| `import motor` | Código Python directo | `motor.recomendar(perfil)` |
| `app.py` | Probar el motor a mano, perfil por perfil | `make app` → `localhost:8501` |
| `server.py` | El bot de Nicolás, vía HTTP | `make server` → `POST localhost:8000/recomendar` (`/docs` para probarlo desde el navegador) |
| `mcp_server.py` | Un LLM, como tool call directo (sin HTTP) | `make mcp`, herramienta `recomendar_seguro` — ver `apuntes/PARA_NICOLAS.md` |

`dashboard.py` no es una forma de *usar* el motor — es de solo lectura sobre
`data/motor.db`: muestra en vivo (auto-refresco cada 10s) cuántas recomendaciones se
hicieron, qué productos ganan más, distribución de confianza, hipótesis más activadas
y actividad por hora.

## Estructura del proyecto

```
├── motor.py                    Motor de recomendación (recomendar, registrar)
├── server.py                   API FastAPI — POST /recomendar, GET /salud
├── mcp_server.py                Servidor MCP — herramienta recomendar_seguro
├── app.py                      Demo Streamlit de prueba manual
├── dashboard.py                Métricas en vivo sobre data/motor.db
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
│   ├── modelos/       pesos_hipotesis.json (pesos entrenados)
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

## Regla crítica

Las hipótesis las escribe un humano. El motor las consume, no las inventa.
