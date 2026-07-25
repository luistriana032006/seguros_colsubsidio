# Decisiones de etiquetado — score de propensión por categoría

> **Bloque de trabajo:** etiquetar las 500.000 filas con un score de propensión por cada una de las 5 categorías oficiales de seguro.
> **Estado:** ✅ cerrado, verificado, reproducible.
> Documento redactado bajo el marco de [`reglas_documentacion_agent.md`](../reglas_documentacion_agent.md) (Método AR).

> ⚠️ **Este documento cubre TRES corridas.** Las secciones 1-11 son la **primera corrida (v1)** y se conservan sin modificar como diagnóstico del antes. La **§ 12 es la v2**, que corrige H1, H2 y H3. La **§ 13** cierra H8 como decisión de negocio. La **§ 14 es la v3**, que corrige H9.
> **El archivo vigente para el motor es `Usos_Productos_Afiliados_ETIQUETADO_V3.csv`.**

| | v1 | v2 | v3 (vigente) |
|---|---|---|---|
| Sección | § 1-11 | § 12 | § 14 |
| Entrada | `..._RANGO_SALARIAL_LIMPIO.csv` | `..._ETIQUETADO.csv` | `..._ETIQUETADO_V2.csv` |
| Salida | `..._ETIQUETADO.csv` (97,7 MB) | `..._ETIQUETADO_V2.csv` (100,7 MB) | **`..._ETIQUETADO_V3.csv`** (103,7 MB) |
| Filas × columnas | 500.000 × 24 | 500.000 × 24 | 500.000 × **25** |
| Estado | 📦 evidencia del antes | 📦 evidencia del antes | ✅ **vigente** |

Script único para las tres: [`../etiquetado_hipotesis.py`](../etiquetado_hipotesis.py) — iterado en el sitio, hoy produce la v3.

Bloque anterior: [`decisiones_limpieza_rango_salarial.md`](./decisiones_limpieza_rango_salarial.md) · Reproducir: `python3 etiquetado_hipotesis.py` (~40 s)

> Nota de reproducibilidad: `etiquetado_hipotesis.py` **fue iterado en el sitio**, así que hoy produce la v3. Las versiones anteriores no son re-ejecutables desde el script actual — se conservan sus salidas (`ETIQUETADO.csv`, `ETIQUETADO_V2.csv`) y sus números completos en este documento.

---

## 0. Alcance — qué entró y qué NO entró en este bloque

**Sí entró:** aplicar los pesos ya decididos por negocio sobre las 500.000 filas y producir los scores, la categoría top, la secundaria y las reglas legibles.

**Los pesos son una decisión cerrada, no una sugerencia.** Se ejecutaron exactamente como fueron especificados. Todo lo que detecté como mejorable durante la implementación está en **§ 7 Sugerencias**, sin aplicar.

**Explícitamente NO entró:**

| Fuera de alcance | Por qué |
|---|---|
| Cambiar cualquier peso | Decisión de negocio ya tomada. Las observaciones van como sugerencia, no como cambio. |
| `NearestNeighbors` / búsqueda de vecinos | Es el paso siguiente. Este bloque produce el insumo, no el motor de similitud. |
| Fuente 3 (contexto nacional) y la fórmula de combinación | `score_final = score_reglas_internas + ajustes_fuente_3` es un bloque aparte. Acá solo se produce la parte interna. |
| Reglas de elegibilidad dura (edad de los productos CHUBB) | Van **antes** de la propensión, en otra capa. No se mezclan con el score. |
| Tocar el archivo de entrada | Se leyó, nunca se escribió. |

---

## 1. Diagnóstico previo (insumos calculados, no asumidos)

**`SEGMENTO_GRUPO_FAMILIAR` — los 2 valores más frecuentes se calcularon con `value_counts`**, como pedía la especificación:

| Valor | Filas | ¿Top 2? |
|---|---:|---|
| **LAMBDA** | 286.457 | ✅ |
| **RHO** | 121.478 | ✅ |
| EPSILON | 46.999 | — |
| IOTA | 25.263 | — |
| CHI | 11.843 | — |
| THETA | 7.933 | — |
| PI | 27 | — |

**Disponibilidad de datos que afecta la regla de omisión:**

| Columna | Sin dato | % |
|---|---:|---:|
| `RANGO_SALARIAL_LIMPIO` = `"Desconocido"` | 4.988 | 0,998 % |
| `CIUDAD_AFILIADO` nula | 288.392 | 57,678 % |
| `DROGUERIA`, `RANGO_EDAD`, `SEGMENTO_GRUPO_FAMILIAR`, `VIVIENDA` | 0 | 0 % |

**Consecuencia:** las reglas de Personal y Familiar nunca se omiten (sus 3 columnas están completas). Las omisiones solo ocurren en Crédito, Hogar, Movilidad y Mascotas.

---

## 2. 🔴 Ambigüedad detectada y resuelta: reglas de PRESENCIA vs. reglas de VALOR

*(Esta es la decisión más importante del bloque. Cambia el resultado de 288.392 filas — el 57,68 % de la base.)*

**El conflicto.** La regla general de nulos dice:

> *"si el valor de una columna es 'Desconocido' o nulo, esa regla específica se omite del cálculo para esa fila"*

Pero dos reglas de la especificación **usan la ausencia de dato como la señal misma**:

- Movilidad: `CIUDAD_AFILIADO no nula → +0.5`
- Hogar: `CIUDAD_AFILIADO no nula → +0.3`

Aplicar la omisión literalmente a esas reglas es circular: si la ciudad es nula, la regla *"ciudad no nula"* se omitiría por falta del dato que precisamente está evaluando.

**Por qué la lectura literal es inviable.** Las **dos** reglas de Movilidad dependen de `CIUDAD_AFILIADO`. Si ambas se omiten cuando la ciudad es nula, Movilidad se queda **sin ninguna regla evaluable** en 288.392 filas → el score no sería calculable para el 57,68 % de la base. Eso no puede ser lo buscado.

**Criterio aplicado:**

| Tipo de regla | Qué evalúa | Ante dato faltante |
|---|---|---|
| **PRESENCIA** (`CIUDAD_AFILIADO no nula`) | si el dato existe | **Se evalúa siempre.** El nulo ES el dato; la regla da `false` y no suma. |
| **VALOR** (`== "SI"`, `in {…}`) | el contenido del dato | **Se omite.** No suma, no resta. |

Con este criterio: ciudad nula → Movilidad = 0.00 (evaluado, sin señal), no "incalculable".

**Esto es una interpretación, no un cambio de pesos.** Ningún peso fue modificado. Si la intención era otra, el cambio es de una línea (`m_ciudad_mov = ciudad_conocida`) y hay que definir qué hacer con las 288.392 filas que quedarían sin score de Movilidad.

---

## 3. Reglas aplicadas, tal cual fueron especificadas

