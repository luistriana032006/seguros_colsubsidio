# Decisiones de limpieza — `RANGO_SALARIAL`

> **Bloque de trabajo:** limpieza quirúrgica de una sola columna del dataset.
> **Fecha de ejecución:** 2026-07-24
> **Estado:** ✅ cerrado, verificado, reproducible.
> Documento redactado bajo el marco de [`reglas_documentacion_agent.md`](../reglas_documentacion_agent.md) (Método AR).

| | |
|---|---|
| Script | [`../limpieza_rango_salarial.py`](../limpieza_rango_salarial.py) |
| Entrada | `../Usos_Productos_Afiliados_SIN_ID.xlsx` — **no se modificó** |
| Salida | `../Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv` — 500.000 filas × 16 columnas |
| Contexto previo | [`exploracion_dataset_nuevo.md`](./exploracion_dataset_nuevo.md), [`nomenclatura_afiliados.md`](./nomenclatura_afiliados.md) |
| Reproducir | `python3 limpieza_rango_salarial.py` (~1 min, dominado por la lectura del Excel) |

---

## 0. Alcance — qué entró y qué NO entró en este bloque

*(Método AR: "Identificá qué NO entra en el bloque de trabajo actual… No 'mejores' cosas fuera de ese alcance sin avisar primero.")*

**Sí entró:** la columna `RANGO_SALARIAL`, y nada más.

**Explícitamente NO entró** — el usuario lo marcó como fuera de alcance y no se tocó nada de esto:

| Fuera de alcance | Por qué no se tocó |
|---|---|
| Deduplicación de filas | Los ~15.560 grupos "duplicados" NO son duplicados: son personas distintas que coinciden en columnas de baja cardinalidad. Con 500.000 filas y pocas categorías por columna, la coincidencia es matemáticamente esperable. Deduplicar borraría personas reales. |
| `PISCILAGO` | No es un error de dato; es una variable sin varianza. Se excluye del modelo, no se "arregla". |
| `HOTELES`, `AGENCIAS`, `VIVIENDA` | Activación casi nula pero **real**. Corregirlos sería inventar activación que no ocurrió. |
| Códigos griegos (`CATEGORIA`, `SEGMENTO_*`, `PIRAMIDE_NUEVA`) | Anonimización intencional confirmada por negocio (ver [`nomenclatura_afiliados.md`](./nomenclatura_afiliados.md)). No es un hueco de información. |
| Cualquier otra columna | El pedido fue quirúrgico. Ninguna otra columna se leyó para escribir, solo se copió tal cual al archivo de salida. |

**Regla dura de todo el bloque:** no se borra ninguna fila, ni silenciosamente ni a propósito. **Entran 500.000, salen 500.000.**

---

## 1. Diagnóstico (estado antes de tocar nada)

`RANGO_SALARIAL` es la única columna con un problema real: **conviven dos esquemas de bucketing distintos en la misma columna**.

| Valor | Filas | % | Esquema |
|---|---:|---:|---|
| Entre 1 y 1.5 SMLV | 302.490 | 60,498 % | dominante |
| Entre 1.5 y 2 SMLV | 41.805 | 8,361 % | dominante |
| Menor al SMLV | 33.868 | 6,774 % | dominante |
| Entre 2 y 2.5 SMLV | 27.295 | 5,459 % | dominante |
| Entre 3 y 4 SMLV | 23.780 | 4,756 % | dominante |
| Entre 4 y 6 SMLV | 23.021 | 4,604 % | dominante |
| Entre 2.5 y 3 SMLV | 19.347 | 3,869 % | dominante |
| Entre 10 y 20 SMLV | 9.778 | 1,956 % | dominante |
| Entre 6 y 8 SMLV | 8.721 | 1,744 % | dominante |
| *(nulo)* | 4.988 | 0,998 % | nulo |
| Entre 8 y 10 SMLV | 3.098 | 0,620 % | dominante |
| Entre 20 y 30 SMLV | 1.238 | 0,248 % | dominante |
| Mayor a 30 SMLV | 431 | 0,086 % | dominante |
| **Menor a 2 SMLV** | **123** | 0,025 % | **minoritario** |
| **Entre 2 y 4 SMLV** | **13** | 0,003 % | **minoritario** |
| **Entre 4 y 8 SMLV** | **3** | 0,001 % | **minoritario** |
| **Entre 8 y 19 SMLV** | **1** | 0,000 % | **minoritario** |

