# Análisis de la base — hechos observados

Documento de **análisis del dataset**, no de código ni de decisiones de implementación.
Acá van los cruces, perfiles de segmentos y relaciones entre columnas que se van
encontrando al trabajar con la base.

**Regla de este archivo: por defecto, solo hechos verificables.** Conteos, porcentajes y
relaciones de conjunto comprobadas contra el archivo. El cruce de lo que acá se registra lo
hace quien lea, no este documento.

**Excepción, con formato obligatorio:** si una interpretación necesita quedar junto a los datos
que interpreta, va en una **sección aparte marcada 🟡 NOTA DE INTERPRETACIÓN**, nunca mezclada
con las tablas de hechos, y siempre indicando qué la sostiene y qué no se puede concluir con lo
disponible. Hoy hay una: [A1.7](#-a17--nota-de-interpretación-no-es-un-hecho-verificado).

**Cómo se relaciona con los otros `.md` de `apuntes/`:**

| Archivo | Qué contiene |
|---|---|
| [`exploracion_dataset_nuevo.md`](./exploracion_dataset_nuevo.md) | Exploración inicial: esquema, completitud, cardinalidad columna por columna |
| **`db.md`** *(este)* | Análisis posteriores: perfiles de segmentos, cruces entre columnas |
| [`decisiones_limpieza_rango_salarial.md`](./decisiones_limpieza_rango_salarial.md) | Decisiones de limpieza y su razonamiento |
| [`decisiones_etiquetado_hipotesis.md`](./decisiones_etiquetado_hipotesis.md) | Decisiones de etiquetado y su razonamiento |

---

## A1 — Perfil del grupo `categoria_top = "Sin señal suficiente"`

**Fuente:** `Usos_Productos_Afiliados_ETIQUETADO_V3.csv` · **Fecha:** 2026-07-24
**Tamaño del grupo:** 3.534 filas de 500.000 (**0,707 %**)

**Definición del grupo:** filas donde `score_credito`, `score_hogar`, `score_movilidad` y
`score_personal_familiar` valen 0, y `score_mascotas` vale exactamente 0.5.

### A1.1 Columnas con un único valor en las 3.534 filas (100 % del grupo)

| Columna | Valor |
|---|---|
| `RANGO_SALARIAL_LIMPIO` | `Desconocido` |
| `CIUDAD_AFILIADO` | nula |
| `SEGMENTO_GRUPO_FAMILIAR` | `THETA` |
| `SEGMENTO_POBLACIONAL` | `OMEGA` |
| `PIRAMIDE_NUEVA` | `OMICRON` |
| `EMPRESA_FOCO` | `EMP_000001` |
| `DROGUERIA` | `NO` |
| `HOTELES` | `NO` |
| `AGENCIAS` | `NO` |
| `VIVIENDA` | `NO` |
| `PISCILAGO` | `NO` |

### A1.2 Columnas con más de un valor

| Columna | Valor | Filas | % del grupo |
|---|---|---:|---:|
| `CATEGORIA` | MU | 3.453 | 97,71 % |
| | SIGMA | 81 | 2,29 % |
| `RANGO_EDAD` | 20 a 35 años | 2.853 | 80,73 % |
| | Menor de 19 años | 681 | 19,27 % |
| `GENERO` | M | 1.953 | 55,26 % |
| | F | 1.581 | 44,74 % |

### A1.3 Scores — idénticos en las 3.534 filas

| Score | Valor |
|---|---:|
| `score_credito` | 0.00 |
| `score_personal_familiar` | 0.00 |
| `score_hogar` | 0.00 |
| `score_movilidad` | 0.00 |
| `score_mascotas` | 0.50 |

### A1.4 Qué proporción de cada valor cae dentro del grupo

| Valor | En toda la base | En el grupo | % del valor capturado |
|---|---:|---:|---:|
| `RANGO_SALARIAL_LIMPIO = Desconocido` | 4.988 | 3.534 | 70,85 % |
| `SEGMENTO_POBLACIONAL = OMEGA` | 4.988 | 3.534 | 70,85 % |
| `CATEGORIA = MU` | 4.798 | 3.453 | 71,97 % |
| `PIRAMIDE_NUEVA = OMICRON` | 7.081 | 3.534 | 49,91 % |
| `SEGMENTO_GRUPO_FAMILIAR = THETA` | 7.933 | 3.534 | 44,55 % |
| `RANGO_EDAD = Menor de 19 años` | 6.886 | 681 | 9,89 % |
| `RANGO_EDAD = 20 a 35 años` | 248.109 | 2.853 | 1,15 % |
| `EMPRESA_FOCO = EMP_000001` | 408.715 | 3.534 | 0,86 % |
| `DROGUERIA = NO` | 411.769 | 3.534 | 0,86 % |
| `GENERO = M` | 268.710 | 1.953 | 0,73 % |
| `GENERO = F` | 231.290 | 1.581 | 0,68 % |

### A1.5 Comparación de la distribución del grupo contra la base completa

| Columna | Valor | % en el grupo | % en la base |
|---|---|---:|---:|
| `RANGO_EDAD` | 20 a 35 años | 80,73 % | 49,62 % |
| | Menor de 19 años | 19,27 % | 1,38 % |
| `GENERO` | M | 55,26 % | 53,74 % |
| | F | 44,74 % | 46,26 % |
| `CATEGORIA` | MU | 97,71 % | 0,96 % |
| | SIGMA | 2,29 % | 72,82 % |
| `SEGMENTO_GRUPO_FAMILIAR` | THETA | 100 % | 1,59 % |
| `SEGMENTO_POBLACIONAL` | OMEGA | 100 % | 1,00 % |
| `PIRAMIDE_NUEVA` | OMICRON | 100 % | 1,42 % |
| `EMPRESA_FOCO` | EMP_000001 | 100 % | 81,74 % |
| `DROGUERIA` | NO | 100 % | 82,35 % |

### A1.6 Filas que quedan fuera del grupo teniendo `RANGO_SALARIAL_LIMPIO = Desconocido`

De las 4.988 filas sin dato de salario, **1.454 no** pertenecen al grupo:

| Motivo por el que tienen score > 0 | Filas |
|---|---:|
| `RANGO_EDAD` en {36 a 45, 46 a 55, Mayor de 55} | 1.261 |
| `DROGUERIA = SI` | 231 |
| `CIUDAD_AFILIADO` no nula | 0 |
| `SEGMENTO_GRUPO_FAMILIAR` en {LAMBDA, RHO} | 0 |

Las 1.454 tienen `categoria_top = Personal y Familiar`.

---

### 🟡 A1.7 — NOTA DE INTERPRETACIÓN (no es un hecho verificado)

> **Todo lo de A1.1 a A1.6 son hechos medidos contra el archivo. Esta sección NO lo es.**
> Es una lectura de esos hechos, registrada acá por pedido explícito para que quede junto al
> perfil que interpreta. **No debe citarse como dato confirmado ni usarse como regla de negocio
> sin validación de Colsubsidio.**

**Qué se descarta.** La lectura de que este grupo sean "menores de edad" **no cuadra con los
hechos del propio documento**: solo el **19,27 %** del grupo es `Menor de 19 años`; el
**80,73 %** restante está en `20 a 35 años` (A1.2). La edad no explica el grupo.

**Qué variable sí acompaña al grupo completo.** `SEGMENTO_POBLACIONAL = OMEGA` está en el
**100 %** de las 3.534 filas (A1.1), y R1 prueba que OMEGA es exactamente el conjunto sin dato
de ingreso. `CATEGORIA = MU` acompaña al **97,71 %** — alto, pero **no al 100 %**: 81 filas son
`SIGMA` (A1.2), y R3 muestra que MU está *contenida* en OMEGA, no que sean el mismo conjunto
(4.798 ⊂ 4.988, con 190 filas de diferencia).

**Lectura más consistente con los hechos:** el rasgo que define al grupo es **no tener ingreso
propio registrado en el sistema** — posibles beneficiarios dentro del núcleo familiar de un
titular — **sin relación necesaria con la edad**.

**Límite explícito de esta interpretación:** con los datos disponibles **no se puede distinguir**
si `OMEGA` es un segmento demográfico real del negocio o simplemente el "cajón técnico" donde
cae cualquier registro sin dato de ingreso. Ambas cosas producirían exactamente el mismo patrón
observado. Resolverlo requiere confirmación de Colsubsidio, no más análisis del archivo.

**Estado del código:** ninguna acción requerida. La v3 ya trata estas filas correctamente
(`categoria_top = "Sin señal suficiente"`, `requiere_escalamiento = true`).

---

## A2 — Relaciones de conjunto entre columnas (verificadas fila por fila)

**Fuente:** `Usos_Productos_Afiliados_ETIQUETADO_V3.csv` · **Fecha:** 2026-07-24

| # | Relación | Comprobación |
|---|---|---|
| **R1** | `SEGMENTO_POBLACIONAL = OMEGA` y `RANGO_SALARIAL` nulo (`RANGO_SALARIAL_LIMPIO = "Desconocido"`) son **el mismo conjunto exacto** de 4.988 filas | `(desconocido == omega).all()` → `True` |
| **R2** | Ninguna otra categoría de `SEGMENTO_POBLACIONAL` (`ETA`, `PI`, `TAU`, `XI`) contiene un solo nulo de salario | tabla cruzada, 0 en las 4 |
| **R3** | Las 4.798 filas con `CATEGORIA = MU` están **todas** dentro de las 4.988 sin salario | `MU y no-Desconocido` = 0 |
| **R4** | 190 filas sin salario **no** son `MU` (son `SIGMA`) | 4.988 − 4.798 = 190 |
| **R5** | Las 4.988 filas sin salario tienen **todas** `CIUDAD_AFILIADO` nula | ciudad conocida en ese conjunto = 0 |
| **R6** | Las 4.988 filas sin salario tienen **todas** `SEGMENTO_GRUPO_FAMILIAR = THETA` | ninguna es `LAMBDA` ni `RHO` |
| **R7** | `SEGMENTO_GRUPO_FAMILIAR = THETA` (7.933) y `PIRAMIDE_NUEVA = OMICRON` (7.081) **contienen** a las 4.988 sin salario, pero son conjuntos más grandes | 7.933 > 4.988 y 7.081 > 4.988 |

**Distribución completa de `SEGMENTO_POBLACIONAL` contra el nulo de salario:**

| `SEGMENTO_POBLACIONAL` | Con salario | Sin salario |
|---|---:|---:|
| ETA | 127.439 | 0 |
| PI | 134.725 | 0 |
| TAU | 231.119 | 0 |
| XI | 1.729 | 0 |
| **OMEGA** | **0** | **4.988** |

---

## A3 — Corrección a la exploración inicial: `PISCILAGO`

**Fecha:** 2026-07-24

[`exploracion_dataset_nuevo.md`](./exploracion_dataset_nuevo.md) § 2 documenta `PISCILAGO` como
**Booleano, siempre `False`**. Verificado contra el archivo original: la columna es **texto**, y
su único valor es **`"NO"`** en las 500.000 filas.

| Fuente | Tipo | Valor único |
|---|---|---|
| `Usos_Productos_Afiliados_SIN_ID.xlsx` (original) | texto | `NO` — 500.000 filas |
| `Usos_Productos_Afiliados_ETIQUETADO_V3.csv` | texto | `NO` — 500.000 filas |

El hecho de fondo no cambia (la columna es constante y no aporta varianza); lo que estaba mal
documentado es el tipo y la representación del valor.

---

## Bitácora de actualizaciones

**#2 — 2026-07-24:** Se agrega **A1.7**, primera nota de interpretación del documento, marcada
🟡 y separada de los hechos: se descarta la lectura de "menores de edad" (solo el 19,27 % del
grupo lo es) y se registra que el rasgo que acompaña al 100 % del grupo es
`SEGMENTO_POBLACIONAL = OMEGA`, con el límite explícito de que no se puede distinguir si OMEGA
es un segmento demográfico real o el cajón técnico de los registros sin ingreso. Corregido
respecto a lo planteado: `CATEGORIA = MU` acompaña al **97,71 %**, no al 100 % (81 filas son
`SIGMA`), y R3 prueba contención de MU en OMEGA, no identidad. Se ajustó la regla del encabezado
para admitir interpretaciones marcadas, que antes prohibía en absoluto. Sin cambios de código:
la v3 ya trata estas filas correctamente.

**#1 — 2026-07-24:** Creación del documento. Se agregan A1 (perfil de las 3.534 filas del grupo
`"Sin señal suficiente"`), A2 (7 relaciones de conjunto verificadas entre `SEGMENTO_POBLACIONAL`,
`CATEGORIA`, `SEGMENTO_GRUPO_FAMILIAR`, `PIRAMIDE_NUEVA`, `CIUDAD_AFILIADO` y el nulo de
`RANGO_SALARIAL`) y A3 (corrección del tipo de `PISCILAGO` respecto a la exploración inicial).
