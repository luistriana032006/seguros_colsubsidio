# Exploración del dataset nuevo — `Usos_Productos_Afiliados_SIN_ID`

> ⚠️ **Nota de formato:** el archivo entregado no es un CSV — es un **Excel (.xlsx)**. Se procesó con `openpyxl` en modo streaming (sin cargar todo en memoria) y se convirtió a CSV temporal local para analizarlo con **DuckDB**. Nada salió del entorno local.

---

## 🚨 RESPUESTA A LA PREGUNTA MÁS IMPORTANTE (léase primero)

# NO EXISTE NINGUNA COLUMNA QUE INDIQUE QUÉ SEGURO(S) TIENE O COMPRÓ CADA PERSONA

Las 15 columnas del archivo son **perfil del afiliado + uso de servicios y beneficios de Colsubsidio** (hoteles, droguería, agencias, vivienda, piscilago). **Ninguna** columna menciona pólizas, productos de seguro, ni las categorías Mascotas / Hogar / Crédito / Movilidad / Personal y Familiar.

**Conclusión:** seguimos exactamente en el mismo escenario que con el dataset anterior — el motor debe construirse con **reglas de negocio hipotéticas ("SI cualidad ENTONCES categoría")**, no con patrones verificados contra una etiqueta real. Este archivo nuevo cambia el *catálogo de cualidades disponibles* (menos columnas, pero con datos de uso de servicios que antes no teníamos), no la naturaleza del reto.

---

## 1. Inspección básica

| Aspecto | Valor |
|---|---|
| Archivo | `Usos_Productos_Afiliados_SIN_ID.xlsx` |
| Tamaño en disco | 29 MB (30,092,618 bytes) |
| Formato | Excel (.xlsx) — 1 sola hoja llamada `in` |
| Encoding | UTF-8 (interno del formato XLSX; no aplica "delimitador" por no ser texto plano) |
| N° de filas de datos (conteo real) | **500,000** (+ 1 fila de encabezado) |
| Qué representa cada fila | Un afiliado de Colsubsidio (persona), con su perfil demográfico/segmentación y flags de uso de ciertos servicios/beneficios |
| N° de columnas | **15** |
| Filas 100% idénticas entre sí (excluyendo el ID `SERIE`) | 15,560 grupos de duplicados — normal dado que son variables categóricas de baja cardinalidad, no indica error |

**Primeras 5 filas crudas:**

| SERIE | GENERO | RANGO_EDAD | RANGO_SALARIAL | CATEGORIA | SEGMENTO_GRUPO_FAMILIAR | SEGMENTO_POBLACIONAL | PIRAMIDE_NUEVA | EMPRESA_FOCO | CIUDAD_AFILIADO | HOTELES | PISCILAGO | DROGUERIA | AGENCIAS | VIVIENDA |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | F | 36 a 45 años | Entre 8 y 10 SMLV | ZETA | LAMBDA | PI | DELTA | EMP_000001 | BOGOTA D.C. | NO | False | SI | NO | NO |
| 2 | F | 20 a 35 años | Menor al SMLV | SIGMA | CHI | TAU | PSI | EMP_000001 | (vacío) | NO | False | SI | NO | NO |
| 3 | M | 20 a 35 años | Entre 1 y 1.5 SMLV | SIGMA | CHI | PI | XI | EMP_000001 | (vacío) | NO | False | SI | NO | NO |
| 4 | F | 20 a 35 años | Entre 1 y 1.5 SMLV | SIGMA | LAMBDA | ETA | ETA | EMP_000001 | (vacío) | NO | False | SI | NO | NO |
| 5 | M | 20 a 35 años | Entre 1.5 y 2 SMLV | SIGMA | RHO | PI | XI | EMP_000002 | BOGOTA D.C. | NO | False | SI | NO | NO |

---

## 2. Esquema completo