**Los dos esquemas:**

- **Dominante (fino) — 494.872 filas (98,974 %)**, 12 buckets:
  `Menor al SMLV`, `Entre 1 y 1.5`, `1.5 y 2`, `2 y 2.5`, `2.5 y 3`, `3 y 4`, `4 y 6`, `6 y 8`, `8 y 10`, `10 y 20`, `20 y 30`, `Mayor a 30`.
- **Minoritario (grueso) — 140 filas (0,028 %)**, 4 buckets, cada uno del doble de ancho:
  `Menor a 2`, `2 y 4`, `4 y 8`, `8 y 19`.

**Otras verificaciones del diagnóstico:** 0 valores con espacios sobrantes, 0 strings vacíos, 0 variantes de mayúsculas/minúsculas del mismo valor. El único desorden es el de esquemas — no hay nulos disfrazados de texto.

### 🔴 Error encontrado en la documentación previa

*(Método AR: "reportá… qué errores encontraste")*

`CLAUDE.md` afirmaba que el esquema minoritario eran **"~17 filas"**. El conteo real es **140 filas** repartidas en 4 valores.

**Causa del error:** el 17 corresponde al número de **valores únicos** de la columna (16 etiquetas distintas + el nulo), no al número de filas. Se confundió cardinalidad con conteo de registros. El dato "16" aparece efectivamente como cardinalidad de `RANGO_SALARIAL` en [`exploracion_dataset_nuevo.md`](./exploracion_dataset_nuevo.md) § 2.

**Acción tomada:** se corrigió `CLAUDE.md` en los tres lugares donde aparecía el dato inválido (tabla de columnas, sección de limpieza, log de decisiones). No se dejó documentación desactualizada.

**Impacto sobre el trabajo:** ninguno en el criterio — remapear 140 filas o 17 se resuelve igual. El impacto es de confianza en la cifra: 140 sigue siendo el 0,028 % de la base, así que la conclusión de fondo ("es una excepción marginal, no un problema estructural") se mantiene intacta.

---

## 2. Tabla de equivalencia — remapeo, no borrado

**Criterio único y uniforme:** cada bucket grueso se solapa con varios buckets finos. Se asigna el bucket fino que **concentra más población dentro de ese solape** — es decir, el destino más probable para una persona de la que solo sabemos que cae en el rango ancho. Es asignación por máxima verosimilitud, no una elección estética.

| Valor original | Valor remapeado | Filas | Por qué este mapeo específico |
|---|---|---:|---|
| `Menor a 2 SMLV` | `Entre 1 y 1.5 SMLV` | 123 | El rango 0–2 SMLV lo cubren tres buckets finos: `Menor al SMLV` (33.868), `Entre 1 y 1.5` (302.490) y `Entre 1.5 y 2` (41.805). De cada 100 afiliados que ganan menos de 2 SMLV, ~80 están en el tramo 1–1.5. Es, con diferencia, el destino más probable. |
| `Entre 2 y 4 SMLV` | `Entre 2 y 2.5 SMLV` | 13 | El rango 2–4 lo cubren `2 y 2.5` (27.295), `2.5 y 3` (19.347) y `3 y 4` (23.780). El tramo 2–2.5 es el más poblado de los tres y además el más angosto: la densidad de afiliados por SMLV es ahí más del doble que en los otros dos. |
| `Entre 4 y 8 SMLV` | `Entre 4 y 6 SMLV` | 3 | El rango 4–8 lo cubren solo dos buckets: `4 y 6` (23.021) y `6 y 8` (8.721). El primero tiene 2,6 veces más gente. |
| `Entre 8 y 19 SMLV` | `Entre 10 y 20 SMLV` | 1 | El rango 8–19 lo cubren `8 y 10` (3.098) y la mayor parte de `10 y 20` (9.778). Aun descontando el tramo 19–20 que sobra, `10 y 20` aporta ~3 veces más población. **Salvedad:** el bucket destino se extiende 1 SMLV más allá del original. Aceptable porque es 1 sola fila y ninguna hipótesis del motor distingue 19 de 20 SMLV — ambos caen en el mismo perfil de ingreso alto. |

