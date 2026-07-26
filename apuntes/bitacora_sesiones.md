# Bitácora de sesiones

Registro de trabajo por sesión, siguiendo el Método AR (`reglas_documentacion_agent.md`).
Cada sesión se agrega como entrada nueva al final — este documento no se reescribe entero.

---

## Sesión 1 — 2026-07-25 — Reseteo del repo + generación de datos sintéticos

### Qué se pidió
Dos tareas encadenadas en la misma sesión:
1. Reseteo completo del repo: archivar documentación del marco anterior, borrar código/datos que ya no aplican, crear la estructura nueva (`data/sintetico/`, `data/modelos/`, `scripts/`), y reemplazar `README.md`.
2. Crear `scripts/generar_datos_sinteticos.py`: genera 5.000 perfiles sintéticos de usuarios en `data/sintetico/datos_sinteticos.csv`, siguiendo las hipótesis de `apuntes/Hipotesis_Generales_Seguros.md` y el catálogo de `data/catalogo/catalogo_productos.csv`.

### Qué se tocó y por qué

**Reseteo:**
- Movidos a `apuntes/deprecados/`: `db.md`, `decisiones_etiquetado_hipotesis.md`, `decisiones_limpieza_rango_salarial.md`, `decisiones_producto_especifico.md`, `exploracion_dataset_nuevo.md`, `integracion con nicolas.md`, `linea_de_vida_archivos.md`, `RESUMEN_SESION.md`, `VICTOR.md`, `CLAUDE.MD`, `reglas_documentacion_agent.md` — documentación del marco de propensión anterior (motor basado en reglas SI/ENTONCES sobre la base de 500.000 afiliados), ya no aplica al marco nuevo.
- Eliminados: `motor.py`, `app.py`, `seguros.db`, los 5 scripts de lote del marco anterior (`limpieza_rango_salarial.py`, `etiquetado_hipotesis.py`, `estructurar_hipotesis.py`, `emparejar_producto.py`, `generar_dataset_sintetico.py`), `data/catalogo/hipotesis_producto_estructuradas.csv`, `data/hipotesis/*.json` (3 archivos), `data/datasets/clientes_socioeconomico.json`, `data/processed/` completa (6 CSV).
- Creadas (con `.gitkeep`): `data/sintetico/`, `data/modelos/`, `scripts/` (quedó vacía tras el borrado, necesitaba el placeholder para que git la trackee).
- `README.md` reemplazado por el contenido nuevo dado por el usuario (contrato de datos con el bot, estructura de carpetas nueva, regla crítica de que las hipótesis las escribe un humano).

**Generación de datos sintéticos:**
- Se leyeron primero `apuntes/Hipotesis_Generales_Seguros.md` (hipótesis fuente, con sus notas de solapamiento entre reglas) y `data/catalogo/catalogo_productos.csv` (24 productos), antes de escribir código, según lo pedido.
- `scripts/generar_datos_sinteticos.py` genera 5.000 filas en tres franjas de conteo fijo (no probabilístico): 3.500 construidas para cumplir una hipótesis puntual → producto de esa hipótesis; 1.000 con perfil sin construir a propósito → producto de respaldo de una categoría elegida al azar; 500 completamente aleatorias → producto elegido al azar entre los 15 productos elegibles, sin relación con el perfil.
- El pool de "productos elegibles" para la franja de ruido se calcula leyendo `catalogo_productos.csv` y restando los 9 productos de declaración directa (en vez de hardcodear una lista aparte) — evita que el script y el catálogo se desincronicen.
- Salida: `data/sintetico/datos_sinteticos.csv` (5.000 filas, 17 columnas, separador coma, UTF-8).

### Decisiones propias (no explícitas en el pedido original)