| Columna | Tipo de dato | % nulos | Cardinalidad (valores distintos) |
|---|---|---|---|
| SERIE | Entero (BIGINT) | 0% | 500,000 (único por fila → es el ID de fila) |
| GENERO | Texto | 0% | 2 |
| RANGO_EDAD | Texto (categórico) | 0% | 5 |
| RANGO_SALARIAL | Texto (categórico) | 1.0% | 16 |
| CATEGORIA | Texto (código) | 0% | 4 |
| SEGMENTO_GRUPO_FAMILIAR | Texto (código) | 0% | 7 |
| SEGMENTO_POBLACIONAL | Texto (código) | 0% | 5 |
| PIRAMIDE_NUEVA | Texto (código) | 0% | 10 |
| EMPRESA_FOCO | Texto (código) | 0% | 2 |
| CIUDAD_AFILIADO | Texto | **57.68%** | 310 |
| HOTELES | Texto (SI/NO) | 0% | 2 |
| PISCILAGO | Booleano | 0% | **1** (siempre `False`, sin variación) |
| DROGUERIA | Texto (SI/NO) | 0% | 2 |
| AGENCIAS | Texto (SI/NO) | 0% | 2 |
| VIVIENDA | Texto (SI/NO) | 0% | 2 |

**Alertas de calidad de datos:**
- **`PISCILAGO` es constante** (siempre `False`) — no aporta nada para segmentar ni construir reglas. Se puede descartar.
- **`RANGO_SALARIAL` tiene categorías solapadas/inconsistentes**: conviven etiquetas como "Entre 2 y 2.5 SMLV" y "Entre 2 y 4 SMLV", o "Menor al SMLV" y "Menor a 2 SMLV" — parecen dos esquemas de bucketing mezclados. ~~Afecta muy pocas filas (17 en total)~~ **Corregido 2026-07-24: son 140 filas, no 17** — el 17 era la cardinalidad de la columna (16 etiquetas + nulo), no un conteo de registros. Sigue siendo marginal (0,028 % de la base). **Ya resuelto:** ver [`decisiones_limpieza_rango_salarial.md`](./decisiones_limpieza_rango_salarial.md) y usar la columna `RANGO_SALARIAL_LIMPIO`.
- **`CATEGORIA`, `SEGMENTO_GRUPO_FAMILIAR`, `SEGMENTO_POBLACIONAL` y `PIRAMIDE_NUEVA` usan códigos en letras griegas** (SIGMA, ZETA, LAMBDA, TAU, ETA, DELTA, XI, etc.). **Actualizado 2026-07-23:** negocio confirmó que esto es anonimización intencional — no un diccionario faltante. Preserva consistencia (mismo código = mismo grupo real) pero **no van a divulgar el mapeo código→significado**, así que no hay que seguir pidiéndolo. Sí confirmaron para qué sirve cada *columna* (no cada código): ver [`nomenclatura_afiliados.md`](./nomenclatura_afiliados.md). Esto sigue limitando la explicabilidad a nivel de "qué significa LAMBDA exactamente", pero ya no es un hueco de información pendiente — es una restricción de diseño con la que hay que trabajar.

---

## 3. ¿Existe una etiqueta de producto/póliza?

**NO.** Ya respondido arriba con el máximo detalle. Para que quede registrado en el lugar que pide la plantilla: se revisaron las 15 columnas una por una y ninguna representa tenencia de seguro, tipo de póliza, prima, fecha de compra ni similar. Lo más cercano son 4 flags binarios de **uso de servicios/beneficios de Colsubsidio** (HOTELES, DROGUERIA, AGENCIAS, VIVIENDA), que **no son seguros** — son servicios de bienestar/subsidio.

---

## 4. Catálogo de cualidades por grupo temático

### 🧑 Demográficas
| Columna | Qué representa | Valores reales | % completitud |
|---|---|---|---|
| GENERO | Sexo del afiliado | `M`, `F` | 100% |
| RANGO_EDAD | Rango etario | "20 a 35 años", "36 a 45 años", "46 a 55 años", "Mayor de 55 años", "Menor de 19 años" | 100% |

### 💰 Financieras / laborales
| Columna | Qué representa | Valores reales | % completitud |
|---|---|---|---|
| RANGO_SALARIAL | Rango de ingreso en Salarios Mínimos (SMLV) | "Menor al SMLV", "Entre 1 y 1.5 SMLV", "Entre 2 y 2.5 SMLV", "Entre 6 y 8 SMLV", "Mayor a 30 SMLV" | 99.0% |
| EMPRESA_FOCO | Empresa empleadora (anonimizada como código) | `EMP_000001` (81.7%), `EMP_000002` (18.3%) | 100% |

