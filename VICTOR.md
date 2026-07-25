# VICTOR.md — para quien retoma este proyecto

Este documento existe para que puedas entender **todo el proyecto sin tener que reconstruir el
contexto conversación por conversación**. Léelo de principio a fin antes de tocar código — cada
sección tiene un puntero al documento con el detalle completo si lo necesitás.

---

## 1. Qué es esto, en una frase

Un **motor genérico de reglas de propensión**: recibe un perfil de persona, la ruta a un
dataset, y la ruta a un archivo de hipótesis (reglas de negocio), y devuelve qué categoría de
producto recomendarle y por qué — con las reglas exactas que se activaron, no una caja negra.

Nació como el motor de recomendación de seguros para el Hackathon Colsubsidio × 30X, y en la
última sesión se generalizó para no depender de ningún dominio específico. **Las dos cosas
conviven hoy**: el caso de Colsubsidio sigue siendo un ejemplo de uso real del motor genérico,
no algo que se perdió.

## 2. ⚠️ Esto NO es RAG — aclaración importante

Si ves `seguros.db` y pensás "ah, esto es la base vectorial del RAG", **no lo es**. No hay
embeddings, no hay búsqueda semántica, no hay vector store en ningún lugar de este repo.

`seguros.db` es un **log de auditoría transaccional**: cada vez que se llama a `recomendar()`,
se guarda el perfil que entró y el resultado completo que salió, para poder responder después
"¿por qué se le recomendó X a esta persona el domingo?". La recomendación **ya está calculada**
cuando se escribe en la base — la base no participa del cálculo, solo lo registra.

La decisión de **no usar retrieval/vector DB** fue deliberada desde el principio del proyecto
(ver `CLAUDE.MD`, sección de arquitectura): el requisito no negociable del reto es que la
lógica sea explicable — "nada de caja negra". Con reglas evaluadas directo contra columnas, cada
recomendación se justifica con la regla exacta que la disparó. Un retrieval semántico no da esa
garantía.

Si en algún momento el proyecto necesita RAG de verdad (por ejemplo, para que un bot busque en
fichas de producto redactadas en prosa libre), es una pieza **aparte**, no una evolución de
`seguros.db`.

## 3. Cómo correr esto en menos de 2 minutos

```bash
pip install -r requirements.txt
streamlit run app.py
# o: ./iniciar.sh
```

Levanta en `http://localhost:8501`. Elegís un dataset y un archivo de hipótesis de los
dropdowns, armás un perfil, le das a "Recomendar". Ver `README.md` para más detalle.

## 4. Arquitectura actual

```
motor.py          <- el motor genérico. recomendar(perfil, ruta_dataset, ruta_hipotesis)
app.py             <- demo Streamlit, agnóstica de dominio
seguros.db         <- log de auditoría (SQLite). Se regenera solo, no hace falta versionarlo.
data/
  raw/             <- el .xlsx original de Colsubsidio (fuente, nunca se modifica)
  processed/       <- 6 CSV derivados del pipeline de lote de Colsubsidio (ver §6)
  catalogo/        <- catálogo de 24 productos de seguros + reglas ya estructuradas
  datasets/         <- datasets de prueba del motor genérico (ej. clientes_socioeconomico.json)
  hipotesis/        <- archivos de reglas para el motor genérico (uno por caso de uso)
scripts/           <- los 4 scripts del pipeline de lote de Colsubsidio (no hacen falta para la demo)
apuntes/           <- toda la documentación de decisiones, sesión por sesión (ver §7)
```

**Regla de oro:** `motor.py` y `app.py` no deben tener ningún nombre de columna ni categoría de
negocio hardcodeado. Si necesitás una regla nueva, va en un archivo JSON de `data/hipotesis/`,
no en el código Python. Verificarlo es un grep:

```bash
grep -niE "RANGO_SALARIAL|DROGUERIA|Colsubsidio|Credito|CHUBB" motor.py app.py
# debe dar 0 resultados
```

### El formato de una hipótesis (`data/hipotesis/*.json`)

```json
{"columna": "numero_hijos", "operador": ">", "valor": 0, "categoria_destino": "Vida y Familia"}
```

Operadores válidos: `==`, `>`, `<`, `>=`, `<=`, `in`. Para reglas compuestas (AND de varias
columnas — no estaba en el formato original, se agregó porque hacía falta):

```json
{"condiciones": [
    {"columna": "numero_hijos", "operador": "==", "valor": 0},
    {"columna": "estado_civil", "operador": "==", "valor": "Soltero"}
  ],
  "categoria_destino": "Protección Personal"}
```

El peso de cada regla **no se define a mano**: se calcula automáticamente como la frecuencia
real de esa condición en el dataset (`filas que cumplen / total`). Si esa frecuencia es menor a
5%, el peso se fuerza a 0.01 (existe, pero pesa casi nada).

## 5. Qué se pierde al pasar de un motor específico a uno genérico

Esto es importante y no está oculto en ningún lado: el motor genérico **no puede expresar todo
lo que el motor viejo (específico de Colsubsidio) sí tenía**. Concretamente:

- Pesos graduados por valor (ej. 12 pesos distintos según el bucket de salario) — el genérico
  solo soporta "cumple / no cumple", un peso por regla.
- Reglas compuestas con OR real entre grupos (el genérico solo tiene AND dentro de una regla).
- Un operador de "columna no nula" (presencia como señal en sí misma) — no existe en el esquema.
- Una regla que aplique a todas las filas sin condición ("base universal").
- Pesos negativos (penalizaciones).