- **Conflicto de nombres de carpeta detectado antes de tocar nada:** ya existía `apuntes/apuntes_deprecados/` (sin trackear en git, con 8 archivos movidos por fuera de git) que no coincidía ni en nombre (`apuntes/deprecados/` pedido) ni en el listado de archivos con la instrucción del reseteo. Se preguntó al usuario en vez de decidir solo — resolución: renombrar la carpeta existente y dejar los 2 archivos extra (`nomenclatura_afiliados.md`, el `.docx`) donde estaban.
- Limpieza adicional no pedida explícitamente: se borraron `__pycache__/` (raíz y `scripts/`) por ser bytecode huérfano de los scripts eliminados, y las carpetas `data/hipotesis/` y `data/datasets/` que quedaron vacías tras borrar su único contenido.
- Tasas base para campos booleanos/categóricos sin cifra especificada en el pedido ni en las fuentes leídas (`tiene_dependientes`, `usa_drogueria`, distribución de `tipo_vivienda`, `estado_civil`, `tipo_vehiculo`, split perro/gato/otro dentro de "tiene mascota"): se asumieron valores razonables para la demo, documentados como comentario `supuestos_demo` directamente en el script — no hay dato duro que los respalde.
- Filas de las tres franjas mezcladas (shuffle) antes de guardar, para que el CSV no quede en bloques consecutivos por franja — no afecta la distribución, solo el orden.
- Columnas booleanas exportadas como texto `"true"/"false"` en minúscula (en vez del `True`/`False` por defecto de pandas), para que el CSV coincida con la convención de tipos del contrato de datos documentado en el `README.md`.
- Construcción de la partición 70/20/10 con conteos exactos (3.500/1.000/500) en vez de muestreo probabilístico por fila — cumple el ±2% de tolerancia pedido de forma exacta (0% de desviación), ya que el enunciado dio números exactos, no aproximados.

### Verificación

El script valida antes de guardar (y lanza `ValueError` si algo falla, sin escribir CSV parcial):
- Cero filas con `producto_comprado` nulo.
- Cero productos de declaración directa presentes en `producto_comprado`.
- Las tres franjas dentro de ±2% del objetivo.

Corrida real (ver salida completa en consola de la sesión): 5.000 filas, 70.0%/20.0%/10.0% exacto, todas las verificaciones pasaron, tasa de mascota 69.4% (objetivo DANE 67%), `usa_hoteles` 3.12% y `usa_agencias` 2.02% (dentro de los topes de 5%/3% pedidos), cero productos excluidos.

Para reproducir: `python3 scripts/generar_datos_sinteticos.py` desde la raíz del repo (usa rutas relativas al archivo del script, no depende del directorio actual). Semillas fijas (`random.seed(42)`, `np.random.seed(42)`) — misma corrida, mismo resultado.

### Qué falta / qué verificar en la próxima sesión

- Nada quedó pendiente ni roto dentro del alcance pedido en esta sesión.
- El motor de recomendación en sí (equivalente al `motor.py` del marco anterior, pero adaptado al nuevo contrato de datos y a `data/sintetico/`) todavía no existe — es el siguiente hueco lógico según la estructura nueva del `README.md`. **Resuelto en [[Sesión 2]].**
- `data/modelos/` sigue vacía (solo `.gitkeep`) — no se entrenó nada en esta sesión, solo se generaron los datos sintéticos de entrada.
- Ningún cambio de esta sesión está commiteado todavía (queda en el working tree).

---

## Sesión 2 — 2026-07-25 — `motor.py`: motor de recomendación

### Qué se pidió
Crear `motor.py` en la raíz: `recomendar(perfil: dict) -> dict`, motor de propensión en tres capas (elegibilidad dura por edad → score por hipótesis → selección final), sobre el nuevo contrato de datos (campo `necesidad` explícito en el perfil, a diferencia del motor del marco anterior que no lo tenía).

### Qué se tocó y por qué
- Se leyeron `apuntes/Hipotesis_Generales_Seguros.md`, `data/catalogo/catalogo_productos.csv` y las primeras filas de `data/sintetico/datos_sinteticos.csv` antes de escribir código, según lo pedido.
- `motor.py` (nuevo, raíz del repo): implementa las tres capas tal como se pidieron —
  - CAPA 1: `_productos_no_elegibles_por_edad()` filtra AP-CHUBB-01 / APDIG-CHUBB-01 / ONCO-CHUBB-01 fuera de rango de edad, antes de sumar cualquier score.
  - CAPA 2: `HIPOTESIS` — un dict por `necesidad` con las reglas SI/ENTONCES dadas, cada una con su condición, delta de score, candidatos y descripción (para armar `hipotesis_activadas`).
  - CAPA 3: `_seleccionar()` — producto_principal por score más alto, desempate por más campos `estado_*` verificados en el catálogo, producto_alternativa solo si el segundo tiene `estado_precio == "verificado"`, y caída a producto de respaldo si nadie supera 0.3.