**Crédito** — máximo 1.0

| Regla | Peso | Tipo |
|---|---:|---|
| `RANGO_SALARIAL_LIMPIO` ∈ {Menor al SMLV, Entre 1 y 1.5, Entre 1.5 y 2} | +1.0 | VALOR |

**Personal y Familiar** — máximo 1.0

| Regla | Peso | Tipo |
|---|---:|---|
| `DROGUERIA == "SI"` | +0.4 | VALOR |
| `SEGMENTO_GRUPO_FAMILIAR` ∈ {LAMBDA, RHO} *(calculado)* | +0.3 | VALOR |
| `RANGO_EDAD` ∈ {36 a 45, 46 a 55, Mayor de 55} | +0.3 | VALOR |

**Hogar** — máximo teórico 1.0

| Regla | Peso | Tipo |
|---|---:|---|
| `RANGO_SALARIAL_LIMPIO` ∈ {3 y 4, 4 y 6, 6 y 8, 8 y 10, 10 y 20, 20 y 30, Mayor a 30} | +0.4 | VALOR |
| `CIUDAD_AFILIADO` no nula | +0.3 | PRESENCIA |
| `VIVIENDA == "SI"` | +0.3 | VALOR |

**Movilidad** — máximo 1.0

| Regla | Peso | Tipo |
|---|---:|---|
| `CIUDAD_AFILIADO` no nula | +0.5 | PRESENCIA |
| `CIUDAD_AFILIADO` ∈ {SOACHA, MOSQUERA, ZIPAQUIRA, FUNZA} | +0.5 | VALOR |

Las dos suman **1.0 como máximo, nunca 1.5**: la periférica se apoya sobre la de presencia y ahí topa. Resultado: periférica = 1.0, ciudad conocida no periférica = 0.5, ciudad nula = 0.0.

**Mascotas** — rango real 0.35 a 0.65

| Regla | Peso | Tipo |
|---|---:|---|
| Base fija, todas las filas | = 0.5 | — |
| `RANGO_SALARIAL_LIMPIO` ∈ {Menor al SMLV, Entre 1 y 1.5, Entre 1.5 y 2} | +0.15 | VALOR |
| `CIUDAD_AFILIADO == "BUCARAMANGA"` | −0.15 | VALOR |

---

## 4. Por qué NO se renormalizó el score sobre los pesos disponibles

La regla de nulos dice que una regla omitida *"no cuenta como cero"*. La lectura estricta de eso sería **renormalizar**: `score = puntos obtenidos ÷ peso total de las reglas que sí tenían dato`. **No se hizo**, por dos razones verificables:

1. **Rompe Mascotas.** Con base 0.5 + 0.15 por salario bajo, renormalizar daría `0.65 ÷ 0.65 = 1.00`. **Las 378.256 filas de salario bajo tendrían Mascotas = 1.00**, la categoría de confianza más baja del proyecto empatando en el máximo. Contradice directamente el "base fija = 0.5 para todas las filas" de la especificación.
2. **Deja Crédito sin definir.** Crédito tiene una sola regla. Si el salario es `"Desconocido"`, el denominador es 0 → división indefinida en 4.988 filas.

Además, **los pesos ya fueron diseñados para sumar exactamente 1.0 por categoría** (Crédito 1.0; PyF 0.4+0.3+0.3; Hogar 0.4+0.3+0.3; Movilidad 0.5+0.5). No hace falta normalizar para que los scores queden en [0, 1] — se cumple solo.

**Consecuencia honesta de esta decisión, que hay que conocer:** un score de 0.00 por regla omitida es indistinguible, mirando solo el número, de un 0.00 por regla evaluada que no aplicó. En Crédito: 121.714 filas con score 0.00, de las cuales **4.988 son omisión** (salario Desconocido) y **116.726 son evaluación real** (salario alto).

**Mitigación:** la distinción es 100 % recuperable desde las columnas que ya están en el archivo — `RANGO_SALARIAL_LIMPIO == "Desconocido"` y `CIUDAD_AFILIADO.isna()`. No hizo falta agregar columnas nuevas. Ver sugerencia **S4** si se quiere explícita.

---

## 5. Verificación

| Chequeo | Resultado |
|---|---|
| Filas de entrada = filas de salida | **500.000 = 500.000** ✅ |
| Todos los scores dentro de [0, 1] | ✅ |
| Sin nulos en ninguna columna de score | ✅ |
| Las 5 categorías aparecen como top | ✅ ninguna quedó vacía |

**Rango real de cada score:**

| Score | Mín | Máx | Observación |
|---|---:|---:|---|
| `score_credito` | 0.00 | 1.00 | binario: solo 0.00 o 1.00 |
| `score_personal_familiar` | 0.00 | 1.00 | 6 valores distintos, el mejor distribuido |
| `score_hogar` | 0.00 | **0.70** | **nunca alcanza 1.00** → ver hallazgo H2 |
| `score_movilidad` | 0.00 | 1.00 | 3 valores: 0.00 / 0.50 / 1.00 |
| `score_mascotas` | **0.35** | **0.65** | nunca 0 ni 1, por el piso fijo |

**Distribución de `categoria_top`:**

| Categoría | Filas | % |
|---|---:|---:|
| Crédito | 378.286 | 75,657 % |
| Personal y Familiar | 55.832 | 11,166 % |
| Mascotas | 27.367 | 5,473 % |
| Hogar | 26.928 | 5,386 % |
| Movilidad | 11.587 | 2,317 % |

**Distribución de `categoria_secundaria`:**

| Categoría | Filas | % |
|---|---:|---:|
| Mascotas | 361.543 | 72,309 % |
| Personal y Familiar | 72.136 | 14,427 % |
| Movilidad | 39.793 | 7,959 % |
| Hogar | 22.378 | 4,476 % |
| Crédito | 4.150 | 0,830 % |

**Distribución completa de valores por score:**

| Score | Valores observados |
|---|---|
| `credito` | 0.0 = 121.714 · 1.0 = 378.286 |
| `personal_familiar` | 0.0 = 17.221 · 0.3 = 238.740 · 0.4 = 7.179 · 0.6 = 155.808 · 0.7 = 59.520 · 1.0 = 21.532 |
| `hogar` | 0.0 = 256.926 · 0.3 = 172.987 · 0.4 = 31.446 · 0.6 = 16 · 0.7 = 38.625 |
| `movilidad` | 0.0 = 288.392 · 0.5 = 195.085 · 1.0 = 16.523 |
| `mascotas` | 0.35 = 22 · 0.5 = 121.722 · 0.65 = 378.256 |

---

## 6. Hallazgos (se reportan, no se ocultan)

> **Estado tras la v2 (§ 12):** **H1 ✅ resuelto · H2 ✅ resuelto · H3 ✅ resuelto** (con un efecto colateral nuevo, H8). **H4, H5 y H6 siguen abiertos.** El texto de abajo es el diagnóstico original de la v1 y se conserva tal cual.

