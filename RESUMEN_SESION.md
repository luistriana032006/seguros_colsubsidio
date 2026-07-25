# Resumen de sesión — motor genérico de reglas

**Fecha:** 2026-07-25
**Objetivo del pedido:** reconstruir `motor.py` (antes específico de Colsubsidio) como un motor
genérico que recibe *perfil + dataset + hipótesis* y no sabe nada de ningún dominio.
**Estado final: completo.** Las 3 pruebas de validación pasaron, Streamlit levanta, `seguros.db`
tiene las 3 tablas con registros reales.

---

## 1. Qué se construyó

- **Motor genérico de reglas** (`motor.py`): función `recomendar(perfil, ruta_dataset, ruta_hipotesis)`.
  Carga cualquier dataset (CSV o JSON), cualquier archivo de hipótesis (columna/operador/valor →
  categoría), calcula el peso de cada regla como su frecuencia real en el dataset, evalúa el
  perfil, y devuelve categoría top/secundaria, score, confianza, reglas activadas/omitidas y
  si requiere escalamiento.
- **Demo Streamlit agnóstica** (`app.py`): selector de dataset, selector de hipótesis, formulario
  que solo pide los campos que las hipótesis elegidas usan.
- **Persistencia en SQLite** (`seguros.db`): cada perfil y cada recomendación completa quedan
  registrados, con las 3 tablas pedidas.
- **Tres datasets/hipótesis de prueba**, para demostrar que el motor es agnóstico de verdad:
  1. El dominio de seguros de Colsubsidio, convertido a caso de prueba (no se perdió, se preservó).
  2. Un dataset sintético socioeconómico (500 clientes) con hipótesis de negocio genéricas.
  3. Una hipótesis inventada en el momento, sobre el mismo dataset sintético, para probar que
     el motor funciona sin tocar código.

## 2. Archivos creados o modificados

| Archivo | Acción |
|---|---|
| `motor.py` | **Reescrito por completo.** Ya no tiene ningún nombre de columna ni categoría de Colsubsidio hardcodeado. |
| `app.py` | **Reescrito.** Selectores de dataset/hipótesis + formulario dinámico. |
| `data/hipotesis/hipotesis_colsubsidio_ejemplo.json` | **Creado.** El dominio de seguros como caso de prueba (Paso 0, antes de tocar nada). |
| `data/datasets/clientes_socioeconomico.json` | **Creado.** 500 registros sintéticos. |
| `data/hipotesis/hipotesis_socioeconomico.json` | **Creado.** Las 8 hipótesis pedidas en el prompt. |
| `data/hipotesis/hipotesis_prueba_c.json` | **Creado.** Hipótesis inventada para la Prueba C. |
| `scripts/generar_dataset_sintetico.py` | **Creado.** Generador reproducible (semilla fija) del dataset sintético, con las 3 correlaciones pedidas. |
| `seguros.db` | **Creado.** SQLite con 3 tablas: `perfiles`, `recomendaciones`, `hipotesis_log`. |
| `CLAUDE.MD` | **Iterado.** Sección de cambio de arquitectura al inicio; el contenido de negocio de Colsubsidio se conserva abajo como documentación de dominio, no se borró. |
| `apuntes/linea_de_vida_archivos.md` | **Iterado.** Iteración 14. |
| `RESUMEN_SESION.md` | **Creado.** Este archivo. |

**No se tocaron:** los scripts de lote (`scripts/limpieza_rango_salarial.py`, `etiquetado_hipotesis.py`,
`emparejar_producto.py`, `estructurar_hipotesis.py`), ni los CSV en `data/processed/` y `data/catalogo/`,
ni `README.md`, ni `iniciar.sh`.

## 3. Decisiones propias (no explícitas en el prompt)

Todas están además documentadas como comentarios `DECISION PROPIA` en el docstring de `motor.py`,
junto al código exacto que implementan:

1. **Formato de regla compuesta (`"condiciones": [...]`).** El prompt especifica un formato
   estrictamente de una columna por regla, pero una de las hipótesis pedidas explícitamente
   (`numero_hijos == 0 AND estado_civil == "Soltero"`) es un AND de dos columnas. Se extendió el
   esquema con una forma alternativa de regla (lista de sub-condiciones, todas deben cumplirse)
   en vez de inventar un parser de texto libre. El formato atómico original sigue funcionando igual.
2. **Nulos vs. no-cumple, dos listas distintas.** El prompt dice "si no la cumple o el campo es
   nulo: omitir". Se interpretó (y se documentó explícitamente por qué) que "omitir" en el
   sentido de "no listar como omisión" aplica solo cuando el dato falta — si el dato existe pero
   no cumple la condición, simplemente no se activa, sin aparecer en ninguna lista especial. Esto
   preserva la distinción explicativa entre "no se pudo evaluar" y "se evaluó y no aplicó", que
   es justo el propósito de `reglas_omitidas`.
3. **Normalización = `min(1.0, suma de pesos activados)`.** El prompt pide "normalizar entre 0 y 1"
   sin dar la fórmula. Se eligió el tope simple (no una redistribución proporcional más compleja)
   porque es la interpretación más directa que cumple la restricción pedida sin inventar de más.
4. **El archivo de hipótesis acepta lista plana O `{"hipotesis": [...]}`.** Permite documentar
   limitaciones/metadata dentro del propio archivo (usado en `hipotesis_colsubsidio_ejemplo.json`)
   sin romper el parser.
5. **Formato de texto legible de las reglas activadas/omitidas:** `"columna op valor → categoria (peso X.XX)"`.
   No estaba especificado el formato exacto, se eligió el más directo para depurar y auditar.
6. **`app.py` intenta castear cada campo del formulario a `int`, luego `float`, y si falla lo deja
   como texto.** El motor compara "tal cual llega" el valor; si el tipo no calza con lo que pide
   la regla, esa regla simplemente no se puede evaluar (queda en `reglas_omitidas` por el manejo
   de `TypeError` en `_evaluar_regla_en_perfil`), no rompe la respuesta.
7. **Redundancia deliberada en `seguros.db`:** la tabla `recomendaciones` guarda `perfil_entrada`
   completo además de tener `perfil_id` como llave foránea a la tabla `perfiles`. El prompt lo
   pidió en dos secciones distintas con dos niveles de detalle; se implementaron ambas literalmente
   en vez de elegir una — permite auditar "por qué se recomendó X" sin necesitar un JOIN.
8. **Se limpiaron menciones de "Colsubsidio" de los comentarios de `motor.py`/`app.py`** (quedaban
   solo en docstrings explicando el porqué del refactor, no en lógica ejecutable), para que el
   grep de verificación de agnosticismo diera 100% limpio sin zonas grises.

## 4. Pruebas — cuáles pasaron y cuáles no

**Las 3 pasaron.** Ejecutadas de nuevo después del cleanup final, mismos resultados.

### Prueba A — dataset socioeconómico + `hipotesis_socioeconomico.json`
Perfil: `{edad: 35, estado_civil: Casado, numero_hijos: 2, ..., rango_ingresos: Nivel 2}`
**Resultado: `categoria_top = "Vida y Familia"`** — coincide exactamente con lo esperado.
`score_propension = 0.822`, `confianza = alta`.

### Prueba B — dataset Colsubsidio + `hipotesis_colsubsidio_ejemplo.json`
Perfil equivalente al "Caso 1" del motor viejo (salario 1-1.5 SMLV, sin más datos).

**`categoria_top` coincide: `"Crédito"`.** Pero hay divergencias reales, reportadas sin ocultar:

| | Motor viejo (específico) | Motor genérico |
|---|---|---|
| `score_propension` | 1.00 | **0.7566** |
| Cómo se calculó el peso | Tabla de negocio ajustada a mano (12 valores por bucket salarial) | Frecuencia real del bucket salarial en las 500.000 filas |
| `categoria_secundaria` | Mascotas | Mascotas (**empate exacto** con Crédito: 0.7566 = 0.7566, ambas usan la misma condición atómica en el archivo de ejemplo; el desempate por orden de aparición en el archivo favorece a Crédito por casualidad de cómo se escribió el JSON, no por diseño) |