- `CATALOGO` se carga una sola vez al importar el módulo (`pd.read_csv(...).set_index("producto_id")`); `categoria`, `estado_precio` y el conteo de campos verificados se leen siempre de ahí, nunca hardcodeados.

### Decisiones propias (no explícitas en el pedido original)
- **Validación de integridad al importar el módulo:** se recolectan todos los IDs de producto mencionados en `HIPOTESIS`, `ELEGIBILIDAD_DURA` y `PRODUCTOS_RESPALDO` y se comparan contra el índice del catálogo; si falta alguno, el import falla con `ValueError` inmediatamente (fail-fast), en vez de descubrirlo en producción con un `KeyError` a mitad de una recomendación.
- El pedido dice "sin hardcoding de IDs de producto en la lógica — léelos del catálogo". Los IDs de las hipótesis (qué producto gana con qué condición) sí quedan como literales en `HIPOTESIS`, porque son la regla de negocio en sí — no existe columna en `catalogo_productos.csv` que la codifique. Lo que sí se lee siempre del catálogo (nunca duplicado a mano) es `categoria`, si el precio está verificado, y el conteo de campos verificados para desempates. Está documentado como decisión explícita en el docstring del módulo.
- El ajuste "SI ciudad = Bucaramanga → score -0.2" (hipótesis de mascotas) no traía candidato asociado en el pedido. Se interpretó como un ajuste posterior sobre los candidatos de mascotas ya acumulados (PET-SEG-01 y/o PET-PREP-01), no como una regla nueva independiente — si no hay ningún candidato de mascotas todavía, el ajuste no tiene nada sobre qué aplicarse y no se dispara.
- `producto_alternativa`: se implementó literal — es el segundo candidato por score, y solo se incluye si ESE candidato específico tiene precio verificado (no se busca más abajo en el ranking un tercero que sí lo tenga).
- **Bug propio detectado y corregido en la misma sesión, dos intentos:** en el primer borrador, el campo `razon` citaba el score crudo sin capar (`score_final`, ej. 1.40 en el Caso 3 porque MOTO-01 acumuló +0.9 y +0.5) mientras el campo `score` sí iba capado a 1.0 por el contrato ("float entre 0 y 1") — el texto y el dato quedaban contradictorios en la misma respuesta. Se corrigió reutilizando el mismo valor ya redondeado y capado (`score_reportado`) tanto en `score` como en el texto de `razon`. Verificado re-corriendo los 3 casos de prueba.

### Verificación
Los 3 casos de prueba pedidos corren dentro de `if __name__ == "__main__"` y se ejecutaron:
- **Caso 1** (droguería activa, necesidad salud): gana **ASMED-01** sobre SALUD-01 pese a empatar en score (0.8 cada uno) — desempate real por campos verificados: SALUD-01 tiene 0 campos `verificado` en el catálogo, ASMED-01 tiene 2 (`aseguradora`, `precio`). Confianza alta, sin alternativa (SALUD-01 no tiene precio verificado).
- **Caso 2** (salario medio-alto 6_8, edad 45, necesidad familia): gana **VIDAAH-01** (0.9, alta), alternativa **VIDA-01** (0.6, con precio verificado en catálogo).
- **Caso 3** (ciudad Soacha, salario bajo, necesidad movilidad): gana **MOTO-01** con score crudo 1.4 (dos hipótesis: salario+ciudad periférica, y tipo_vehiculo=moto), reportado capado a 1.0, confianza alta, sin alternativa (BICI-01 quedó segundo con 0.6 pero no se evaluó su precio porque el flujo de respaldo no aplica aquí — el segundo candidato real ya perdía frente al umbral de selección normal).

Ningún caso lanzó excepción. El bloque `try/except` de `recomendar()` no se ejercitó con estos 3 casos (los tres tienen `necesidad` válida) — queda sin probar en esta sesión el camino de fallback ante `necesidad` inválida o perfil malformado.