### H1 — Crédito se lleva 3 de cada 4 filas, y siempre con el mismo score
> ✅ **RESUELTO en v2** — escala graduada de 12 buckets. `score_credito` pasó de 2 valores distintos a 13. Ver § 12.2.

378.286 filas (75,66 %) tienen `categoria_top = Crédito`, **todas con score exactamente 1.00**. No es un error: es consecuencia aritmética directa de que el 75,66 % de la base gana menos de 2 SMLV y de que la regla de Crédito es binaria y vale el máximo posible. Cualquier fila que la cumpla llega al techo y gana el ranking casi siempre.

**Lo que implica:** dentro de ese 75,66 % el score **no discrimina** — 378.286 personas reciben la misma recomendación con idéntica confianza. La diferenciación tendrá que venir del motor de similitud, no del score. Ver sugerencia **S1**.

### H2 — Hogar nunca puede llegar a 1.00
> ✅ **RESUELTO en v2** — rebalanceo 0.6 + 0.4 con `VIVIENDA` como bonus. `score_hogar == 1.00` pasó de **0 filas a 38.624**. Ver § 12.2.

Su techo real es **0.70**. La tercera regla (`VIVIENDA == "SI"`, +0.3) solo puede activarse en **36 filas de 500.000** (0,007 %), y ninguna de esas 36 tiene simultáneamente salario alto y ciudad conocida: **`score_hogar == 1.00` ocurre en 0 filas**.

**Lo que implica:** los scores no son comparables en la misma escala entre categorías. Hogar compite con un techo de 0.70 contra categorías que llegan a 1.00, así que pierde desempates que "debería" ganar. Ver sugerencia **S2**.

### H3 — Mascotas es la segunda opción del 72 % de la base, sin ninguna evidencia individual
> ✅ **RESUELTO en v2** — Mascotas con score 0.50 exacto ya no puede ganar el primer lugar: las 27.367 filas que ganaba por descarte se redistribuyeron. **Efecto colateral: ahora Mascotas nunca es top (0 filas).** Ver § 12.4 (hallazgo H8).

El piso fijo de 0.5 la vuelve omnipresente: es `categoria_secundaria` en **361.543 filas (72,31 %)**. Cuando es top (27.367 filas), **siempre lo es con score 0.50** — nunca con 0.65 — es decir, **gana por descarte**, no por señal propia. De esas, **4.150 filas tienen las otras 4 categorías en 0.00**: la recomendación es Mascotas solo porque nada más puntuó.

Es coherente con el diseño (Mascotas no tiene columna propia y se apoya en la Fuente 3), pero hay que saberlo antes de mostrarlo al jurado: *"le recomendamos Mascotas"* en esas filas significa *"no tenemos señal de nada más"*. Ver sugerencia **S3**.

### H4 — La penalización de Bucaramanga es casi inerte

Solo **52 filas** tienen `CIUDAD_AFILIADO == "BUCARAMANGA"`, y de esas solo **22** terminan con score 0.35 (las otras 30 tienen salario bajo, y el +0.15 cancela el −0.15). La regla afecta al 0,004 % de la base. No está mal — simplemente no mueve la aguja.

### H5 — 7,80 % de las filas se decide por desempate

**39.023 filas** tienen empate en el score máximo entre dos o más categorías. En esos casos la categoría top la elige el criterio de desempate (decisión propia **D2**), no los datos: Crédito gana 23.763, Movilidad 9.006, Personal y Familiar 6.254.

### H6 — 7,27 % de la base no tiene ninguna señal fuerte

36.375 filas tienen todos sus scores en ≤ 0.50. Ninguna fila quedó con las 5 categorías en 0.00 (el piso de Mascotas lo impide), pero en estas la recomendación es débil por definición. Son candidatas naturales a `requiere_escalamiento = true` en el objeto de salida del motor.

---

## 7. Decisiones propias del agente

*(Método AR: marcadas aparte, no mezcladas con el pedido original.)*

### Aplicadas — fueron necesarias para poder ejecutar

| # | Decisión | Por qué | Impacto | Reversible |
|---|---|---|---|---|
| **D1** | **Reglas de PRESENCIA se evalúan siempre; las de VALOR se omiten** (§ 2) | Sin esto Movilidad no es calculable en el 57,68 % de la base | 288.392 filas | Sí, 1 línea |
| **D2** | **Desempate por orden de confianza de las hipótesis** (Crédito → Personal y Familiar → Hogar → Movilidad → Mascotas, el orden declarado en `CLAUDE.md`) | La especificación no define qué hacer ante empate, y ocurre en 39.023 filas. Se eligió un criterio explicable en una frase, no arbitrario ni alfabético | 39.023 filas (7,80 %) | Sí, reordenando `CATEGORIAS` |
| **D3** | **No renormalizar sobre pesos disponibles** (§ 4) | La renormalización rompe Mascotas y deja Crédito indefinido | Todas | Sí, documentado |

### Sugerencias — detectadas pero **NO aplicadas** *(estado actualizado tras la v2)*

| # | Sugerencia | Por qué | Estado |
|---|---|---|---|
| **S1** | **Graduar Crédito por bucket** en vez de binario 1.0 (ej. `Menor al SMLV` = 1.0, `1 a 1.5` = 0.85, `1.5 a 2` = 0.7) | Hoy 378.286 personas reciben score idéntico y el ranking no las distingue (H1) | ✅ **APLICADA en v2** con números de negocio, distintos a los propuestos — ver § 12.3 |
| **S2** | **Redistribuir el 0.3 de `VIVIENDA`** entre las otras dos reglas de Hogar, o normalizar cada score por su techo real | Hogar compite con techo 0.70 contra categorías de techo 1.00 y pierde desempates por construcción (H2) | ✅ **APLICADA en v2** con un criterio distinto (bonus, no redistribución) — ver § 12.3 |
| **S3** | **Excluir el piso fijo de Mascotas del ranking** (usarlo como score absoluto, pero no para elegir top/secundaria) | Mascotas es secundaria del 72 % de la base sin evidencia individual; ensucia la segunda recomendación (H3) | ✅ **APLICADA en v2** de forma más quirúrgica que la propuesta — ver § 12.3 |
| **S4** | **Columna `reglas_omitidas_por_falta_de_dato`** | Haría explícito el "0.00 por omisión" vs "0.00 evaluado". Hoy es recuperable pero implícito (§ 4) | ⏸️ **PENDIENTE por decisión de negocio** — se difiere hasta que haga falta depurar algo |

*(En la v1 ninguna se aplicó: los pesos eran decisión de negocio cerrada y S1/S2/S3 los modificaban. Negocio los reabrió y fijó los números en la v2.)*

---

## 8. Ejemplos reales — una fila por categoría