### 👪 Familiares / segmentación interna Colsubsidio (⚠️ códigos individuales anonimizados — ver [`nomenclatura_afiliados.md`](./nomenclatura_afiliados.md))
| Columna | Qué representa (confirmado por negocio, 2026-07-23) | Valores reales | % completitud |
|---|---|---|---|
| SEGMENTO_GRUPO_FAMILIAR | Clasifica la composición del hogar / estructura familiar del afiliado. Cada código (LAMBDA, RHO, etc.) es un grupo real distinto, pero su significado exacto no se divulga. | LAMBDA (57.3%), RHO (24.3%), EPSILON (9.4%), IOTA, CHI, THETA, PI | 100% |
| CATEGORIA | Categoría del afiliado dentro del sistema de subsidio familiar. Es la que menos detalle adicional dieron — sin más contexto sobre qué distingue un nivel de otro. | SIGMA (72.8%), PI (16.4%), ZETA (9.8%), MU (1.0%) | 100% |
| SEGMENTO_POBLACIONAL | Segmentación individual del afiliado, construida a partir de ingresos, edad y PAC. | TAU (46.2%), PI (26.9%), ETA (25.5%), OMEGA, XI | 100% |
| PIRAMIDE_NUEVA | Clasifica la **empresa aportante** (no al afiliado directamente) dentro de la pirámide empresarial de Colsubsidio. | ETA (31.2%), XI (21.7%), UPSILON (20.4%), DELTA, BETA, OMEGA, KAPPA, LAMBDA, OMICRON, PSI | 100% |

### 📍 Ubicación
| Columna | Qué representa | Valores reales | % completitud |
|---|---|---|---|
| CIUDAD_AFILIADO | Ciudad/municipio de residencia del afiliado | "BOGOTA D.C." (34.7% del total, 60% de los no-nulos), "SOACHA", "FUSAGASUGA", "MOSQUERA", "ZIPAQUIRA" | **42.32%** (57.68% de nulos) |

### 🏢 Relación con Colsubsidio / uso de servicios
| Columna | Qué representa | Valores reales | % completitud |
|---|---|---|---|
| HOTELES | ¿Usó el beneficio de hoteles Colsubsidio? | `NO` (99.97%), `SI` (0.03%) | 100% |
| DROGUERIA | ¿Usó droguería/farmacia Colsubsidio? | `NO` (82.35%), `SI` (17.65%) | 100% |
| AGENCIAS | ¿Usó agencias/puntos de atención Colsubsidio? | `NO` (99.98%), `SI` (0.02%) | 100% |
| VIVIENDA | ¿Usó beneficio de vivienda Colsubsidio? | `NO` (99.99%), `SI` (0.007%) | 100% |
| PISCILAGO | ¿Usó Piscilago (parque)? | `False` — **siempre**, sin ningún `True` | 100% (pero sin información útil) |

### 🔑 Identificador
| Columna | Qué representa | % completitud |
|---|---|---|
| SERIE | Consecutivo único de fila (1 a 500,000). Reemplaza el ID real (de ahí "SIN_ID" en el nombre del archivo) | 100% |

---

## 5. Cruces candidatos por cada categoría de seguro

Se muestra **qué es construible** con lo que hay — no se decide la regla final, eso queda para la reunión de negocio.

### 🐾 Mascotas
**No hay ninguna columna relacionada con mascotas** (tenencia, tipo, gasto veterinario). Lo único disponible son proxies demográficos genéricos y muy débiles:
- Columnas candidatas: `RANGO_EDAD`, `SEGMENTO_GRUPO_FAMILIAR` (si algún código griego terminara significando "hogar con niños/mascotas", habría que confirmarlo con negocio).
- Hipótesis posible (débil): "SI SEGMENTO_GRUPO_FAMILIAR = LAMBDA Y RANGO_EDAD = 20 a 35 años ENTONCES propensión a Mascotas" — **sin ninguna evidencia directa que la sostenga**, es una apuesta ciega.
- Fila de ejemplo: `SERIE=1, RANGO_EDAD=36 a 45 años, SEGMENTO_GRUPO_FAMILIAR=LAMBDA` — no hay nada en la fila que hable de mascotas.