Para reproducir: `python3 motor.py` desde la raíz del repo.

### Qué falta / qué verificar en la próxima sesión
- No se probó el camino de excepción interna (`necesidad` inválida, perfil sin campos esperados, `edad` no numérica, etc.) — los 3 casos pedidos son todos "camino feliz". **Parcialmente resuelto en [[Sesión 4]]** (validación de entrada explícita, aunque no es lo mismo que forzar el `except` interno).
- El motor todavía no se corrió contra `data/sintetico/datos_sinteticos.csv` fila por fila para ver paridad o distribución de recomendaciones a escala — solo los 3 perfiles de prueba manuales.
- `data/modelos/` sigue vacía — este motor es de reglas, no de modelo entrenado; si en algún momento se espera algo serializado ahí, es un paso aparte todavía no iniciado. **Resuelto en [[Sesión 7]]** (`pesos_hipotesis.json`).
- Ningún cambio de esta sesión está commiteado todavía (queda en el working tree).

---

## Sesión 3 — 2026-07-25 — `app.py` (interfaz Streamlit de prueba manual) + fix de `iniciar.sh`

### Qué se pidió
Interfaz Streamlit para probar `motor.recomendar()` manualmente. El primer pedido incluía una Sección 3 con 7 botones de casos de prueba precargados y la exigencia de usar callbacks con `st.session_state` (no `st.form`); ese pedido se interrumpió a mitad de camino (ya había leído `motor.py` y el catálogo, pero no había escrito código todavía) y el usuario lo reemplazó por una versión más simple: solo Sección 1 (formulario) y Sección 2 (resultado), sin los botones de casos de prueba. En un mensaje aparte se pidió además arreglar `iniciar.sh` para que funcionara.

### Qué se tocó y por qué
- `app.py` (nuevo, raíz): formulario con los 14 campos del perfil en el orden pedido (sin `st.form`, tal como se exigió). Botón "Recomendar" que arma el perfil, llama a `motor.recomendar()` y guarda el resultado en `st.session_state`. Sección de resultado: producto principal/alternativa con nombre legible + ID, categoría, confianza con color (`st.success`/`st.warning`/`st.error` para alta/media/baja), score con `st.progress`, lista de hipótesis activadas, razón en `st.info`. Cualquier excepción de `recomendar()` se atrapa y se muestra con `st.error()`.
- `iniciar.sh`: en realidad ya funcionaba (instala `requirements.txt`, evita el prompt de bienvenida de Streamlit creando `~/.streamlit/credentials.toml`, levanta `app.py` en `localhost:8501`) — lo único roto era un comentario que citaba `CLAUDE.MD`, archivo que ya no está en la raíz desde el reseteo de [[Sesión 1]] (se movió a `apuntes/deprecados/`). Se corrigió el comentario para que no señale a algo que ya no existe ahí.

### Decisiones propias (no explícitas en el pedido original)
- `catalogo_productos.csv` no tiene una columna `nombre` (como decía literalmente el pedido) sino `nombre_producto` — se usó la columna real sin bloquear a preguntar, avisando al usuario al reportar el resultado.
- Confianza mostrada con cajas de color (`st.success`/`warning`/`error`) en vez de markdown con spans de color (`:green[...]`) — más robusto visualmente y no depende de una sintaxis de color específica de una versión de Streamlit.

### Verificación
`streamlit run app.py` corrido en modo headless: compila sin errores, responde HTTP 200, log del servidor sin tracebacks.

### Qué falta / qué verificar en la próxima sesión
- No se probó interactivamente en navegador — solo arranque headless + compilación + HTTP 200. No se verificó el layout visual real.
- Ningún cambio de esta sesión está commiteado todavía.

---

## Sesión 4 — 2026-07-25 — Validación de entrada en `motor.py` + `apuntes/contrato_campos_motor.md`

### Qué se pidió
Dos cosas: (1) agregar `_validar_perfil(perfil)` a `motor.py`, llamada antes de cualquier otra lógica dentro de `recomendar()`, que devuelve un JSON de error específico (`campos_faltantes`/`campos_invalidos`/`mensaje`) sin lanzar excepción si el perfil no cumple el contrato de 14 campos. (2) crear `apuntes/contrato_campos_motor.md` con contenido exacto dado por el usuario, documentando ese mismo contrato y en qué paso del bot de Nicolás se recoge cada campo.