**Crédito** — `SERIE=2` · F · 20 a 35 años · Menor al SMLV · CHI · ciudad nula · DROGUERIA=SI
`Crédito 1.00` · PyF 0.40 · Hogar 0.00 · Movilidad 0.00 · **Mascotas 0.65** (secundaria)
→ *Por qué:* `RANGO_SALARIAL_LIMPIO=Menor al SMLV`. Sin ciudad, Hogar y Movilidad quedan en 0.

**Personal y Familiar** — `SERIE=1` · F · 36 a 45 años · Entre 8 y 10 SMLV · LAMBDA · BOGOTA D.C. · DROGUERIA=SI
`PyF 1.00` · Crédito 0.00 · **Hogar 0.70** (secundaria) · Movilidad 0.50 · Mascotas 0.50
→ *Por qué:* `DROGUERIA=SI, SEGMENTO_GRUPO_FAMILIAR=LAMBDA, RANGO_EDAD=36 a 45 años` — las 3 reglas activas, el único caso que llega a 1.00.

**Hogar** — `SERIE=36` · M · 20 a 35 años · Entre 3 y 4 SMLV · CHI · LA CALERA · DROGUERIA=SI
`Hogar 0.70` · Crédito 0.00 · PyF 0.40 · **Movilidad 0.50** (secundaria) · Mascotas 0.50
→ *Por qué:* `RANGO_SALARIAL_LIMPIO=Entre 3 y 4 SMLV, CIUDAD_AFILIADO=LA CALERA`. Es el techo real de Hogar (H2).

**Movilidad** — `SERIE=276` · F · 20 a 35 años · Entre 2 y 2.5 SMLV · LAMBDA · SOACHA · DROGUERIA=SI
`Movilidad 1.00` · Crédito 0.00 · **PyF 0.70** (secundaria) · Hogar 0.30 · Mascotas 0.50
→ *Por qué:* `CIUDAD_AFILIADO=SOACHA (periférica)` — presencia 0.5 + periférica 0.5.

**Mascotas** — `SERIE=16` · F · 20 a 35 años · **Desconocido** · THETA · ciudad nula · DROGUERIA=SI
`Mascotas 0.50` · Crédito 0.00 · **PyF 0.40** (secundaria) · Hogar 0.00 · Movilidad 0.00
→ *Por qué:* `base nacional Mascotas (0.5)`. Caso de libro de H3: **gana por descarte**. Su Crédito 0.00 es por **omisión** (salario Desconocido), no por evaluación (§ 4).

---

## 9. Columnas nuevas en el archivo de salida

Se agregaron 8 columnas al final. **Ninguna columna existente fue modificada** (24 columnas = 16 originales + 8 nuevas).

| Columna | Tipo | Contenido |
|---|---|---|
| `score_credito` | float [0-1] | 2 decimales |
| `score_personal_familiar` | float [0-1] | 2 decimales |
| `score_hogar` | float [0-1] | 2 decimales |
| `score_movilidad` | float [0-1] | 2 decimales |
| `score_mascotas` | float [0-1] | 2 decimales |
| `categoria_top` | texto | La de mayor score (desempate D2) |
| `categoria_secundaria` | texto | La segunda de mayor score |
| `reglas_activadas_top` | texto | Reglas que dispararon el score de la top, legible por un humano |

`reglas_activadas_top` está pensado para alimentar la explicación al usuario final: incluye el **valor real** de la fila, no el nombre de la regla. Ej. `DROGUERIA=SI, SEGMENTO_GRUPO_FAMILIAR=LAMBDA, RANGO_EDAD=36 a 45 años`.

⚠️ **Recordatorio de `CLAUDE.md`:** `SEGMENTO_GRUPO_FAMILIAR=LAMBDA` sirve para el motor, pero **nunca debe mostrarse al usuario final** — los códigos griegos no significan nada legible fuera de Colsubsidio. El bot de Nicolás debe filtrar esas reglas al redactar, o traducirlas a lenguaje de negocio.

---

## 10. Qué falta / qué verificar en la próxima sesión

**Qué se hizo:** 500.000 filas etiquetadas con 5 scores + top + secundaria + reglas legibles. Verificado, sin filas perdidas, sin scores fuera de rango, las 5 categorías representadas.

**Qué falta:**

1. **`NearestNeighbors` sobre este archivo** — pendiente #2 de `CLAUDE.md`, ahora reducido: los pesos de las reglas quedan cerrados en este bloque; lo único abierto es **cómo el motor usa estos scores para encontrar vecinos** (¿los scores entran como features de la distancia, o solo las columnas de perfil y los scores se usan para rankear al final?). Es una decisión de diseño aparte, no se resolvió acá.
2. **Fórmula de combinación con Fuente 3** — especialmente para Mascotas, que hoy vive de un piso fijo (H3).
3. **Decidir el destino de las sugerencias S1-S4** (§ 7). S1 y S2 son las que más cambiarían el ranking.
4. **Reglas de elegibilidad dura por edad** — van antes de la propensión, no se tocaron.

**Qué verificar antes de seguir:**

- Que el motor lea **`Usos_Productos_Afiliados_ETIQUETADO.csv`**, no el CSV limpio ni el Excel original.
- Que `reglas_activadas_top` se filtre antes de llegar al usuario final (códigos griegos, § 9).
- Que las 36.375 filas sin señal fuerte (H6) se mapeen a `requiere_escalamiento = true`.

---

## 11. Desviación respecto al plan original

**Desviación de ejecución: ninguna.** Los pesos se aplicaron exactamente como fueron especificados; ninguno fue modificado. Las columnas de salida son las pedidas, con los nombres pedidos. El archivo de entrada no se tocó.

**Una decisión que hubo que tomar para poder ejecutar:** la ambigüedad entre la regla general de nulos y las reglas de presencia sobre `CIUDAD_AFILIADO` (§ 2, decisión **D1**). No era resoluble "ejecutando lo especificado", porque la lectura literal deja Movilidad sin calcular en el 57,68 % de la base. Se eligió la única lectura viable y quedó documentada con su alternativa y su costo.

**Dos decisiones menores forzadas por vacíos de la especificación:** el criterio de desempate (**D2**, no estaba definido y afecta 39.023 filas) y la no-renormalización (**D3**, § 4).

**Señal de alerta de dos fallos seguidos:** no se activó. El script corrió correcto en el primer intento y todas las verificaciones pasaron.

**Sobre los pesos:** cumplí la instrucción de no cambiarlos en silencio. Las 4 mejoras que detecté están en § 7 como sugerencias sin aplicar, cada una con el hallazgo que la motiva.

---

---
---

# 12. SEGUNDA CORRIDA (v2) — corrección de H1, H2 y H3

**2026-07-24** · Todo lo anterior (§ 1-11) es el diagnóstico de la v1 y **no fue modificado**.

## 12.1 Alcance de esta iteración