El caso de prueba `data/hipotesis/hipotesis_colsubsidio_ejemplo.json` es la mejor traducción
posible al esquema genérico, pero **no reproduce exactamente los números del motor viejo** — el
propio archivo JSON documenta, campo por campo, qué se perdió y por qué (`_README_LIMITACIONES`).
Detalle completo con las 3 pruebas de validación: **`RESUMEN_SESION.md`**.

## 6. El pipeline de lote de Colsubsidio (el origen de todo esto)

Antes de que existiera el motor genérico, hubo un pipeline completo procesando las 500.000 filas
del dataset de afiliados de Colsubsidio. Ese trabajo **no se descartó** — sigue siendo el
material de referencia para el caso de uso de seguros, y los CSV que produjo viven en
`data/processed/`. En orden:

1. **Limpieza** (`scripts/limpieza_rango_salarial.py`) — unificó dos esquemas de bucketing de
   salario mezclados en la columna original.
2. **Etiquetado** (`scripts/etiquetado_hipotesis.py`) — calculó un score de propensión por cada
   una de las 5 categorías de seguro para las 500.000 filas (3 iteraciones: V1/V2/V3).
3. **Estructuración de hipótesis** (`scripts/estructurar_hipotesis.py`) — convirtió las
   hipótesis de negocio (escritas en prosa en `apuntes/Hipotesis_Generales_Seguros.md`) a un
   CSV parseable.
4. **Emparejamiento de producto** (`scripts/emparejar_producto.py`) — asignó, a cada persona, un
   producto específico del catálogo de 24 (`data/catalogo/catalogo_productos.csv`), no solo una
   categoría genérica.

Cada uno de estos 4 pasos tiene su propio documento de decisiones en `apuntes/` — no repitas
este trabajo sin leerlos primero (ver §7).

## 7. Cómo está documentado este proyecto — reglas para seguir documentando

Este proyecto se construyó bajo un método explícito de documentación (`reglas_documentacion_agent.md`,
en la raíz — léelo, es corto). Las reglas más importantes, resumidas:

- **Antes de empezar una tarea:** si hay un documento de contexto del proyecto, usalo como mapa.
  No releas todo el repo para reconstruirlo. Ese documento acá es `CLAUDE.MD`.
- **Identificá qué NO entra en el bloque de trabajo actual** antes de arrancar. No "mejores"
  cosas fuera de ese alcance sin avisar primero.
- **Reportá qué tocaste y por qué**, qué errores encontraste, y si resolviste algo distinto a lo
  pedido — marcado explícitamente como decisión propia, no mezclado con el pedido original.
- **Señal de alerta:** dos fallos seguidos en lo mismo → parar, instrumentar, no improvisar una
  tercera hipótesis a ciegas.
- **Nunca dejes un documento de contexto desactualizado** después de un cambio que lo invalida.

### Los 4 documentos que sostienen todo esto

| Documento | Qué contiene | Cuándo mirarlo |
|---|---|---|
| **`CLAUDE.MD`** | Contexto del proyecto, decisiones ya tomadas, pendientes | Siempre, antes de tocar nada |
| **`apuntes/linea_de_vida_archivos.md`** | Orden cronológico de qué archivo se creó/movió/iteró y cuándo — **sin el porqué**, solo el qué y cuándo | Para saber si un archivo es el vigente o quedó superado |
| **`apuntes/decisiones_*.md`** (uno por bloque de trabajo) | El razonamiento completo de cada decisión: diagnóstico, criterio, verificación, decisiones propias marcadas aparte | Antes de tocar la parte del sistema que ese documento cubre |
| **`RESUMEN_SESION.md`** | Snapshot de la última sesión grande (el refactor a motor genérico): qué se construyó, qué se decidió sin que estuviera explícito, qué pruebas pasaron, qué quedó pendiente | Para retomar exactamente donde quedó |

### Si vas a seguir trabajando en esto

1. Actualizá `apuntes/linea_de_vida_archivos.md` con una entrada nueva por cada sesión de
   trabajo — es un registro append-only, no se reescribe lo viejo.
2. Si tomás una decisión que no estaba explícitamente pedida (un umbral, un formato, una
   interpretación de algo ambiguo), marcala como tal en el código o en un documento — no la
   mezcles como si fuera parte del pedido original. Es lo que hace que este proyecto sea
   auditable en vez de una caja negra de decisiones invisibles.
3. Antes de asumir que algo "no existe" o "está roto", verificá con el sistema de archivos real
   — varias veces en este proyecto una referencia asumida terminó no correspondiendo al estado
   real del repo (ver `apuntes/decisiones_producto_especifico.md` § 16.1 para un ejemplo
   concreto de esto pasando y cómo se manejó).

## 8. Qué falta / dónde está débil hoy

- `README.md` describe la interfaz vieja de la demo (5 botones de casos de prueba); la interfaz
  actual usa selectores de dataset/hipótesis. No está actualizado.
- `seguros.db` no tiene `.gitignore` — al ser un log que crece con cada uso, probablemente no
  debería versionarse tal cual. Ver `.gitignore` de este commit para la decisión que se tomó.
- El contrato de campos con el bot conversacional (Nicolás) está en
  `apuntes/integracion con nicolas.md` — confirmalo antes de asumir los nombres de campo del
  perfil de entrada.
- Los CSV de `data/processed/` pesan hasta 113 MB cada uno — **no están en este repo de Git**
  (ver `.gitignore`), porque exceden el límite de 100 MB de GitHub. Si los necesitás, pedile a
  quien te pasó el proyecto que te los comparta aparte, o regeneralos corriendo el pipeline de
  `scripts/` en orden (§6) a partir de `data/raw/Usos_Productos_Afiliados_SIN_ID.xlsx`.