**Explicación en una frase, si alguien pregunta en el jurado:**
> *"Esa fila venía con un rango más ancho que el resto de la base; la pusimos en el tramo fino donde está la mayoría de la gente de ese mismo rango ancho."*

### Por qué remapear y no borrar estas 140 filas

Son personas reales con dato salarial válido, solo expresado con otra granularidad. Borrarlas eliminaría 140 afiliados completos —con su edad, ciudad, género y segmento intactos— para resolver un problema de formato. El error máximo que introduce el remapeo es de medio SMLV **dentro del mismo perfil de ingreso**; el error de borrarlas es perder el 100 % de su información.

### Alternativa evaluada y descartada: unificar al revés (fino → grueso)

Colapsar los 12 buckets finos en los 4 gruesos "arreglaría" la inconsistencia **sin ninguna suposición** — es la opción técnicamente más conservadora y hay que decir que existe.

Se descartó porque destruiría resolución en 494.872 filas para acomodar 140. `RANGO_SALARIAL` es la variable clave de las hipótesis de **Crédito** (confianza alta) y entra en **Hogar** y **Movilidad**; perder la distinción entre 1–1.5 y 1.5–2 SMLV degradaría el motor justo donde más se apoya. **Se ajusta la excepción a la regla, no la regla a la excepción.**

---

## 3. Nulos → `"Desconocido"`

**4.988 filas (0,998 %) sin `RANGO_SALARIAL` se recategorizan como `"Desconocido"`. Ninguna se elimina.**

**Por qué:** esa fila sigue teniendo datos válidos en el resto de columnas —edad, ciudad, género, segmento, uso de droguería— que sirven para hipótesis que no dependen del salario. Borrar la fila completa penalizaría categorías que no tienen nada que ver con el problema real: por ejemplo, una persona sin dato salarial pero con `DROGUERIA = SI` y grupo familiar conocido sigue siendo una señal fuerte para **Personal y Familiar**, y perderla empobrece esa hipótesis por un hueco que solo afecta a **Crédito**.

`"Desconocido"` es además una categoría honesta: le dice al motor **"no sé"**, que es distinto de **"no existe"**. Es el mismo criterio ya aplicado a `CIUDAD_AFILIADO` (57,68 % de nulos tratados como categoría "Desconocida"), así que el dataset queda coherente consigo mismo.

---

## 4. Trazabilidad

- La columna original `RANGO_SALARIAL` **no se sobrescribió**: queda intacta en el archivo de salida.
- Se creó `RANGO_SALARIAL_LIMPIO` **inmediatamente a la derecha** de la original, para que la comparación fila por fila sea visual e inmediata.
- El resultado se guardó en un **archivo nuevo**. El Excel original no fue modificado.

Para ver exactamente qué cambió:

```python
import pandas as pd
df = pd.read_csv("Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv")
cambiadas = df[df["RANGO_SALARIAL"].fillna("(nulo)") != df["RANGO_SALARIAL_LIMPIO"]]
print(cambiadas[["RANGO_SALARIAL", "RANGO_SALARIAL_LIMPIO"]].value_counts(dropna=False))
# 4.988 nulos -> Desconocido, y las 140 filas del esquema minoritario
```