### Qué se tocó y por qué
- `motor.py`: nuevas constantes `CAMPOS_OBLIGATORIOS`, `NECESIDADES_VALIDAS` (derivada de `PRODUCTOS_RESPALDO`, no duplicada a mano), `TIPOS_VIVIENDA_VALIDOS`, `ESTADOS_CIVILES_VALIDOS`, `TIPOS_MASCOTA_VALIDOS`, `TIPOS_VEHICULO_VALIDOS`. `_validar_perfil()` valida presencia y tipo/rango de los 14 campos, incluidas las reglas cruzadas `num_dependientes` ↔ `tiene_dependientes` y `tipo_mascota` ↔ `tiene_mascota`. `recomendar()` la llama primero y devuelve su resultado de error tal cual si no es `None`, antes de tocar el resto de la lógica.
- `apuntes/contrato_campos_motor.md` (nuevo): contenido exacto pedido, sin modificaciones.

### Decisiones propias (no explícitas en el pedido original)
- Distinción explícita entre "campo faltante" (la llave no existe en el dict) y "campo inválido" (la llave existe pero el valor no cumple tipo/rango, incluyendo `None` donde no corresponde) — el pedido no marcaba esta frontera, se definió así para que ambas listas no se solapen ni se pisen.
- `_es_entero()` excluye `bool` explícitamente (en Python `bool` es subclase de `int`) para que `True`/`False` nunca cuenten por accidente como `edad` o `num_dependientes` válidos.

### Verificación
Se corrieron los 3 casos de prueba originales de `motor.py` (idénticos a antes, la validación no los rompió), un perfil incompleto (12 `campos_faltantes` detectados), un perfil con 9 valores inválidos distintos (cada uno con su razón puntual), y un perfil válido de control (pasa sin error).

### Qué falta / qué verificar en la próxima sesión
- Ningún cambio de esta sesión está commiteado todavía.

---

## Sesión 5 — 2026-07-25 — `scripts/crear_db.py` + `motor.registrar()`

### Qué se pidió
Crear `scripts/crear_db.py`: arma `data/motor.db` (SQLite) con 3 tablas (`catalogo`, `usuarios`, `recomendaciones`), migrando el catálogo completo a la primera. Agregar `registrar(perfil, resultado, canal="prueba")` a `motor.py`: guarda cada perfil + resultado, nunca lanza excepción, no registra nada si `resultado` trae `"error": true`.

### Qué se tocó y por qué
- `scripts/crear_db.py` (nuevo): `ESQUEMA` con `CREATE TABLE IF NOT EXISTS` para las 3 tablas, con las columnas exactas pedidas. La tabla `catalogo` se migra calculando `campos_verificados` (conteo de columnas `estado_*` == `"verificado"` por fila, vía pandas) — pero solo si la tabla está vacía, para no reinsertar en corridas repetidas.
- `motor.py`: `registrar()` inserta primero en `usuarios`, toma el `lastrowid` como `usuario_id`, e inserta en `recomendaciones` con `hipotesis_activadas` serializado vía `json.dumps`. Ambas filas comparten el mismo `timestamp` ISO. Todo envuelto en un único `try/except` que traga cualquier excepción sin propagarla.

### Decisiones propias (no explícitas en el pedido original)
- Interpretación estricta de "si motor.db ya existe no la sobreescribe": no solo la creación de tablas es idempotente (`IF NOT EXISTS`), sino que la migración del catálogo también se salta si la tabla ya tiene filas — para no arriesgarse a "sobreescribir" en sentido amplio. Efecto secundario: si `catalogo_productos.csv` cambia más adelante, hay que borrar `motor.db` a mano para refrescar esa tabla.
- `perfil.get("id_interno")` / `perfil.get("id_contacto")` con default `None`: estos dos campos no forman parte del contrato de `motor.recomendar()` (`apuntes/contrato_campos_motor.md`), pero sí existen como columnas en `usuarios` — se leen de forma opcional sin fallar si el perfil no los trae.