### 🏠 Hogar
- Columnas candidatas: `VIVIENDA` (uso del beneficio de vivienda Colsubsidio), `CIUDAD_AFILIADO`, `RANGO_SALARIAL`.
- Hipótesis posible: **"SI VIVIENDA = SI ENTONCES propensión a seguro de Hogar"** (ya usa un beneficio de vivienda de la caja, es candidato natural a proteger esa vivienda).
- Fila de ejemplo real: `SERIE=8350, GENERO=M, RANGO_EDAD=20 a 35 años, RANGO_SALARIAL=Entre 1 y 1.5 SMLV, CIUDAD_AFILIADO=(vacío), VIVIENDA=SI`.

### 💳 Crédito
- Columnas candidatas: `RANGO_SALARIAL`, `EMPRESA_FOCO`, `CATEGORIA` (pendiente de significado real).
- Hipótesis posible: "SI RANGO_SALARIAL está entre 1 y 2 SMLV ENTONCES propensión a seguro de Crédito" (rango de ingreso medio-bajo, perfil típico de quien toma crédito de libranza/consumo).
- Fila de ejemplo real: `SERIE=2, GENERO=F, RANGO_SALARIAL=Menor al SMLV, CATEGORIA=SIGMA, EMPRESA_FOCO=EMP_000001`.

### 🚗 Movilidad
**Tampoco hay columnas directas** (vehículo, moto, siniestros de tránsito). Proxies muy débiles:
- Columnas candidatas: `CIUDAD_AFILIADO` (afiliados en municipios aledaños a Bogotá como Soacha, Mosquera, Zipaquirá, Funza sugieren desplazamientos largos → posible necesidad de movilidad/seguro vehicular), `AGENCIAS` (visitas físicas).
- Hipótesis posible (débil): "SI CIUDAD_AFILIADO está en el área metropolitana pero no es Bogotá D.C. ENTONCES propensión a Movilidad" — supone que necesita transportarse más, no está verificado.
- Fila de ejemplo real: `SERIE` con `CIUDAD_AFILIADO=SOACHA` (hay 8,790 casos así).

### 👨‍👩‍👧 Personal y Familiar
Es la categoría con **más señales indirectas disponibles**:
- Columnas candidatas: `SEGMENTO_GRUPO_FAMILIAR`, `RANGO_EDAD`, `DROGUERIA` (uso de farmacia → posible indicador de cuidado de salud propio o familiar), `HOTELES`/`PISCILAGO` (uso recreativo familiar, aunque PISCILAGO no varía).
- Hipótesis posible: "SI DROGUERIA = SI Y SEGMENTO_GRUPO_FAMILIAR = RHO ENTONCES propensión a seguro Personal y Familiar" (usa farmacia con regularidad, perfil de cuidado de salud del núcleo familiar).
- Fila de ejemplo real: `SERIE=1, RANGO_EDAD=36 a 45 años, SEGMENTO_GRUPO_FAMILIAR=LAMBDA, DROGUERIA=SI`.

---

## 6. Huecos — qué NO tenemos

| Categoría | Qué falta (cualidad obvia que NO está) |
|---|---|
| 🐾 Mascotas | Nada de nada: sin tenencia de mascota, tipo, cantidad, gasto veterinario. Es el hueco más grande de los 5. |
| 🏠 Hogar | Sin estrato, sin tipo de vivienda (propia/arrendada), sin avalúo/valor del inmueble, sin metros cuadrados. Solo un flag binario de "usó beneficio de vivienda de Colsubsidio", que no equivale a "tiene casa propia". |
| 💳 Crédito | Sin historial crediticio, score, deuda actual, mora, ni uso de líneas de crédito de la caja. Solo un proxy indirecto de ingreso. |
| 🚗 Movilidad | Sin tenencia de vehículo/moto, tipo, kilometraje, siniestros de tránsito. Solo la ciudad de residencia como proxy geográfico débil. |
| 👨‍👩‍👧 Personal y Familiar | Sin número exacto de hijos/dependientes, sin edades de hijos, sin diagnósticos o antecedentes de salud. El "grupo familiar" existe pero está codificado sin diccionario. |