**Se corrigieron los 3 hallazgos** que reporté en la primera corrida, con **números fijados por negocio**, no con los que yo había propuesto.

**Se mantuvo exactamente igual, sin tocar:**

- La interpretación de reglas de **presencia vs. valor** para nulos (§ 2)
- La decisión de **no renormalizar** (§ 4)
- El **desempate por orden de confianza** de `CLAUDE.md` (D2)
- Los **pesos de Personal y Familiar y de Movilidad** — no había hallazgo ahí

**No se aplicó S4** (columna de reglas omitidas): queda pendiente por decisión de negocio.

**No se re-ejecutó desde cero:** la v2 parte de `Usos_Productos_Afiliados_ETIQUETADO.csv` (la salida de la v1) y recalcula sobre él las 8 columnas de score. No se volvió al Excel ni se repitió la limpieza. La v1 se conserva íntegra como evidencia del antes.

## 12.2 Los tres cambios aplicados

**CAMBIO 1 — Crédito: de binario a escala graduada por bucket.** Reemplaza la regla única `∈ {3 buckets bajos} → 1.0`:

| Bucket | Peso | | Bucket | Peso |
|---|---:|---|---|---:|
| Menor al SMLV | 0.85 | | Entre 4 y 6 SMLV | 0.25 |
| **Entre 1 y 1.5 SMLV** | **1.00** | | Entre 6 y 8 SMLV | 0.15 |
| Entre 1.5 y 2 SMLV | 0.90 | | Entre 8 y 10 SMLV | 0.10 |
| Entre 2 y 2.5 SMLV | 0.70 | | Entre 10 y 20 SMLV | 0.05 |
| Entre 2.5 y 3 SMLV | 0.55 | | Entre 20 y 30 SMLV | 0.03 |
| Entre 3 y 4 SMLV | 0.40 | | Mayor a 30 SMLV | 0.02 |

`"Desconocido"` no está en la tabla: la regla se omite, como ya se hacía.

**CAMBIO 2 — Hogar: rebalanceado para que el techo llegue a 1.0.**

| Regla | v1 | v2 |
|---|---:|---:|
| `RANGO_SALARIAL_LIMPIO` ∈ {3 y 4 SMLV o superior} | 0.4 | **0.6** |
| `CIUDAD_AFILIADO` conocida *(presencia)* | 0.3 | **0.4** |
| `VIVIENDA == "SI"` | 0.3 | **+0.15 como BONUS** |

Las dos primeras suman 1.0 por sí solas; `VIVIENDA` es un bonus **por encima** de ese presupuesto, con `score_hogar = min(1.0, suma)`.

**CAMBIO 3 — Mascotas: regla de elegibilidad para `categoria_top`.** Los pesos **no cambian** (base 0.5, +0.15 salario bajo, −0.15 Bucaramanga). Cambia el ranking: si `score_mascotas == 0.5` exacto (ningún correlato de Fuente 3 se activó), Mascotas queda **excluida del cálculo de `categoria_top`** y este se recalcula entre las otras 4. Sigue elegible como `categoria_secundaria`.

## 12.3 Delta entre lo que yo había propuesto y lo que fijó negocio

*(Pedido explícito: documentar la diferencia.)*

| | Mi propuesta (S1-S3) | Lo aplicado (negocio) | Por qué la de negocio es mejor |
|---|---|---|---|
| **S1** | Escala **monótona decreciente**: `Menor al SMLV` = 1.0 → `1 a 1.5` = 0.85 → `1.5 a 2` = 0.7. Solo 3 buckets. | **Pico en `Entre 1 y 1.5 SMLV` = 1.00**, con `Menor al SMLV` **por debajo** (0.85). Los 12 buckets. | Yo asumí "a menor ingreso, mayor propensión a crédito". Negocio corrigió: quien gana **menos de un SMLV** probablemente **no califica** para crédito formal (capacidad de pago, informalidad), mientras que 1–1.5 SMLV es el perfil típico de libranza. Mi curva habría premiado justo al segmento menos bancarizable. |
| **S2** | **Redistribuir** el 0.3 de `VIVIENDA` entre las otras dos reglas, o normalizar por techo real. | Conservar `VIVIENDA` como **bonus de 0.15 fuera del presupuesto**, con tope en 1.0. | Mi versión **eliminaba** la señal de `VIVIENDA`. La de negocio la preserva —sigue sumando cuando aparece— sin que su ausencia impida llegar a 1.0. Mejor: no se pierde información real por ser rara. |
| **S3** | Sacar el piso de Mascotas del ranking **siempre**, tanto de top como de secundaria. | Excluirla **solo cuando el score es 0.50 exacto** y **solo de top**; sigue compitiendo por secundaria. | Más quirúrgica. La mía habría anulado también los casos con correlato real (0.65 y 0.35), que sí son evidencia. Aunque en la práctica el resultado sobre `categoria_top` terminó siendo el mismo — ver H8. |

## 12.4 Verificación de la v2

| Chequeo | Resultado |
|---|---|
| Filas de entrada = filas de salida | **500.000 = 500.000** ✅ |
| Todos los scores dentro de [0, 1] | ✅ |
| Sin nulos en los scores | ✅ |
| Las 5 categorías aparecen como top | ❌ **Mascotas quedó en 0 filas** → hallazgo H8 |

**Techos alcanzados — antes y después:**

| Score | Máx v1 | Máx v2 | Valores distintos v1 → v2 |
|---|---:|---:|---|
| `score_credito` | 1.00 | 1.00 | **2 → 13** ✅ H1 resuelto |
| `score_hogar` | **0.70** | **1.00** | 5 → 7 ✅ H2 resuelto |
| `score_personal_familiar` | 1.00 | 1.00 | 6 → 6 *(sin cambios, correcto)* |
| `score_movilidad` | 1.00 | 1.00 | 3 → 3 *(sin cambios, correcto)* |
| `score_mascotas` | 0.65 | 0.65 | 3 → 3 *(pesos sin cambios, correcto)* |

**`categoria_top` — antes y después:**

| Categoría | v1 | % v1 | v2 | % v2 | Δ |
|---|---:|---:|---:|---:|---:|
| Crédito | 378.286 | 75,657 % | **408.900** | **81,780 %** | +30.614 |
| Hogar | 26.928 | 5,386 % | **45.716** | **9,143 %** | +18.788 |
| Personal y Familiar | 55.832 | 11,166 % | **41.441** | **8,288 %** | −14.391 |
| Movilidad | 11.587 | 2,317 % | **3.943** | **0,789 %** | −7.644 |
| Mascotas | 27.367 | 5,473 % | **0** | **0,000 %** | −27.367 |

**61.146 filas (12,23 %) cambiaron de `categoria_top`.** Hacia dónde se fueron las que Mascotas ganaba por descarte: 14.331 → Crédito, 11.620 → Hogar, 1.416 → Personal y Familiar.