### Verificación
`crear_db.py` corrido dos veces: la primera crea la DB y migra 24 productos; la segunda detecta que `catalogo` ya tenía 24 y no reinserta. `motor.py` sigue dando los mismos 3 resultados de siempre. `registrar()` probado con un perfil válido (queda 1 fila en `usuarios` y 1 en `recomendaciones`), con un resultado de error (no registra nada), y con entradas malformadas (`None`, dict vacío, resultado sin las llaves esperadas) sin lanzar excepción en ningún caso.

### Qué falta / qué verificar en la próxima sesión
- Ningún cambio de esta sesión está commiteado todavía.

---

## Sesión 6 — 2026-07-25 — `dashboard.py`

### Qué se pidió
Interfaz Streamlit de solo lectura sobre `data/motor.db`, con 7 secciones: métricas globales, distribución de productos, distribución de confianza, actividad en el tiempo, hipótesis más activadas, últimas 10 recomendaciones, distribución por canal. Cache de 10s + botón de refresco manual, gráficos con plotly (no matplotlib), mensaje claro si la DB está vacía o no existe.

### Qué se tocó y por qué
- `dashboard.py` (nuevo, raíz): `cargar_datos()` cacheada con `@st.cache_data(ttl=10)`; botón "Refrescar ahora" que llama a `cargar_datos.clear()`. Si la DB no existe o le faltan las 3 tablas, o si `recomendaciones` está vacía, muestra el mensaje pedido y corta con `st.stop()` antes de intentar renderizar nada más. Las 7 secciones con `plotly.express`: barras horizontales (productos), torta con verde/amarillo/rojo (confianza), línea por hora del día (actividad), tabla de frecuencias desserializando `hipotesis_activadas` con `json.loads` + `Counter`, join `recomendaciones` ↔ `usuarios` para traer `necesidad`/`canal` en la tabla de últimas 10 y en la distribución por canal.
- `motor.py`: se detectó que el bloque `__main__` nunca llamaba a `registrar()` — solo imprimía el resultado de `recomendar()`. Como la verificación pedida dependía explícitamente de que "correr `motor.py` genere 3 registros de prueba" en la DB, se agregó la llamada a `registrar(perfil, resultado, canal="prueba")` dentro del loop de `__main__`.
- `requirements.txt`: se agregó `plotly>=5.20` (no estaba instalado en el entorno; se instaló y se dejó declarado para que no falte en otra máquina).

### Decisiones propias (no explícitas en el pedido original)
- Umbral de "suficientes datos" para el gráfico de actividad por hora: definido arbitrariamente en menos de 5 filas → mensaje "Aún no hay suficientes datos" (el pedido no daba un número concreto).
- Etiquetas del gráfico de productos combinan nombre legible + ID (`"nombre (ID)"`) en vez de solo el ID — no pedido explícitamente, pero consistente con el patrón de legibilidad ya usado en `app.py` ([[Sesión 3]]).

### Verificación
Probado con `motor.db` inexistente (HTTP 200, aparece el mensaje de "aún no ha procesado ninguna recomendación", sin tracebacks en el log). Probado con datos reales siguiendo los pasos pedidos (`crear_db.py` + `motor.py` generando 3 registros): cada una de las 7 secciones se recalculó y verificó manualmente contra esos 3 registros sin excepciones (productos con nombre legible, 100% confianza alta, las 6 hipótesis puntuales, join con `usuarios` correcto, canal `prueba` ×3, sección de actividad mostrando el mensaje de datos insuficientes como se esperaba con solo 3 filas). Al terminar se restauró `data/motor.db` a su estado previo (1 usuario/1 recomendación de una prueba anterior) para no dejar mezclados los registros de esta verificación.

### Qué falta / qué verificar en la próxima sesión
- Ningún cambio de esta sesión está commiteado todavía.

---

## Sesión 7 — 2026-07-25 — `scripts/entrenar_motor.py` + pesos entrenados en `motor.py`

### Qué se pidió
Script que calcula el peso real de cada una de las 18 hipótesis del motor (17 "normales" + 1 con ajuste) a partir de los 5.000 registros sintéticos, con la fórmula peso = (filas que cumplen la condición Y compraron el producto) ÷ (total de filas que compraron ese producto), reglas de piso (0.05), señal mínima si no hay datos (0.01) y ajuste aditivo para `bucaramanga_mascota`, guardando todo en `data/modelos/pesos_hipotesis.json`. Después, actualizar `motor.py` para que cargue esos pesos al iniciar, con fallback a los valores fijos originales si el JSON no existe.