Salida real de ese snippet (ejecutado sobre el archivo generado):

```
RANGO_SALARIAL     RANGO_SALARIAL_LIMPIO
NaN                Desconocido              4988
Menor a 2 SMLV     Entre 1 y 1.5 SMLV        123
Entre 2 y 4 SMLV   Entre 2 y 2.5 SMLV         13
Entre 4 y 8 SMLV   Entre 4 y 6 SMLV            3
Entre 8 y 19 SMLV  Entre 10 y 20 SMLV          1
```

---

## 5. Verificación

| Métrica | Resultado |
|---|---:|
| Filas que cambiaron de valor (remapeo de esquema) | **140** |
| Filas que quedaron como `"Desconocido"` | **4.988** |
| Filas idénticas a la original | **494.872** |
| Filas de entrada | 500.000 |
| **Filas de salida** | **500.000 ✅** |

Chequeos automáticos que corre el script, todos en OK:

- ✅ Ninguna fila perdida (entrada = salida = 500.000).
- ✅ Columna original intacta (su `value_counts` es idéntico al del Excel, releído desde disco para comparar).
- ✅ Ningún valor del esquema minoritario sobrevive en la columna limpia.
- ✅ Ningún nulo en la columna limpia.
- ✅ Ningún valor inesperado fuera de los dos esquemas conocidos — **el script avisa en grande si aparece uno**, en vez de dejarlo pasar en silencio.

**Distribución final de `RANGO_SALARIAL_LIMPIO`** (13 valores: 12 buckets + `Desconocido`):

| Valor | Filas | % |
|---|---:|---:|
| Menor al SMLV | 33.868 | 6,774 % |
| Entre 1 y 1.5 SMLV | 302.613 | 60,523 % |
| Entre 1.5 y 2 SMLV | 41.805 | 8,361 % |
| Entre 2 y 2.5 SMLV | 27.308 | 5,462 % |
| Entre 2.5 y 3 SMLV | 19.347 | 3,869 % |
| Entre 3 y 4 SMLV | 23.780 | 4,756 % |
| Entre 4 y 6 SMLV | 23.024 | 4,605 % |
| Entre 6 y 8 SMLV | 8.721 | 1,744 % |
| Entre 8 y 10 SMLV | 3.098 | 0,620 % |
| Entre 10 y 20 SMLV | 9.779 | 1,956 % |
| Entre 20 y 30 SMLV | 1.238 | 0,248 % |
| Mayor a 30 SMLV | 431 | 0,086 % |
| Desconocido | 4.988 | 0,998 % |
| **Total** | **500.000** | **100 %** |

El impacto sobre la distribución es despreciable: el bucket más afectado (`Entre 1 y 1.5 SMLV`) pasa de 60,498 % a 60,523 %, un movimiento de **0,025 puntos porcentuales**.

---

## 6. Decisiones propias del agente

*(Método AR: "Si tomaste una decisión que no estaba en el plan, marcala explícitamente como decisión propia. No la mezcles como si fuera parte del pedido original.")*

Estas tres **no estaban en el pedido**. Se marcan aparte para que puedan revertirse sin tocar lo pedido:

| # | Decisión propia | Por qué se tomó | Reversible |
|---|---|---|---|
| D1 | **Documentar la alternativa descartada** (colapsar fino → grueso, § 2) | Es la objeción obvia que puede aparecer en el jurado. Dejarla escrita convierte "no se nos ocurrió" en "lo evaluamos y esta es la razón". | N/A — es solo documentación |
| D2 | **Recomendación abierta sobre `"Desconocido"` en la similitud** (§ 7) | Toca el pendiente #2 de `CLAUDE.md` (pesos), que **no** es este bloque. Por eso se dejó anotado, **no implementado**. | N/A — no se implementó |
| D3 | **Salida en CSV** en vez de Excel | Inspeccionable fila por fila con cualquier herramienta y mucho más rápido de leer desde el motor que un `.xlsx` de 500k filas. | Sí — una línea (`to_csv` → `to_parquet`) si se prefiere Parquet para la etapa de `NearestNeighbors` |