**`categoria_secundaria`:** Mascotas 347.505 (69,50 %) · Personal y Familiar 75.109 (15,02 %) · Movilidad 34.003 (6,80 %) · Hogar 24.357 (4,87 %) · Crédito 19.026 (3,81 %).

**Resolución de `categoria_top`:**

| Métrica | v1 | v2 |
|---|---:|---:|
| Filas resueltas por **desempate** | 39.023 (7,80 %) | **43.434 (8,69 %)** |
| Mascotas excluida del primer lugar | — | 121.722 (24,34 %) |
| Filas con `categoria_top` de score **0.00** | 4.150 *(eran Mascotas 0.5)* | **3.534 (0,71 %)** |

**Distribución completa de scores v2:**

| Score | Valores observados |
|---|---|
| `credito` | 0.0 = 4.988 · 0.02 = 431 · 0.03 = 1.238 · 0.05 = 9.779 · 0.10 = 3.098 · 0.15 = 8.721 · 0.25 = 23.024 · 0.40 = 23.780 · 0.55 = 19.347 · 0.70 = 27.308 · 0.85 = 33.868 · 0.90 = 41.805 · 1.00 = 302.613 |
| `hogar` | 0.0 = 256.926 · 0.15 = 19 · 0.40 = 172.968 · 0.55 = 16 · 0.60 = 31.446 · 0.75 = 1 · **1.00 = 38.624** |
| `personal_familiar` | sin cambios respecto a v1 |
| `movilidad` | sin cambios respecto a v1 |
| `mascotas` | sin cambios respecto a v1 |

## 12.5 Hallazgos nuevos de la v2

### 🔴 H8 — Mascotas ya nunca es la primera recomendación (0 filas de 500.000)

El CAMBIO 3 no solo evitó que Mascotas ganara por descarte: **la eliminó por completo del primer lugar**. No es un bug — es aritmética, y hay que entender por qué:

- Mascotas solo es **elegible** para top cuando su score ≠ 0.50, o sea con **0.65** (378.256 filas) o **0.35** (22 filas).
- El +0.15 que la lleva a 0.65 se activa con **el mismo predictor que Crédito**: salario bajo-medio.
- Verificado: de las 378.256 filas con Mascotas = 0.65, **las 378.256 tienen `score_credito` ≥ 0.85**. Ninguna excepción.
- Las 22 filas con Mascotas = 0.35 tienen alguna otra categoría en ≥ 0.55.

**Mascotas y Crédito están anticorrelacionadas por construcción:** Mascotas solo sube cuando Crédito ya está en su techo. Mientras compartan el mismo predictor, Mascotas no puede ganar nunca.

**Implicación de negocio:** una de las 5 categorías oficiales **jamás se ofrece como primera opción**. Sigue siendo secundaria en el 69,50 % de la base, así que no desaparece del sistema — pero si el bot solo muestra la top, Mascotas nunca se vende. **Esto necesita decisión de negocio**, no un ajuste técnico mío. Opciones, sin aplicar:

- Darle a Mascotas un predictor propio que no sea el salario (hoy no existe en el dataset — por eso depende de la Fuente 3).
- Que el bot ofrezca siempre top + secundaria, no solo la top.
- Reservarle un cupo a Mascotas cuando su score sea 0.65 y la diferencia con la top sea menor a cierto umbral.

### H9 — 3.534 filas reciben Crédito con score 0.00

Todas tienen `RANGO_SALARIAL_LIMPIO = "Desconocido"` **y** `CIUDAD_AFILIADO` nula **y** Personal y Familiar en 0. Sus 4 categorías elegibles quedan en 0.00, y el desempate por confianza les asigna **Crédito con score 0.00**: se recomienda un seguro de crédito a alguien de quien **no se conoce el salario**, sin ninguna evidencia a favor.

En la v1 estas filas caían en Mascotas 0.50 — que al menos era un piso declarado. **El cambio las dejó peor**: antes la recomendación era débil pero coherente; ahora es Crédito sin sustento, que es justo la categoría donde el dato faltante importa más. Su secundaria es Mascotas en las 3.534.

**Recomendación (no aplicada):** que estas filas se marquen `requiere_escalamiento = true` en el objeto de salida del motor, o que la regla sea "si el score de la top es 0.00, no hay recomendación". Es una decisión de negocio.

*(La cifra bajó de 4.150 a 3.534 porque la escala graduada de Crédito rescató 616 filas de salario alto que antes puntuaban 0.00 y ahora tienen entre 0.02 y 0.40.)*

### H4, H5, H6 — siguen abiertos

- **H4** (penalización Bucaramanga casi inerte, 52 filas): sin cambios, no se tocó.
- **H5** (filas decididas por desempate): **empeoró levemente**, de 7,80 % a **8,69 %**. La escala graduada de Crédito creó valores nuevos que empatan con Hogar y Movilidad (ej. 0.40, 0.70).
- **H6** (filas sin señal fuerte): sigue vigente, ahora con H9 como su caso extremo.

## 12.6 Decisiones propias del agente en la v2

**Aplicadas:** ninguna nueva. Los tres cambios venían con números fijados por negocio y se ejecutaron tal cual. D1, D2 y D3 de la v1 siguen vigentes sin modificación.

Dos detalles de implementación que decidí yo, ambos cosméticos y reversibles:

| # | Decisión | Por qué |
|---|---|---|
| **D4** | `reglas_activadas_top` de Crédito ahora muestra el peso del bucket, ej. `RANGO_SALARIAL_LIMPIO=Entre 2 y 2.5 SMLV (0.70)` | Con la escala graduada, saber *qué* bucket activó la regla ya no basta para explicar el score; hace falta *cuánto* aportó |
| **D5** | La salida va a un **archivo nuevo** (`_V2.csv`) en vez de sobrescribir `ETIQUETADO.csv` | Mantiene el antes/después comparable fila por fila, igual que se hizo con la limpieza. Costo: 98 MB extra en disco |

**Sugerencia nueva, no aplicada:** ver H8 — Mascotas necesita un predictor que no sea el salario, o una regla de exposición en el bot. No lo resolví porque es decisión de negocio, no técnica.

## 12.7 Desviación respecto al plan de la v2

**Desviación: ninguna.** Los tres cambios se aplicaron con los números exactos especificados. Lo que se pidió mantener sin tocar (presencia/valor, no renormalizar, desempate, pesos de PyF y Movilidad) quedó intacto — verificado en la tabla de § 12.4: `personal_familiar` y `movilidad` conservan exactamente la misma distribución que en v1. S4 no se aplicó, como se pidió.

**Señal de alerta de dos fallos seguidos:** no se activó. El script corrió correcto al primer intento.