**Por qué diverge, con causa raíz:** el motor viejo tenía una escala graduada de 12 pesos
distintos por bucket salarial (0.02 a 1.00, ajustados a mano), reglas compuestas con Y/O, una
regla de "presencia de ciudad" sin condición de valor, una base fija para Mascotas, y una
penalización negativa por ciudad. **El esquema genérico pedido (columna/operador/valor →
categoría) no puede expresar ninguna de esas cinco cosas**: no hay pesos por valor específico
(solo pertenencia sí/no), no hay operador de "no nulo", no hay "siempre verdadero", y no hay
pesos negativos. El archivo `hipotesis_colsubsidio_ejemplo.json` usa el subconjunto atómico más
parecido al original (documentado con el detalle completo de cada pérdida dentro del propio
archivo JSON, campo `_README_LIMITACIONES`), pero no es una traducción sin pérdida — no podía serlo
con este esquema de reglas.

### Prueba C — dataset socioeconómico + `hipotesis_prueba_c.json` (inventada al momento)
5 reglas nuevas, incluida una compuesta, sobre las mismas columnas del dataset sintético, **sin
tocar `motor.py`**. Perfil: joven freelancer soltero sin hijos.
**Resultado: `categoria_top = "Riesgo Joven Independiente"`** — la regla compuesta
`edad < 30 Y estabilidad_laboral == 'Freelance'` se activó correctamente. `requiere_escalamiento
= true` porque el peso (0.01, forzado por ser <5% del dataset) da un score bajo. Demuestra
agnosticismo real: el motor nunca vio estas categorías ni estas columnas antes de esta ejecución.

## 5. Verificación final

| Chequeo | Resultado |
|---|---|
| Las 3 pruebas pasan sin tocar `motor.py` entre ellas | ✅ |
| `streamlit run app.py` levanta sin error | ✅ HTTP 200, log sin errores (verificado 2 veces, antes y después del cleanup de comentarios) |
| `seguros.db` existe con las 3 tablas y registros de las pruebas | ✅ 3 filas en `perfiles`, 3 en `recomendaciones`, 3 en `hipotesis_log` |
| Ningún `.py` tiene hardcodeada una columna o categoría de dominio | ✅ `grep -niE` por `RANGO_SALARIAL\|DROGUERIA\|Colsubsidio\|SEGMENTO_GRUPO_FAMILIAR\|CIUDAD_AFILIADO\|VIVIENDA\|Credito\|CHUBB` en `motor.py` y `app.py` da 0 resultados |

## 6. Qué quedó pendiente / no se pudo hacer

- **La traducción de las hipótesis de Colsubsidio al esquema genérico pierde fidelidad real**
  (ver Prueba B). Si se necesita reproducir el motor viejo con exactitud, el esquema de reglas
  tendría que crecer (pesos explícitos por valor, operador de nulidad, penalizaciones negativas,
  una "base universal") — eso ya no sería el formato simple pedido en este prompt.
- **`README.md` no se actualizó** para reflejar el nuevo `app.py` (selectores de dataset/hipótesis
  en vez de los 5 botones de casos de prueba de antes). No estaba en el alcance pedido
  explícitamente ("Sin documento de decisiones extenso"), pero el README describe una interfaz
  que ya no es exacta.
- **No se migró `iniciar.sh`** — sigue apuntando a `streamlit run app.py`, que sigue siendo
  correcto, así que no hacía falta tocarlo.
- **No se revisó si `seguros.db` necesita `.gitignore`** — al ser una base de datos que crece con
  cada uso (incluida cada corrida de demo del jurado), probablemente no debería versionarse tal
  cual; no se tomó esa decisión porque no fue pedida.