---

## 7. Qué falta / qué verificar en la próxima sesión

*(Método AR: "generá o actualizá un resumen corto de 'qué se hizo / qué falta / qué verificar'")*

**Qué se hizo:** `RANGO_SALARIAL` limpia y verificada. 140 remapeos + 4.988 nulos a `"Desconocido"`, en columna nueva, archivo nuevo, 0 filas perdidas.

**Qué falta (hereda al siguiente bloque):**

1. **Decidir el peso de `"Desconocido"` en la función de similitud** — pendiente #2 de `CLAUDE.md`. `"Desconocido"` es un valor más de la columna, así que dos perfiles sin dato salarial se parecerán entre sí por esa vía. **Recomendación (decisión D2, no implementada): que el match `Desconocido = Desconocido` sea neutro, no que sume.** Coincidir en la ausencia de un dato no es evidencia de parecerse.
2. **Etiquetar las 500.000 filas con las hipótesis de negocio** — pendiente #5 de `CLAUDE.md`, siguiente paso natural. Debe partir del CSV limpio, no del Excel.

**Qué verificar antes de seguir:**

- Que todo consumidor nuevo lea **`RANGO_SALARIAL_LIMPIO`** y no `RANGO_SALARIAL`. La original se conserva **solo como evidencia de auditoría**; si el motor la usa por error, vuelven los dos esquemas y los nulos.
- Que el archivo de trabajo sea `Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv`. El `.xlsx` original ya no es la fuente de verdad para el motor.

---

## 8. Desviación respecto al plan original

*(Método AR: "Reportá cuánto te desviaste del plan original y por qué, aunque no te lo pidan explícitamente.")*

**Desviación de ejecución: ninguna.** Los 5 pasos pedidos (diagnóstico → remapeo → nulos → trazabilidad → verificación) se ejecutaron en orden y completos. No se tocó ninguna columna fuera de alcance, no se dedupló, no se borró ninguna fila.

**Dos desviaciones menores, ambas hacia arriba:**

1. **Un dato del pedido resultó ser incorrecto y se corrigió** (§ 1): el pedido decía "~17 filas según el diagnóstico previo"; son 140. Se reportó antes de continuar y se ejecutó sobre la cifra real, no sobre la asumida.
2. **Se actualizó `CLAUDE.md`**, que no estaba en el pedido explícito. Se hizo porque el Método AR lo exige ("Nunca dejes un documento de contexto desactualizado después de un cambio que lo invalida") y porque el cambio invalidaba tres secciones.

**Señal de alerta de dos fallos seguidos:** no se activó. Ningún paso falló ni requirió un segundo intento.

**Único error propio durante la ejecución:** el snippet de verificación de § 4 se escribió mal en la primera versión de este documento (usaba un `.where()` innecesario que no capturaba bien los nulos). Se detectó al ejecutarlo de verdad contra el archivo generado, se corrigió y se pegó la salida real. Lección: no publicar código de ejemplo en documentación sin correrlo — un snippet que no corre es peor que ninguno, porque el siguiente lo copia.

---

## Bitácora de actualizaciones

**#1 — 2026-07-24:** Creación del documento. Limpieza de `RANGO_SALARIAL` ejecutada y verificada (140 remapeos + 4.988 nulos a `"Desconocido"`, 500.000 filas intactas). Se corrigió el dato "~17 filas" de `CLAUDE.md` → **140 filas** (era la cardinalidad de la columna, no el conteo de registros). Documento reubicado de la raíz del proyecto a `apuntes/` y reescrito bajo el marco del Método AR. Pendiente heredado: peso de `"Desconocido"` en la función de similitud (§ 7).