**Lo que sí hago notar, porque no estaba previsto:** el CAMBIO 3 tuvo un efecto más fuerte que el buscado (H8: Mascotas pasó de 27.367 a **0** filas como top) y el CAMBIO 1 dejó 3.534 filas en una situación peor que antes (H9). Ninguno de los dos es un error de implementación —ambos son consecuencia aritmética de las reglas pedidas— pero los dos requieren una decisión de negocio antes de mostrar esto al jurado.

---
---

# 13. Que Mascotas nunca gane el top es una decisión de negocio, no un bug

**2026-07-24** · Cierra el hallazgo H8 de § 12.5.

En la v2 reporté que Mascotas quedó en **0 filas** como `categoria_top` y lo marqué como algo que requería decisión de negocio. **La decisión está tomada: se acepta el comportamiento tal cual, no se corrige.**

## 13.1 Por qué fue consciente

**Mascotas es, por diseño, la categoría con menos evidencia real del dataset.** No tiene ninguna columna propia — no hay un campo "tiene mascota", ni nada que lo aproxime. Su score se sostiene sobre un piso estadístico nacional (Fuente 3: DANE + estudio de mercado), no sobre un rasgo observado de la persona. Eso ya estaba declarado en `CLAUDE.md`: confianza **"Baja, no nula"**, la única de las 5 sin columna clave.

Que pierda sistemáticamente contra categorías que **sí** tienen evidencia individual (salario para Crédito, droguería y grupo familiar para Personal y Familiar, ciudad para Hogar y Movilidad) es el resultado correcto de un motor que ordena por propensión.

**Inflar Mascotas artificialmente para que gane sería falsear la propensión.** Subirle el piso, darle un peso extra o reservarle un cupo produciría recomendaciones que el motor no puede justificar con ninguna regla visible sobre esa persona — exactamente lo que prohíbe el requisito no negociable del reto: *"la lógica debe ser documentada y explicable, nada de caja negra"*. Una recomendación de Mascotas ganada por un peso inventado no se puede defender ante el jurado con datos de la persona; solo con "le subimos el número para que apareciera".

## 13.2 Qué significa esto en la práctica

Mascotas **no desaparece del sistema**: es `categoria_secundaria` en **343.971 filas (68,79 %)**. Sigue disponible como recomendación de segundo orden, que es exactamente el peso que le corresponde a una hipótesis sostenida por estadística nacional y no por el perfil del afiliado.

La exposición de Mascotas al usuario final es un asunto de **cómo el bot presenta los resultados** (top sola vs. top + secundaria), no del motor de propensión. Queda documentado fuera de este repo.

## 13.3 Qué NO se hizo

Las tres opciones que había propuesto en § 12.5 quedan **descartadas**, no pendientes:

| Opción propuesta | Estado |
|---|---|
| Darle a Mascotas un predictor propio | ❌ Descartada — no existe en el dataset; inventarlo es falsear |
| Reservarle un cupo cuando la diferencia con la top sea pequeña | ❌ Descartada — es inflar la propensión por otra vía |
| Que el bot ofrezca top + secundaria | ➡️ Fuera del alcance de este repo (decisión de presentación) |

---
---

# 14. TERCERA CORRIDA (v3) — filas sin ninguna señal

**2026-07-24** · Corrige el hallazgo H9 de § 12.5. **Ningún peso cambia respecto a la v2.**

| | v3 |
|---|---|
| Entrada | `../Usos_Productos_Afiliados_ETIQUETADO_V2.csv` — no se modificó |
| Salida | **`../Usos_Productos_Afiliados_ETIQUETADO_V3.csv`** — 500.000 × **25 columnas** (103,7 MB) |
| Estado | ✅ **vigente para el motor** |

## 14.1 Diagnóstico — qué estaba mal

En la v2, 3.534 filas recibían `categoria_top = Crédito` con `score_credito = 0.00`. Sus 4 categorías con reglas quedaban todas en cero, así que el ganador no salía de los datos de la persona: salía del **desempate por orden de confianza** (D2), que ante un empate de ceros elegía la primera de la lista.

El resultado era una recomendación de seguro de crédito para alguien de quien **no se conoce el ingreso** — justo la variable de la que depende esa categoría. Peor que no recomendar nada, porque tiene la misma forma que una recomendación fundamentada.

**Perfil de esas 3.534 filas — es un perfil concreto, no ruido disperso.** Las 3.534 comparten *exactamente* las mismas características:

| Columna | Valor | Cobertura |
|---|---|---|
| `RANGO_SALARIAL_LIMPIO` | `Desconocido` | 3.534 / 3.534 |
| `CIUDAD_AFILIADO` | nula | 3.534 / 3.534 |
| `DROGUERIA` | `NO` | 3.534 / 3.534 |
| `SEGMENTO_GRUPO_FAMILIAR` | `THETA` | 3.534 / 3.534 |
| `RANGO_EDAD` | `20 a 35 años` (2.853) · `Menor de 19 años` (681) | 3.534 / 3.534 |

Es el cruce exacto de todas las condiciones que apagan cada regla: sin salario (apaga Crédito y Hogar), sin ciudad (apaga Hogar y Movilidad), sin droguería + grupo familiar fuera del top-2 + edad joven (apaga las 3 reglas de Personal y Familiar). No es azar: son afiliados jóvenes de un mismo segmento familiar sobre los que el dataset no registra nada más.

## 14.2 Criterio aplicado

**Antes** de calcular `categoria_top`, se evalúa si se cumplen las 5 condiciones a la vez:

```
score_credito            == 0
score_hogar              == 0
score_movilidad          == 0
score_personal_familiar  == 0
score_mascotas           == 0.5   (su base exacta, sin bono ni penalización)
```

Si se cumplen, **no se fuerza ningún desempate** y la fila se marca:

| Campo | Valor |
|---|---|
| `categoria_top` | `"Sin señal suficiente"` |
| `categoria_secundaria` | `null` |
| `requiere_escalamiento` | `true` |
| `reglas_activadas_top` | `"Ninguna regla de propensión se activó con la información disponible"` |

Para **todas las demás filas**, el cálculo sigue exactamente igual que en la v2.

**Por qué la condición incluye `score_mascotas == 0.5` y no `== 0`:** Mascotas nunca puede valer 0, su piso es 0.35. El 0.5 exacto es la señal de que tampoco se activó su bono ni su penalización — o sea que la Fuente 3 no aportó nada específico sobre esa persona. Verificado que la condición es consistente: si Mascotas valiera 0.65 la fila tendría salario bajo (y Crédito ≥ 0.85), y si valiera 0.35 tendría ciudad conocida (y Movilidad ≥ 0.5). En ambos casos alguna otra categoría sería > 0, así que la quinta condición nunca contradice a las otras cuatro.

**Columna nueva:** `requiere_escalamiento` (booleano) — 25 columnas en total. Es `false` en las 496.466 filas restantes.