### Qué se tocó y por qué
- `scripts/entrenar_motor.py` (nuevo): `HIPOTESIS_A_CALCULAR` con las 18 condiciones exactas dadas. `_calcular_peso()` evalúa cada condición con `df.eval(condicion, engine="python")` — necesario porque las condiciones usan `in` y `and`, que el motor de evaluación por defecto de pandas no soporta bien. Guarda `pesos_hipotesis.json` con `version`/`fecha_entrenamiento`/`total_registros_entrenamiento`/`pesos` (cada hipótesis con `peso`, `productos`, `soporte`, `total_producto`).
- `motor.py`: `PESOS_FALLBACK` con los 18 valores fijos originales (verificados condición por condición contra `HIPOTESIS_A_CALCULAR` antes de tocar nada, para confirmar que la correspondencia era 1:1). `_cargar_pesos()` lee el JSON y solo lo usa si trae todas las claves esperadas; si no, cae en `PESOS_FALLBACK`. Los `delta` hardcodeados de `HIPOTESIS` y el ajuste `-0.2` de Bucaramanga (hasta ahora fijo, ver [[Sesión 2]]) se reemplazaron por lookups a `PESOS[necesidad][clave]`.

### Decisiones propias (no explícitas en el pedido original)
- Orden de aplicación de las 4 reglas de cálculo: el pedido las listaba sueltas, sin especificar el orden entre la primera (`total=0 → peso=0.01`) y la segunda (`peso<0.05 → piso 0.05`). Se interpretó `0.01` como un caso terminal que NO pasa después por el piso de `0.05` — si el piso lo pisara igual, no tendría sentido que fueran dos constantes distintas en el pedido.
- Para hipótesis con más de un producto candidato (`drogueria_activa` → SALUD-01, ASMED-01), "total de filas que compraron ese producto" se interpretó como la unión de ambos IDs, no un producto aislado — coincide con que ambos comparten el mismo `delta` en `motor.py`.

### Verificación
Top 5 pesos más altos con soporte impresos (`familia.salario_bajo_medio_familia` 0.9594, `hogar.salario_bajo_medio_hogar` 0.9516, `familia.mayor_55` 0.9362, `movilidad.periferia_salario_bajo` 0.9185, `familia.salario_bajo_familia` 0.9143). Los 3 casos de prueba de `motor.py` siguen recomendando los mismos productos con confianza alta (solo cambiaron los scores, no los ganadores). Fallback confirmado: borrando el JSON, `motor.PESOS` vuelve a ser exactamente `PESOS_FALLBACK`. Comparación completa de las 18 hipótesis original vs. entrenado: diferencia absoluta promedio 0.14, máxima 0.46 (`familia.salario_bajo_medio_familia`), mínima 0.001 (`credito.salario_medio_bajo_credito`) — confirma que los pesos entrenados capturan señal real de los datos sintéticos y no son casi idénticos a los originales, como se esperaba dado el ruido del 10%/20% de la generación ([[Sesión 1]]).

### Qué falta / qué verificar en la próxima sesión
- Ninguno de los cambios de las Sesiones 3 a 7 está commiteado todavía (sigue todo en el working tree).

---

## Sesión 8 — 2026-07-25 — `server.py` (API FastAPI sobre el motor)

### Qué se pidió
Servidor FastAPI que expone `motor.recomendar()` como servicio HTTP para que Nicolás le haga POST con el perfil y reciba la recomendación — sin manejar conversación, sesiones, ni los 11 pasos del bot. Modelo Pydantic `PerfilUsuario` con 17 campos y tipos/validaciones exactas. Dos endpoints: `GET /salud` (healthcheck) y `POST /recomendar` (llama a `motor.recomendar()` y luego a `motor.registrar()`, HTTP 422 si el motor devuelve error, HTTP 500 si lanza excepción inesperada, nunca traceback crudo). CORS abierto a todos los orígenes. Arranque con `uvicorn.run("server:app", ..., reload=True)`.