**Hueco transversal a las 5 categorías (actualizado 2026-07-23):** los códigos en letras griegas (`CATEGORIA`, `SEGMENTO_GRUPO_FAMILIAR`, `SEGMENTO_POBLACIONAL`, `PIRAMIDE_NUEVA`) son anonimización intencional, no un diccionario pendiente — negocio ya confirmó para qué sirve cada columna (ver [`nomenclatura_afiliados.md`](./nomenclatura_afiliados.md)) pero no va a revelar qué significa cada código individual. Cualquier hipótesis que dependa de "cuál código es cuál" sigue sin poder confirmarse — pero hipótesis que solo necesitan "mismo código = mismo grupo" (agrupar, contar, comparar segmentos entre sí) ya están respaldadas.

---

## 7. Comparación con el dataset anterior

No se encontraron en este directorio los archivos `analisis_csv_exploratorio.md` ni `catalogo_cualidades_para_hipotesis.md` — solo existe `reglas_documentacion_agent.md` (reglas del agente, no un análisis previo). Se omite esta sección para no inventar una comparación sin base real. Si el análisis anterior está en otra carpeta o repo, compártelo y se actualiza esta sección.

---

## 8. Datos sensibles (Ley 1581 / 1266 de Colombia)

| Columna | Tipo de dato sensible |
|---|---|
| GENERO | Dato personal (género) |
| RANGO_EDAD | Dato personal (edad) |
| RANGO_SALARIAL | **Dato financiero** — ingreso económico |
| EMPRESA_FOCO | Dato laboral (empleador) |
| CIUDAD_AFILIADO | Dato de ubicación/residencia |
| DROGUERIA | Posible **dato de salud** (uso de farmacia puede insinuar tratamiento/condición de salud) — tratar con la misma cautela que datos sensibles de salud aunque no sea un diagnóstico explícito |
| CATEGORIA / SEGMENTO_* / PIRAMIDE_NUEVA | Clasificaciones internas potencialmente derivadas de datos sensibles (ingreso, salud, composición familiar) — al no tener diccionario, tratar con precaución hasta confirmar qué agregan |
| VIVIENDA, HOTELES, AGENCIAS | Datos de comportamiento/consumo de servicios — personales aunque de menor sensibilidad |
| SERIE | Identificador de fila anonimizado (no es el ID real del afiliado, ya fue removido — de ahí "SIN_ID") |

**Recomendación:** igual que con el dataset anterior, todo el análisis debe permanecer en el entorno local. No subir este archivo ni extractos con estas columnas a herramientas o servicios externos.

---

## Bitácora de actualizaciones

**#2 — 2026-07-24:** Ejecutada la limpieza de `RANGO_SALARIAL`, la única pendiente real del dataset (sección 2, "Alertas de calidad de datos"). Se corrigió ahí mismo el conteo erróneo: **140 filas** usaban el esquema de bucketing grueso, no 17 — el 17 era la cardinalidad de la columna reportada en el esquema (§ 2), confundida con conteo de registros. Se remapearon al bucket fino más poblado de cada rango y los 4.988 nulos pasaron a `"Desconocido"`; **ninguna fila borrada, 500.000 antes y después**. Resultado en `Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv`, columna nueva `RANGO_SALARIAL_LIMPIO` (la original se conserva al lado). Razonamiento mapeo por mapeo en [`decisiones_limpieza_rango_salarial.md`](./decisiones_limpieza_rango_salarial.md). El resto de alertas de este documento se mantienen sin tocar por decisión explícita (PISCILAGO, activación baja, códigos griegos, "duplicados").

**#1 — 2026-07-23:** Negocio respondió la pregunta abierta sobre los códigos en letras griegas (secciones 2, 4 y 6): es anonimización intencional, no un diccionario faltante. Se confirmó el propósito de cada columna (`CATEGORIA`, `SEGMENTO_GRUPO_FAMILIAR`, `SEGMENTO_POBLACIONAL`, `PIRAMIDE_NUEVA`), pero el mapeo código→significado individual no se va a divulgar. Detalle completo en [`nomenclatura_afiliados.md`](./nomenclatura_afiliados.md). Pendiente: tipos de seguro de Colsubsidio para cruzar con estas columnas (el usuario los va a pasar aparte).