**Decisión propia menor (D6):** el pedido escribía `reglas_activadas_top` como lista (`["Ninguna regla…"]`). Se escribió como **texto plano**, sin corchetes, para no romper el formato de la columna — en el resto de las filas es texto separado por comas (`DROGUERIA=SI, RANGO_EDAD=…`). Mezclar dos formatos en la misma columna obligaría al bot a parsear dos casos. Reversible en una línea.

## 14.3 Verificación

| Chequeo | Resultado |
|---|---|
| Filas de entrada = filas de salida | **500.000 = 500.000** ✅ |
| Filas en `"Sin señal suficiente"` | **3.534 (0,707 %)** |
| `requiere_escalamiento = true` coincide exactamente con esas filas | ✅ |
| `categoria_secundaria` nula en todas ellas | ✅ 3.534 / 3.534 |
| `reglas_activadas_top` con el texto de sin señal en todas ellas | ✅ 3.534 / 3.534 |
| **Filas que cambiaron de `categoria_top` respecto a v2** | **3.534 — exactamente las de sin señal** ✅ |
| Resto de filas idéntico a v2 (`categoria_top` y `categoria_secundaria`) | ✅ |
| Scores dentro de [0, 1] · sin nulos | ✅ |

**El número resultó ser exactamente 3.534**, el mismo que había reportado en H9. No se asumió: se verificó que la condición de las 5 igualdades captura ni más ni menos que ese conjunto. La razón de que coincida está explicada arriba — las otras dos configuraciones posibles de Mascotas son incompatibles con tener las otras 4 en cero.

**`categoria_top` — v2 vs v3:**

| Categoría | v2 | v3 | Δ |
|---|---:|---:|---:|
| Crédito | 408.900 | **405.366** | −3.534 |
| Hogar | 45.716 | 45.716 | — |
| Personal y Familiar | 41.441 | 41.441 | — |
| Movilidad | 3.943 | 3.943 | — |
| Mascotas | 0 | 0 | — *(§ 13)* |
| **Sin señal suficiente** | — | **3.534** | +3.534 |

Todo el movimiento salió de Crédito, que era donde el desempate las estaba depositando. `categoria_secundaria` de Mascotas baja de 347.505 a 343.971 (−3.534), consistente.

**Ejemplo real** (`SERIE=88806`): F · 20 a 35 años · salario `Desconocido` · `THETA` · ciudad nula · `DROGUERIA=NO`
Scores: Crédito 0.00 · PyF 0.00 · Hogar 0.00 · Movilidad 0.00 · Mascotas 0.50
→ `categoria_top = "Sin señal suficiente"` · `categoria_secundaria` nula · `requiere_escalamiento = True`

## 14.4 Error propio durante la implementación

*(Método AR: reportar qué falló, no solo el resultado.)*

En el primer intento el `reglas_activadas_top` de las filas sin señal salió **vacío**. Causa: puse el bloque que asigna el texto **antes** de la línea que asigna `reglas_activadas_top` para todas las filas, así que esa línea lo sobrescribía con el texto (vacío) de la categoría que había ganado el desempate.

Se sumaron dos errores: mi propio chequeo de verificación **sí detectó** el problema e imprimió `ERROR`, pero yo no había incluido esa variable en el `return` de la función, así que el veredicto final igual decía "TODAS LAS VERIFICACIONES PASARON". El primer error lo habría encontrado el chequeo; el segundo lo dejó pasar.

**Corregido:** el override de sin señal ahora va **después** de la asignación general, y todos los chequeos nuevos están conectados al veredicto final. **Lección:** un chequeo que imprime pero no participa del resultado es peor que no tenerlo — da una falsa sensación de cobertura.

## 14.5 Desviación respecto al plan de la v3

**Desviación: ninguna en el alcance.** No se tocó ningún peso: `score_credito`, `score_hogar`, `score_movilidad`, `score_personal_familiar` y `score_mascotas` se calculan exactamente igual que en la v2, y está verificado que ninguna fila fuera de las 3.534 cambió de categoría.

**Una decisión propia menor:** D6, el formato de texto plano en `reglas_activadas_top` (§ 14.2).

**Señal de alerta de dos fallos seguidos:** no se activó como tal, pero hubo **un** fallo con causa raíz identificada y corregida en la primera vuelta de instrumentación (§ 14.4).

---

## Bitácora de actualizaciones

**#3 — 2026-07-24:** Tercera corrida (v3). Cierra H9: las **3.534 filas sin ninguna señal** dejan de recibir una categoría por desempate entre ceros y pasan a `categoria_top = "Sin señal suficiente"`, `categoria_secundaria` nula, `requiere_escalamiento = true` (columna nueva, 25 en total). Verificado que **solo esas 3.534 filas cambiaron** respecto a v2 y que ningún peso se modificó. Salida: `Usos_Productos_Afiliados_ETIQUETADO_V3.csv` — **el archivo vigente para el motor**. Documentado además (§ 13) que **H8 queda cerrado como decisión de negocio**: que Mascotas nunca gane el top es consciente y correcto — es la categoría con menos evidencia real por diseño, e inflarla para que gane falsearía la propensión y rompería el requisito de explicabilidad del reto. Error propio durante la implementación registrado en § 14.4.

**#2 — 2026-07-24:** Segunda corrida (v2). Aplicados los 3 cambios de negocio que cierran H1 (Crédito graduado en 12 buckets: 2 → 13 valores distintos), H2 (Hogar rebalanceado 0.6+0.4+bonus 0.15: `score_hogar == 1.00` pasó de 0 a 38.624 filas) y H3 (Mascotas con piso 0.50 excluida de `categoria_top`). 61.146 filas (12,23 %) cambiaron de categoría top. Salida nueva: `Usos_Productos_Afiliados_ETIQUETADO_V2.csv` — **el archivo vigente para el motor**; la v1 se conserva como evidencia. Secciones 1-11 no modificadas salvo las marcas de estado. Hallazgos nuevos: **H8** Mascotas ya nunca es primera recomendación (0 filas — comparte predictor con Crédito y siempre pierde), **H9** 3.534 filas reciben Crédito con score 0.00. Ambos requieren decisión de negocio. S1, S2 y S3 quedan aplicadas; S4 pendiente por decisión de negocio.

**#1 — 2026-07-24:** Creación del documento. Etiquetado de las 500.000 filas ejecutado y verificado (5 scores + `categoria_top` + `categoria_secundaria` + `reglas_activadas_top`; 24 columnas de salida). Decisiones propias aplicadas: D1 presencia vs. valor, D2 desempate por confianza, D3 sin renormalizar. Hallazgos reportados: H1 Crédito se lleva el 75,66 % con score idéntico, H2 Hogar nunca llega a 1.00, H3 Mascotas es secundaria del 72 % por su piso fijo, H4 penalización Bucaramanga casi inerte, H5 7,80 % de filas decididas por desempate, H6 7,27 % sin señal fuerte. Sugerencias S1-S4 documentadas sin aplicar.