### Qué se tocó y por qué
- `server.py` (nuevo, raíz): `PerfilUsuario(BaseModel)` con `Literal[...]` para los 5 campos de enumeración (`necesidad`, `rango_salarial`, `tipo_vivienda`, `estado_civil`, `tipo_vehiculo`) y `Field(ge=..., le=...)` para los rangos numéricos (`edad` 18-75, `num_dependientes` 0-4) — esto hace que FastAPI/Pydantic rechacen automáticamente con HTTP 422 antes de que el request llegue al código propio. `GET /salud` lee `motor.RUTA_PESOS.exists()` para reportar `"entrenados"` vs `"fallback"`. `POST /recomendar` arma el dict del perfil, llama a `motor.recomendar()` dentro de un `try/except` (HTTP 500 si algo lanza excepción), traduce `resultado["error"] == True` a HTTP 422 con el detalle del motor como `detail`, y si todo sale bien llama a `motor.registrar(..., canal=perfil.canal)` antes de devolver el resultado con HTTP 200.
- `requirements.txt`: se agregaron `fastapi>=0.110.0` y `uvicorn>=0.29.0` (ya estaban instalados en el entorno — 0.135.2 y 0.42.0 respectivamente — pero no declarados).

### Decisiones propias (no explícitas en el pedido original)
- División de responsabilidades entre Pydantic y `motor.py` para la validación: los campos "planos" (tipo, presencia, rangos, membresía de las listas cerradas) quedan a cargo de Pydantic vía `Literal`/`Field` — eso ya produce el HTTP 422 automático que pedía la Prueba 3 sin escribir código propio. La validación cruzada más fina (`tipo_mascota` según `tiene_mascota`, `num_dependientes` según `tiene_dependientes`) se dejó completamente delegada a `motor._validar_perfil()` ([[Sesión 4]]), que ya la implementaba — no se duplicó esa lógica en Pydantic.
- El `try/except` alrededor de `motor.recomendar()` para el HTTP 500 es defensivo por diseño: `motor.recomendar()` ya está construido para nunca lanzar excepción hacia afuera ([[Sesión 2]]), así que en la práctica ese camino no debería dispararse nunca en operación normal — se dejó de todos modos porque el pedido lo exigía explícitamente ("si lanza excepción inesperada").

### Verificación
Las 4 pruebas pedidas, corridas contra el servidor real (`python3 server.py` en background, `curl` contra `127.0.0.1:8000`):
- **Prueba 1** (`GET /salud`): HTTP 200, `{"estado":"ok","version":"v1","motor":"activo","pesos":"entrenados"}`.
- **Prueba 2** (`POST /recomendar` válido): HTTP 200, `producto_principal: "ASMED-01"` (dentro de lo esperado, ASMED-01 o SALUD-01), score 0.89, confianza alta.
- **Prueba 3** (`POST /recomendar` incompleto): HTTP 422, `detail` con los 11 campos faltantes — generado automáticamente por Pydantic, no por código propio.
- **Prueba 4** (verificación en `data/motor.db`): confirmada fila nueva en `usuarios` (`id_interno='test-001'`, `canal='whatsapp'`) y su fila correspondiente en `recomendaciones` (`producto_principal='ASMED-01'`, `confianza='alta'`), mismo `timestamp` en ambas.

`/docs` verificado con HTTP 200 (Swagger UI real, no solo la ruta respondiendo) y `/openapi.json` confirmado como JSON válido. Servidor de prueba detenido al final, sin procesos residuales.

### Qué falta / qué verificar en la próxima sesión
- El camino de HTTP 500 (excepción inesperada de `motor.recomendar()`) no se ejercitó realmente porque `motor.recomendar()` está diseñado para no lanzar nunca — quedaría pendiente forzarlo artificialmente si se quiere probar ese branch específico.
- `reload=True` en `uvicorn.run()` es cómodo para desarrollo pero no es el modo recomendado para lo que sea que se despliegue durante el hackathon — revisar si hace falta un modo de arranque sin autoreload para esa parte.
- Ninguno de los cambios de las Sesiones 3 a 8 está commiteado todavía (sigue todo en el working tree).
