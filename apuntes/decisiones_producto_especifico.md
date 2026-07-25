# Decisiones de emparejamiento categoría → producto específico

> **Bloque de trabajo:** pendiente #6 de `CLAUDE.md` — emparejar la `categoria_top` de cada persona con un producto concreto del catálogo de la Base Maestra.
> **Fecha:** 2026-07-24
> **Estado:** ✅ **COMPLETO Y VERIFICADO.**
> Documento redactado bajo el marco de [`reglas_documentacion_agent.md`](../reglas_documentacion_agent.md) (Método AR).

> ⚠️ **Este documento cubre TRES rondas.** Las secciones 1-6 son el **primer intento**, que quedó **bloqueado** en el paso 0.75 por falta del catálogo; se conservan sin modificar. Las **§ 7-15 son el segundo intento**, que cerró el bloque y produjo V1. La **§ 16 es la tercera ronda**, que produjo **V2 — el archivo vigente**.

| | Intento 1 (bloqueado) | Intento 2 (vigente) |
|---|---|---|
| Sección | § 1-6 | § 7-13 |
| Scripts | `estructurar_hipotesis.py` | [`../estructurar_hipotesis.py`](../estructurar_hipotesis.py) *(iterado)* + [`../emparejar_producto.py`](../emparejar_producto.py) |
| Insumos | solo `Hipotesis_Generales_Seguros.md` (v1) | + `catalogo_productos.csv` (24 productos) + `.md` actualizado |
| `hipotesis_producto_estructuradas.csv` | 9 filas | 21 filas → **24 en la 3ª ronda** |
| Salida | ⛔ ninguna | `PRODUCTO_V1.csv` → **`../Usos_Productos_Afiliados_PRODUCTO_V2.csv`** (vigente, § 16) |

**Reproducir:** `python3 estructurar_hipotesis.py && python3 emparejar_producto.py` (~1 min)

---

## 0. Estado de cada paso del pedido

| Paso | Intento 1 | Intento 2 |
|---|---|---|
| **0** — Aclaración del desajuste de edad en `CLAUDE.md` | ✅ texto literal | *(sin cambios)* |
| **0.5** — Estructurar hipótesis de prosa a CSV | ✅ 9 filas, 3 avisos | ✅ **21 filas**, 24 productos |
| **0.75** — Verificar catálogo de productos | 🔴 no existía → bloqueo | ✅ **resuelto** |
| **1** — Filtro de elegibilidad dura | ⛔ | ✅ |
| **2** — Ranking por hipótesis | ⛔ | ✅ |
| **3** — Productos sin hipótesis | ⛔ | ✅ |
| Salida `PRODUCTO_V1.csv` | ⛔ | ✅ |
| Verificación | ⛔ | ✅ todas OK |

---

## 1. PASO 0 — Aclaración incorporada a `CLAUDE.md`

Se agregó, textual, en la sección "Reglas de elegibilidad dura":

> *Los límites de edad (18 mínimo, 65-69 máximo según el producto) no son una decisión de Colsubsidio ni de este equipo — son políticas internas de suscripción de riesgo de la aseguradora (Chubb). […] el desajuste no se resuelve rediseñando el bucket, se resuelve preguntando la edad exacta solo cuando hace falta.*

Copiada palabra por palabra, sin reformular, porque el punto es dejar clara la **responsabilidad** del desajuste: los buckets de `RANGO_EDAD` son de Colsubsidio, los límites de edad son de la aseguradora, y no tienen por qué calzar.

---

## 2. PASO 0.5 — Estructuración de las hipótesis

**Por qué este paso existe:** el `.md` es prosa para lectura humana. Parsear texto libre en tiempo de ejecución sería frágil y no auditable. La traducción se hace una vez, queda en CSV, y cada fila conserva el texto original de la celda para poder verificar después que la estructuración no cambió el sentido.

### 2.1 Criterio de estructuración (estricto, a propósito)

Una hipótesis se estructura **solo si su condición es determinable sin inventar nada**. Se marca "no estructurable" cuando:

| Código | Motivo |
|---|---|
| **(a)** | Usa un término cuantitativo **sin umbral definido** ("salario alto", "bajo-medio", "medio-alto"). Fijar el umbral sería una **decisión de negocio nueva**, no una traducción. |
| **(b)** | Depende de **interpretar un código anonimizado** (`SEGMENTO_GRUPO_FAMILIAR`, `EMPRESA_FOCO`), cuyo significado el negocio no divulga. |
| **(c)** | La **precedencia lógica** del texto es ambigua (mezcla `O` e `Y` sin paréntesis). |

Las no estructurables **no se forzaron a ningún formato** y **no están en el CSV**.

### 2.2 Resultado: 9 filas estructuradas

| Categoría | Elegibilidad dura | Propensión | Total |
|---|---:|---:|---:|
| Personal y Familiar | 4 | 3 | 7 |
| Crédito | 0 | 1 | 1 |
| Movilidad | 0 | 1 | 1 |
| Hogar | 0 | 0 | **0** |
| Mascotas | 0 | 0 | **0** |
| **TOTAL** | **4** | **5** | **9** |

**Las 5 reglas de propensión estructuradas:**

| Producto | Columna | Condición |
|---|---|---|
| `DEUDOR-VIDA-01` | `RANGO_SALARIAL_LIMPIO` | los 10 buckets > 1.5 SMLV *(umbral explícito en el texto)* |
| `SALUD-01` | `DROGUERIA` | `SI` |
| `APEXEQ-PAL-01` | `RANGO_SALARIAL_LIMPIO` | `Menor al SMLV`, `Entre 1 y 1.5 SMLV` *(rango acotado en el texto)* |
| `EXEQ-01` | `RANGO_EDAD` | `Mayor de 55 años` |
| `BICI-01` | `RANGO_EDAD` | `20 a 35 años` |

**Las 4 de elegibilidad dura:** `AP-CHUBB-01` y `APDIG-CHUBB-01` (18 a 65+364), `ONCO-CHUBB-01` (18 a 64+364), `URB-CHUBB-01` (condición de compra — sin columna del dataset que la evalúe, `columna_dataset` vacía).

### 2.3 🔴 AVISO 1 — 10 hipótesis no estructurables automáticamente

| Producto | Categoría | Motivo | Qué falta para desbloquearla |
|---|---|---|---|
| `DESEMP-01` | Crédito | (b) | Qué valor de `EMPRESA_FOCO` significa "relación laboral formal" |
| `INCENDIO-DEUDOR-01` | Crédito | (a) | Desde qué bucket empieza "alto" |
| `ASMED-01` | Personal y Familiar | (b) | Qué códigos de `SEGMENTO_GRUPO_FAMILIAR` son "núcleo con dependientes" |
| `VIDAAH-01` | Personal y Familiar | (a) | El corte de "medio-alto" *(la parte de edad 36-55 sí es clara)* |
| `ASMULT-01` | Personal y Familiar | (a) | El corte de "bajo-medio" |
| `VIDA-01` | Personal y Familiar | (b) | Qué códigos son "hogar con dependientes" |
| `HOGAR-01` | Hogar | (a) + (c) | Paréntesis explícitos **y** el corte de "medio-alto" |
| `ARRENDA-01` | Hogar | (a) | El corte de "bajo-medio" |
| `MOTO-01` | Movilidad | (a) | El corte de "bajo-medio" — **la más cerca de quedar lista**, su lista de municipios ya es explícita |
| `CARRO-01` | Movilidad | (a) | El corte de "medio-alto" |

**Lo que esto significa para el bloque:** **Hogar y Mascotas se quedan con cero reglas de propensión estructuradas.** Hogar tiene 2 productos y ambos cayeron en (a). Sin esto, el emparejamiento en esas categorías no podría hacer otra cosa que asignar el producto por defecto a todo el mundo.

**Observación:** 6 de los 10 bloqueos son la misma pregunta repetida — *dónde corta "bajo-medio" / "medio-alto" / "alto"*. Definir una sola escala de tramos salariales desbloquearía `INCENDIO-DEUDOR-01`, `VIDAAH-01`, `ASMULT-01`, `ARRENDA-01`, `MOTO-01` y `CARRO-01` de una vez. Es una decisión de negocio, no la tomé.

### 2.4 🔴 AVISO 2 — 5 productos sin hipótesis documentada

El `.md` dice **explícitamente** que no tienen columna candidata. No se inventó ninguna regla:

| Producto | Categoría | Lo que dice el `.md` |
|---|---|---|
| `VIAJE-01` | Personal y Familiar | "Sin columna candidata real. Depende 100 % de lo que capture el bot" |
| `SOAT-01` | Movilidad | "No es propensión, es obligación legal […] no se puede anticipar desde el dataset" |
| `PET-SEG-01` | Mascotas | "Ninguna columna candidata dentro de nuestra base" |
| `PET-PREP-01` | Mascotas | ídem |
| `PET-ASIS-01` | Mascotas | ídem |

Estos son los que el PASO 3 del pedido manda marcar `producto_indiferenciado = true`.

### 2.5 🔴 AVISO 3 — El número de productos no cuadra entre las tres fuentes

| Fuente | Productos |
|---|---:|
| El pedido de este bloque | **30** |
| `Hipotesis_Generales_Seguros.md`, línea 4 | **27** |
| Productos con `producto_id` nombrados en las tablas del `.md` | **24** |

Los 24 son: 9 estructurados + 10 no estructurables + 5 sin hipótesis. **Faltan entre 3 y 6 productos** que existen en la Base Maestra pero no aparecen nombrados en el `.md` de hipótesis. No se inventaron.

---

## 3. 🔴 PASO 0.75 — BLOQUEO: no existe el catálogo de productos

**Buscado en todo el repo** (`find` por `*producto*`, `*catalogo*`, `*maestra*`, `*victor*`, `*.csv`, `*.json`): **no existe ningún archivo estructurado con las fichas de los productos** — el que tendría `producto_id`, `categoria`, `elegibilidad`, `perfil_objetivo` para los 27/30 productos de la Base Maestra.

Lo único disponible es `Hipotesis_Generales_Seguros.md`, que **no es el catálogo**: es el documento de hipótesis. Menciona 24 productos de pasada, sin ficha completa, y su propia línea 4 dice que las fichas están en "la Base Maestra de Victor", que no está en este repo.

**Por qué esto bloquea la lógica principal y no se continuó igual:**

| Paso de la lógica | Qué necesita del catálogo |
|---|---|
| **Paso 2** — "0 productos cumplen → producto_top = el producto **más general/menos restrictivo** de la categoría" | Para saber cuál es el más general hace falta el `perfil_objetivo` de **todos** los productos de esa categoría. Con 24 de 30 podría elegir como "más general" un producto que no lo es, simplemente porque el verdadero no está en mi lista. |
| **Paso 3** — "productos sin hipótesis documentada" | La lista solo es correcta si se conoce el universo completo. Hoy no puedo distinguir "sin hipótesis" de "no está en el `.md`". |
| **Verificación** — "lista completa de productos que nunca aparecieron como `producto_top`" | Es imposible de producir sin el universo completo: daría la lista de los que faltan **de los 24**, no de los 30. |

Inventar las fichas faltantes contradiría la instrucción explícita del pedido (*"no inventes ni completes fichas de producto desde cero, deben salir de la Base Maestra real"*) y produciría recomendaciones de producto que no se pueden justificar contra ninguna fuente — exactamente lo que prohíbe el requisito de explicabilidad del reto.

### Qué hace falta para desbloquear

1. **El catálogo de la Base Maestra en formato estructurado** (CSV/JSON) con `producto_id`, `categoria`, `elegibilidad`, `perfil_objetivo` para los 27/30 productos. Es el bloqueo duro.
2. *(Opcional, mejora mucho el resultado)* La escala de tramos salariales de § 2.3, que desbloquea 6 de las 10 hipótesis y le da reglas a Hogar y Movilidad.

Con (1) sola, la lógica corre completa. Con (1) + (2), corre y además discrimina de verdad en 4 de las 5 categorías.

---

## 4. Decisiones propias del agente

| # | Decisión | Por qué |
|---|---|---|
| **D1** | **Criterio estricto de estructurabilidad** (§ 2.1): "bajo-medio" y similares se declaran no estructurables en vez de mapearlos a los tramos que el proyecto ya usa | El proyecto tiene definiciones operativas de "salario alto/bajo" de bloques anteriores. Reutilizarlas acá habría producido un CSV con 15 reglas en vez de 9 — pero serían **mis** umbrales presentados como si vinieran de la Base Maestra. El pedido decía no forzar. |
| **D2** | **Detenerme en el PASO 0.75** en vez de continuar con los 24 productos conocidos | El pedido dice "AVISA antes de continuar". Además el resultado sería silenciosamente incompleto: la verificación pedida no es producible sin el universo completo. |
| **D3** | **El CSV estructurado se genera con un script**, no a mano | Reproducible y auditable: el criterio de inclusión/exclusión queda en el código, no en una decisión invisible. Volver a correrlo con más hipótesis desbloqueadas es agregar una entrada a una lista. |

**No se movió el pendiente #6 de `CLAUDE.md` a "decisiones tomadas"** aunque el pedido lo indicaba: el bloque no se completó, y marcarlo como cerrado dejaría el documento de contexto diciendo algo falso. Queda anotado como avance parcial con su bloqueo.

---

## 5. Qué falta / qué verificar en la próxima sesión

**Qué se hizo:** aclaración de elegibilidad en `CLAUDE.md`; 9 hipótesis estructuradas a CSV con criterio auditable; 10 no estructurables y 5 sin hipótesis reportadas con motivo y con qué falta para cada una; discrepancia 30/27/24 detectada.

**Qué falta:** el catálogo de la Base Maestra (bloqueo duro) y, opcionalmente, la escala de tramos salariales.

**Qué verificar cuando llegue el catálogo:**

- Que los 24 `producto_id` del `.md` existan tal cual en el catálogo — si alguno no coincide, hay un problema de nomenclatura antes de emparejar nada.
- Cuáles son los 3-6 productos que el `.md` no menciona, y si alguno pertenece a Hogar o Mascotas (las dos categorías que hoy quedan sin reglas).
- Que `texto_original` de cada fila del CSV siga correspondiendo a su celda en el `.md`, por si el `.md` cambió.

---

## 6. Desviación respecto al plan

**Desviación: se ejecutaron 2 de los 5 bloques del pedido.** Los pasos 0 y 0.5 están completos. Los pasos 1-3, la salida `PRODUCTO_V1.csv` y su verificación **no se ejecutaron**, por el bloqueo del paso 0.75 — que el propio pedido definió como punto de parada ("AVISA antes de continuar").

**Lo que sí cambió respecto a lo planeado:** no se movió el pendiente #6 a "decisiones tomadas" (§ 4). El pedido lo condicionaba a "si todo sale bien", y no salió todo.

**Señal de alerta de dos fallos seguidos:** no se activó. No hubo fallos de ejecución; hubo un insumo faltante, detectado en el paso que el pedido puso justamente para detectarlo.

---

---
---

# 7. SEGUNDO INTENTO — bloque completo

**2026-07-24** · Todo lo anterior (§ 1-6) es el registro del intento bloqueado y **no fue modificado**.

## 7.1 Qué desbloqueó el bloque

| Insumo nuevo | Qué resolvió |
|---|---|
| `catalogo_productos.csv` | 24 productos reales con `categoria` ya mapeada a las 5 oficiales, más aseguradora/precio/exclusiones con semáforo de confianza. Resuelve el bloqueo del § 3. |
| `Hipotesis_Generales_Seguros.md` actualizado | Las 10 hipótesis que reporté como no estructurables, resueltas y marcadas "Resuelto (24 jul)". |
| **Escala única de `RANGO_SALARIAL_LIMPIO`** | Cierra los 6 bloqueos de tipo (a) de un solo golpe — era exactamente lo que había señalado en § 2.3. |
| **Producto general de respaldo por categoría** | Elimina la decisión que yo habría tenido que tomar ("cuál es el más general"). |

**La cifra de productos quedó zanjada: son 24**, no 27 ni 30. Verificado: los 24 `producto_id` del catálogo coinciden **exactamente** con los 24 de las hipótesis — cero faltantes, cero sobrantes.

## 7.2 Escala única aplicada

| Tier | Buckets |
|---|---|
| Bajo | Menor al SMLV · Entre 1 y 1.5 · Entre 1.5 y 2 |
| Medio | Entre 2 y 2.5 · Entre 2.5 y 3 · Entre 3 y 4 |
| Medio-alto | Entre 4 y 6 · Entre 6 y 8 |
| Alto | Entre 8 y 10 · Entre 10 y 20 · Entre 20 y 30 · Mayor a 30 |

---

## 8. PASO 0.5 rehecho — 21 filas

### 8.1 Cambio de formato: una fila por condición atómica

Las hipótesis nuevas traen **reglas compuestas** (`HOGAR-01` mezcla `Y` con `O`), así que una fila por producto ya no alcanzaba. El CSV pasó a **forma normal disyuntiva**, con un campo nuevo `grupo_and`:

- Filas del mismo producto con el mismo `grupo_and` → se combinan con **Y**.
- Distintos `grupo_and` del mismo producto → se combinan con **O**.

Ejemplo, `HOGAR-01`: grupo 1 = (salario Medio-alto/Alto **Y** ciudad conocida); grupo 2 = (`VIVIENDA=SI`). Aplica si se cumple el grupo 1 **O** el grupo 2 — la precedencia que el `.md` fijó explícitamente.

Sintaxis de `condicion`: `"valor_a|valor_b"` = pertenencia; `"NO_NULO"` = regla de presencia.

### 8.2 Cobertura de los 24 productos

| | Productos |
|---|---:|
| Con hipótesis de propensión | **13** |
| Solo con elegibilidad dura *(no compiten en el ranking)* | 4 |
| Sin ninguna hipótesis | 7 |
| **TOTAL** | **24** |

**Filas por categoría:** Personal y Familiar 11 · Hogar 4 · Movilidad 4 · Crédito 2 · Mascotas 0.

**Orden de desempate** (el orden del archivo, que el PASO 2 usa): `DEUDOR-VIDA-01`, `INCENDIO-DEUDOR-01`, `SALUD-01`, `ASMED-01`, `VIDAAH-01`, `ASMULT-01`, `APEXEQ-PAL-01`, `EXEQ-01`, `HOGAR-01`, `ARRENDA-01`, `MOTO-01`, `CARRO-01`, `BICI-01`.

### 8.3 Los 7 productos sin hipótesis

`DESEMP-01` *(descartado por no verificable)*, `VIDA-01` *(respaldo de PyF)*, `VIAJE-01`, `SOAT-01`, `PET-SEG-01` *(respaldo de Mascotas)*, `PET-PREP-01`, `PET-ASIS-01`. No se les inventó regla.

### 8.4 ⚠️ Punto a confirmar — `APEXEQ-PAL-01`

Su texto **no** fue actualizado el 24 jul y dice: *"bajo (Menor al SMLV a 1.5 SMLV)"*. El paréntesis acota **2 buckets**, pero la palabra "bajo" según la escala única son **3** (incluye `Entre 1.5 y 2 SMLV`).

**Se aplicó la escala única**, por la instrucción explícita de no interpretar cada hipótesis por separado. **Diferencia: 41.805 filas** de la base entran o no según cuál se use. Si la intención era respetar el paréntesis, es quitar un elemento de una lista.

---

## 9. Lógica de emparejamiento aplicada

**PASO 0 — sin señal:** `categoria_top = "Sin señal suficiente"` → `producto_top` nulo, nada que emparejar.

**PASO 1 — elegibilidad dura:** los 3 productos con edad verificada (`AP-CHUBB-01`, `APDIG-CHUBB-01`, `ONCO-CHUBB-01`) son **todos de Personal y Familiar**. Si `RANGO_EDAD` cae en un bucket más ancho que la regla real (`Menor de 19 años` o `Mayor de 55 años`) → `pendiente_confirmacion_edad = true`. `URB-CHUBB-01` no tiene regla de edad, no entra.

**PASO 2 — ranking dentro de la categoría ganadora:**

| Cuántos cumplen | `producto_top` | `productos_alternativos` | `producto_indiferenciado` |
|---|---|---|---|
| 0 | producto de respaldo de la categoría | vacío | **true** *(asignado sin evidencia)* |
| 1 | ese producto | vacío | false |
| 2+ | el primero según el orden del archivo | todos los que cumplen | **true** |

**PASO 3 — sin hipótesis documentada:** no se les inventa regla; solo llegan a `producto_top` vía respaldo, y ahí ya quedan marcados por el caso "0 cumplen".

---

## 10. Verificación

| Chequeo | Resultado |
|---|---|
| Filas de entrada = filas de salida | **500.000 = 500.000** ✅ |
| `producto_top` nulo = filas "Sin señal suficiente" | **3.534 = 3.534** ✅ |
| `pendiente_confirmacion_edad`: todas en `Menor de 19` / `Mayor de 55` | ✅ |
| Columnas de V3 sobrescritas | **ninguna** — 25 → 29 ✅ |

### 10.1 `pendiente_confirmacion_edad` — 3.062 filas (0,612 %)

`Mayor de 55 años` 3.052 · `Menor de 19 años` 10. Todas caen en los dos buckets ambiguos, como pedía la verificación.

*(En toda la base hay 56.818 filas con edad ambigua; se marcan solo las 3.062 de Personal y Familiar — ver decisión D3.)*

### 10.2 `producto_indiferenciado` — 373.777 filas (74,76 %)

| Categoría | Indiferenciado | Total | % | Por empate (2+) | Por respaldo (0) |
|---|---:|---:|---:|---:|---:|
| Crédito | 334.947 | 405.366 | 82,63 % | 0 | 334.947 |
| Personal y Familiar | 30.237 | 41.441 | 72,96 % | 26.908 | 3.329 |
| Hogar | 6.977 | 45.716 | 15,26 % | 1 | 6.976 |
| Movilidad | 1.616 | 3.943 | 40,98 % | 1.616 | 0 |
| Sin señal suficiente | 0 | 3.534 | 0 % | — | — |
| **TOTAL** | **373.777** | **500.000** | **74,76 %** | **28.525** | **345.252** |

### 10.3 Distribución de `producto_top` — solo 9 de 24 productos

| Producto | Filas | % |
|---|---:|---:|
| DEUDOR-VIDA-01 | 405.366 | 81,073 % |
| HOGAR-01 | 29.849 | 5,970 % |
| SALUD-01 | 25.561 | 5,112 % |
| ARRENDA-01 | 15.867 | 3,173 % |
| ASMULT-01 | 7.668 | 1,534 % |
| MOTO-01 | 3.943 | 0,789 % |
| *(nulo — sin señal)* | 3.534 | 0,707 % |
| VIDAAH-01 | 3.514 | 0,703 % |
| VIDA-01 | 3.329 | 0,666 % |
| EXEQ-01 | 1.369 | 0,274 % |

### 10.4 Lista completa: 15 productos que nunca fueron `producto_top`

| Producto | Categoría | Por qué |
|---|---|---|
| `AP-CHUBB-01` | Personal y Familiar | solo elegibilidad dura, sin hipótesis → no compite |
| `APDIG-CHUBB-01` | Personal y Familiar | ídem |
| `ONCO-CHUBB-01` | Personal y Familiar | ídem |
| `URB-CHUBB-01` | Personal y Familiar | ídem |
| `INCENDIO-DEUDOR-01` | Crédito | **inalcanzable por construcción** — ver H3 |
| `CARRO-01` | Movilidad | **inalcanzable por construcción** — ver H3 |
| `APEXEQ-PAL-01` | Personal y Familiar | **dominado** por `ASMULT-01` — ver H4 |
| `ASMED-01` | Personal y Familiar | **empata siempre** con `SALUD-01`, que va antes — ver H5 |
| `BICI-01` | Movilidad | cumple, pero `MOTO-01` va antes en el orden |
| `DESEMP-01` | Crédito | sin hipótesis documentada |
| `VIAJE-01` | Personal y Familiar | ídem |
| `SOAT-01` | Movilidad | ídem |
| `PET-SEG-01` | Mascotas | ídem *(y Mascotas nunca es `categoria_top`)* |
| `PET-PREP-01` | Mascotas | ídem |
| `PET-ASIS-01` | Mascotas | ídem |

**5 de esos 15 sí aparecen en `productos_alternativos`:** `ASMED-01`, `APEXEQ-PAL-01`, `BICI-01`, `ARRENDA-01`, `HOGAR-01`. Los 10 restantes no aparecen en ninguna parte de la salida.

---

## 11. Hallazgos

### H1 — 3 de cada 4 personas reciben un producto sin evidencia específica

**373.777 filas (74,76 %)** tienen `producto_indiferenciado = true`, y **345.252 de ellas (92 %) es por respaldo**, no por empate: ningún producto de su categoría cumplió su hipótesis y se les asignó el genérico. El emparejamiento producto-a-producto **discrimina mucho menos que el de categoría**.

### H2 — Crédito: el producto de respaldo cubre el 82,63 % de la categoría

`DEUDOR-VIDA-01` requiere **> 1.5 SMLV**, pero el pico de la categoría Crédito es justo `Entre 1 y 1.5 SMLV` (**302.613 filas**), que queda por debajo del umbral. El propio `.md` lo anticipó al designarlo producto de respaldo — pero el efecto en volumen es que **405.366 personas reciben `DEUDOR-VIDA-01`, y 334.947 de ellas sin cumplir su hipótesis**.

### H3 — 🔴 Dos productos son inalcanzables por construcción

Su hipótesis apunta a un rango salarial que **es incompatible con que su categoría gane el ranking**:

| Producto | Su condición | Filas de su categoría que la cumplen |
|---|---|---:|
| `INCENDIO-DEUDOR-01` | salario tier **Alto** | **0** de 405.366 filas de Crédito |
| `CARRO-01` | salario **Medio-alto o Alto** | **0** de 3.943 filas de Movilidad |

**Por qué:** con la escala graduada de Crédito (iteración 5), el salario alto da `score_credito` de 0.02–0.10 — nunca gana su categoría. Y una persona de salario Medio-alto con ciudad conocida obtiene `score_hogar = 1.00`, así que Hogar le gana a Movilidad. Verificado: las **14.546 personas de salario tier Alto** de toda la base terminan en Hogar (9.088) o Personal y Familiar (5.458). **Ninguna en Crédito ni Movilidad.**

Es el mismo patrón que ya apareció con Mascotas en la iteración 5: **las hipótesis de producto se definieron sobre las mismas variables que deciden la categoría**, así que dentro de la categoría ganadora el rango de esas variables ya viene restringido. Un producto cuya hipótesis apunta a la parte del rango que no puede ganar la categoría no es alcanzable nunca.

### H4 — `APEXEQ-PAL-01` está dominado por `ASMULT-01`

`ASMULT-01` cubre **Bajo + Medio**; `APEXEQ-PAL-01` cubre **solo Bajo** — un subconjunto estricto. Y `ASMULT-01` va **antes** en el orden de desempate. Resultado: cada vez que `APEXEQ-PAL-01` aplica, `ASMULT-01` también aplica y gana. Solo aparece en `productos_alternativos`.

### H5 — `ASMED-01` nunca es top, pero eso era intencional

Comparte condición exacta con `SALUD-01` (`DROGUERIA = SI`) por decisión de negocio explícita. `SALUD-01` va primero, así que gana siempre. `ASMED-01` sí aparece en `productos_alternativos` **28.525 veces** — la combinación más frecuente de toda la salida es `SALUD-01, ASMED-01, ASMULT-01` (13.126 filas). Funciona como se diseñó.

### H6 — 🔴 `pendiente_confirmacion_edad` hoy no protege nada

Se marcan 3.062 filas, pero los 3 productos con regla de edad **nunca son `producto_top`** (no tienen hipótesis de propensión, así que no compiten). Los productos que esas 3.062 filas efectivamente reciben son `EXEQ-01` (1.369), `ASMULT-01` (1.347) y `SALUD-01` (346) — **ninguno tiene regla de edad**.

La marca es correcta y está bien calculada, pero **hoy no evita ninguna recomendación inválida**. Solo empezará a servir si los productos CHUBB entran al ranking, lo que requiere darles hipótesis de propensión.

### H7 — Los 4 productos CHUBB no participan del motor

Tienen elegibilidad dura verificada (el dato más sólido del catálogo) pero **ninguna hipótesis de propensión**, así que no compiten. Son 4 de los 24 productos, todos de Personal y Familiar, y **ninguno puede recomendarse hoy**.

---

## 12. Decisiones propias del agente

| # | Decisión | Por qué | Reversible |
|---|---|---|---|
| **D1** | **Campo `grupo_and`** añadido al CSV, formato en forma normal disyuntiva | Los campos pedidos (`columna_dataset`, `condicion`) no pueden expresar `HOGAR-01`, que mezcla `Y` con `O`. Sin esto habría que aplanar la regla y perder la precedencia que el `.md` fijó explícitamente | — |
| **D2** | **`APEXEQ-PAL-01` usa la escala única (3 buckets)** y no el paréntesis literal (2) | Instrucción explícita de no interpretar cada hipótesis por separado. **Reportado en § 8.4** porque el texto literal dice otra cosa | Sí, 1 elemento |
| **D3** | **`pendiente_confirmacion_edad` solo en Personal y Familiar** | Los 3 productos con regla de edad son todos de esa categoría. Marcar a alguien de Crédito por un producto que nunca se le va a ofrecer sería ruido. Sin el filtro serían 56.818 filas en vez de 3.062 | Sí, 1 condición |
| **D4** | **`productos_alternativos` incluye también al `producto_top`** | El pedido dice "todos van a productos_alternativos". Se leyó literal: la lista es el conjunto completo de candidatos empatados, y `producto_top` señala cuál se eligió | Sí |
| **D5** | **Normalización de acentos** al cruzar nombres de categoría | Ver § 13 — sin esto el bloque produce un resultado silenciosamente incompleto | — |

---

## 13. Error propio durante la implementación

En la primera corrida, **408.900 filas quedaron sin `producto_top`** — exactamente el total de la categoría Crédito.

**Causa raíz:** desalineación de nombres entre artefactos del propio proyecto. El etiquetado (iteración 4) escribió la categoría como **`"Credito"` sin tilde**, mientras que `catalogo_productos.csv` y las hipótesis usan **`"Crédito"` con tilde**. La comparación `df["categoria_top"] == categoria` fallaba para toda la categoría, en silencio.

**Cómo se detectó:** el chequeo "`producto_top` nulo debe coincidir con las filas sin señal" dio `3.534` vs `408.900` e hizo fallar el veredicto. Es exactamente el chequeo que en la iteración 6 había quedado desconectado del resultado y arreglé entonces — esta vez sí frenó la corrida.

**Corrección:** función `norm()` que quita acentos y compara en minúsculas, aplicada a ambos lados del cruce.

**Lección:** dos artefactos del mismo proyecto que se refieren a la misma entidad con strings distintos es un fallo esperable en cuanto hay más de un script. Los cruces por nombre de categoría deben normalizarse siempre, no solo cuando se sabe que hay diferencia.

---

## 14. Qué falta / qué verificar en la próxima sesión

**Qué se hizo:** 500.000 filas emparejadas con producto específico del catálogo real de 24. Verificado: sin filas perdidas, nulos solo donde corresponde, ninguna columna de V3 sobrescrita.

**Qué falta — todo requiere decisión de negocio, no técnica:**

1. **H3 — los dos productos inalcanzables.** `INCENDIO-DEUDOR-01` y `CARRO-01` no pueden recomendarse nunca con las reglas actuales. O se les cambia la hipótesis, o se acepta explícitamente como se hizo con Mascotas.
2. **H7 — los 4 CHUBB sin hipótesis de propensión.** Tienen el dato de elegibilidad más sólido del catálogo y no se recomiendan nunca. Darles hipótesis los pondría en juego y de paso haría útil `pendiente_confirmacion_edad` (H6).
3. **H2 — el umbral de `DEUDOR-VIDA-01`.** Con > 1.5 SMLV, el 82,63 % de Crédito recibe el producto sin cumplirlo. Bajar el umbral a "cualquier titular" lo haría honesto, o se acepta el respaldo como está.
4. **H4 — `APEXEQ-PAL-01` dominado.** Si se quiere que sea alcanzable, hay que diferenciarlo de `ASMULT-01` (precio, no solo salario) o subirlo en el orden.
5. **§ 8.4 — confirmar `APEXEQ-PAL-01`:** escala única (3 buckets) vs. paréntesis literal (2). Diferencia de 41.805 filas.

**Qué verificar antes de seguir:**

- Que el motor lea **`Usos_Productos_Afiliados_PRODUCTO_V1.csv`**, no V3 ni los anteriores.
- Que el bot no muestre `producto_top` sin mirar `producto_indiferenciado`: en el 74,76 % de los casos el producto es un genérico, no una recomendación específica.
- Que las 3.534 filas con `producto_top` nulo se traten como "no hay recomendación", no como error.

---

## 15. Desviación respecto al plan

**Desviación: ninguna.** Se retomó desde el PASO 0.5 como se pidió, se re-ejecutó completo (9 → 21 filas), y los pasos 0.75 a 3 corrieron con la lógica original sin cambios. Los dos casos especiales se implementaron como se indicó: `ASMED-01`/`SALUD-01` empatan y van ambos a alternativos con `producto_indiferenciado = true`; `DESEMP-01` quedó sin hipótesis, tratado igual que `VIAJE-01` y `SOAT-01`.

**Lo que no estaba previsto:** el campo `grupo_and` (D1), necesario porque las hipótesis nuevas traen reglas compuestas que el formato plano no podía expresar.

**Señal de alerta de dos fallos seguidos:** no se activó. Hubo **un** fallo (§ 13), con causa raíz identificada y corregida en la primera vuelta.

---

---
---

# 16. TERCERA RONDA (V2) — declaración directa y corrección de `APEXEQ-PAL-01`

**2026-07-24** · Todo lo anterior (§ 1-15) no fue modificado.

| | |
|---|---|
| Entrada | `../Usos_Productos_Afiliados_PRODUCTO_V1.csv` — no se modificó |
| Salida | **`../Usos_Productos_Afiliados_PRODUCTO_V2.csv`** — 500.000 × 29 col. ✅ **vigente** |
| `hipotesis_producto_estructuradas.csv` | 21 → **24 filas**, campo `flujo` nuevo |

## 16.1 ⚠️ Los documentos citados como fuente no estaban en el repo

El pedido indicaba confirmar como fuente `Hipotesis_Generales_Seguros.md` (actualizado) e `Integracion_con_Nicolas.md`. **Se verificó y ninguno de los dos estaba disponible:**

| Documento | Estado verificado |
|---|---|
| `Integracion_con_Nicolas.md` | **No existe.** Búsqueda por nombre y por `*nicolas*` en todo el árbol: sin resultados. |
| `Hipotesis_Generales_Seguros.md` | **Sin actualizar.** Mismo timestamp y tamaño que la ronda anterior (18:27, 21.509 bytes), 0 menciones de "declaración directa", y su línea 35 sigue declarando `CARRO-01` como respaldo de Movilidad. |

**Cómo se procedió:** las tres decisiones y la respuesta sobre `APEXEQ-PAL-01` venían **completamente especificadas en el pedido**, así que no hacía falta leer los documentos para ejecutarlas. **La fuente autoritativa de esta ronda es el mensaje del pedido**, no los `.md`. Queda anotado para que, si los documentos aparecen después y dicen algo distinto, se sepa contra qué se implementó.

**Lo que sí queda fuera:** si `Integracion_con_Nicolas.md` define campos del contrato con Nicolás, nada de eso está incorporado — no se vio.

## 16.2 Los tres cambios aplicados

**DECISIÓN 1 — `INCENDIO-DEUDOR-01` y `CARRO-01` salen del motor de propensión.** No por un error de implementación: su hipótesis original estaba mal diseñada desde antes (§ 11, H3). Pasan al grupo nuevo **"declaración directa"**, que no pasa por el ranking en absoluto: no compiten por `producto_top`, no aparecen en `productos_alternativos`, y **no cuentan como `producto_indiferenciado`**.

**DECISIÓN 2 — Los 4 productos CHUBB se unen al mismo grupo**, junto a `DESEMP-01`, `VIAJE-01` y `SOAT-01`. Su `pendiente_confirmacion_edad` **se sigue calculando igual** — no se tocó.

**DECISIÓN 3 — Movilidad cambia de producto de respaldo:** `CARRO-01` → **`BICI-01`**, provisional.

**El grupo de declaración directa queda con 9 productos:** `INCENDIO-DEUDOR-01`, `CARRO-01`, `AP-CHUBB-01`, `APDIG-CHUBB-01`, `ONCO-CHUBB-01`, `URB-CHUBB-01`, `DESEMP-01`, `VIAJE-01`, `SOAT-01`.

**Reparto de los 24 productos del catálogo:**

| Grupo | Productos |
|---|---:|
| Compiten en el ranking, con hipótesis | 11 |
| Compiten, sin hipótesis (solo llegan por respaldo) | 4 |
| **Declaración directa** (fuera del ranking) | **9** |
| **TOTAL** | **24** |

Verificado: **cero solapamiento** entre ranking y declaración directa.

## 16.3 Respuesta aplicada — `APEXEQ-PAL-01`

Respeta su paréntesis original: **`Menor al SMLV` + `Entre 1 y 1.5 SMLV` = 2 buckets.** No se expande a los 3 del tier Bajo.

**Regla general fijada, que aplica de aquí en adelante:** *la escala única solo aplica a términos que no traían ya su propio alcance explícito por escrito.* Queda como comentario en `estructurar_hipotesis.py` para que no se vuelva a decidir cada vez.

## 16.4 Cambio de formato: campo `flujo`

El CSV estructurado suma un campo `flujo` con dos valores: `ranking_propension` y `declaracion_directa`. Fue necesario porque los 4 CHUBB **conservan** su fila de `elegibilidad_dura` (el motor la usa para `pendiente_confirmacion_edad`) pero **no** deben competir — sin un campo aparte, "tiene fila en el CSV" y "compite en el ranking" serían lo mismo, y no lo son.

El motor filtra por `tipo_regla == "propension"` **y además** tiene un guard explícito contra la lista de declaración directa. Redundante a propósito: son dos condiciones independientes que tendrían que fallar a la vez para que un producto excluido se cuele.

## 16.5 Verificación

| Chequeo | Resultado |
|---|---|
| Filas de entrada = filas de salida | **500.000 = 500.000** ✅ |
| Los 9 productos de declaración directa NO aparecen en `producto_top` | ✅ los 9 |
| Los 9 NO aparecen en `productos_alternativos` | ✅ los 9 |
| `producto_top` nulo = filas sin señal | 3.534 = 3.534 ✅ |
| `pendiente_confirmacion_edad` sin tocar | **3.062**, idéntico a V1 ✅ |

### 🔴 16.6 Resultado central: **ninguna fila cambió de `producto_top`**

| Métrica | Filas |
|---|---:|
| Filas con `producto_top` distinto a V1 | **0** |
| Filas con `producto_indiferenciado` distinto | **0** |
| Filas con `productos_alternativos` distinto | **2.083** |

**Las decisiones 1, 2 y 3 no cambiaron ni una sola asignación de producto.** No es un fallo — es la confirmación empírica de lo que reportaba § 11:

- `INCENDIO-DEUDOR-01` y `CARRO-01` **ya eran inalcanzables** (0 filas de sus categorías cumplían su condición), así que sacarlos del ranking no libera nada.
- Los 4 CHUBB **ya no competían** (sin hipótesis de propensión).
- El respaldo nuevo de Movilidad, `BICI-01`, **nunca se usa**: en Movilidad el respaldo se activa en 0 filas, porque las 3.943 cumplen `MOTO-01`. El cambio `CARRO-01` → `BICI-01` no tiene hoy ningún efecto observable.

**Las decisiones formalizan el estado en la estructura, no lo modifican en los datos.** El valor real es que ahora esos 9 productos están declarados fuera del flujo de forma explícita y verificable, en vez de estar dentro y no ganar nunca por accidente aritmético.

**El único cambio material es `APEXEQ-PAL-01`:** 2.083 filas donde dejó de aparecer en `productos_alternativos`.

| Antes | Ahora | Filas |
|---|---|---:|
| `SALUD-01, ASMED-01, ASMULT-01, APEXEQ-PAL-01` | `SALUD-01, ASMED-01, ASMULT-01` | 2.013 |
| `SALUD-01, ASMED-01, ASMULT-01, APEXEQ-PAL-01, EXEQ-01` | `SALUD-01, ASMED-01, ASMULT-01, EXEQ-01` | 70 |

Son exactamente las filas de `Entre 1.5 y 2 SMLV` que la escala única incluía y el paréntesis literal no. `producto_indiferenciado` no cambió en ninguna: esas filas ya tenían 3+ candidatos, y quitar uno las deja con 3.

### 16.7 Distribución de `producto_top` — sin cambios respecto a V1

| Categoría | V1 → V2 |
|---|---|
| Crédito (405.366) | `DEUDOR-VIDA-01` 405.366 → **405.366** |
| Movilidad (3.943) | `MOTO-01` 3.943 → **3.943** |
| Personal y Familiar (41.441) | `SALUD-01` 25.561 · `ASMULT-01` 7.668 · `VIDAAH-01` 3.514 · `VIDA-01` 3.329 · `EXEQ-01` 1.369 → **idénticos** |
| Hogar (45.716) | `HOGAR-01` 29.849 · `ARRENDA-01` 15.867 → **idénticos** |

Siguen siendo **9 de 24 productos** los que llegan a recomendarse. Los 15 restantes ahora se explican así: **9 por declaración directa** (decisión de negocio explícita), 3 de Mascotas (categoría que nunca es top), y 3 que compiten pero nunca ganan — `APEXEQ-PAL-01` (dominado por `ASMULT-01`), `ASMED-01` (empate intencional con `SALUD-01`) y `BICI-01` (`MOTO-01` va antes).

## 16.8 Decisiones propias del agente

| # | Decisión | Por qué |
|---|---|---|
| **D6** | **Campo `flujo` en el CSV estructurado** | Los 4 CHUBB necesitan conservar su fila de elegibilidad y a la vez quedar fuera del ranking; sin un campo aparte no se puede expresar |
| **D7** | **Guard doble en el motor** (filtro por `tipo_regla` + lista explícita de exclusión) | Que un producto excluido se cuele requiere que fallen dos condiciones independientes |
| **D8** | **`PET-PREP-01` y `PET-ASIS-01` NO se movieron** a declaración directa | El pedido nombró 6 productos y el grupo de `DESEMP-01`/`VIAJE-01`/`SOAT-01`; esos dos no estaban en ninguna lista. Siguen "sin hipótesis, dentro del flujo". Si debían moverse, es agregarlos a una lista |

## 16.9 Desviación respecto al plan

**Desviación: ninguna en la implementación.** Los tres cambios y la corrección de `APEXEQ-PAL-01` se aplicaron exactamente como se especificaron. `pendiente_confirmacion_edad` no se tocó, como se pidió: 3.062 filas, idéntico a V1.

**Lo que no se pudo hacer:** confirmar los dos documentos como fuente antes de tocar código (§ 16.1) — no estaban en el repo. Se procedió con el pedido como fuente y quedó anotado.

**Señal de alerta de dos fallos seguidos:** no se activó. Un error trivial de ejecución (un `KeyError` por un diccionario de conteo que no contemplaba el tipo de regla nuevo), corregido en el momento.

---

## Bitácora de actualizaciones

**#3 — 2026-07-24:** Tercera ronda (V2). Grupo nuevo **"declaración directa"** con 9 productos fuera del ranking de propensión: `INCENDIO-DEUDOR-01` y `CARRO-01` (hipótesis mal diseñada de origen), los 4 CHUBB, y `DESEMP-01`/`VIAJE-01`/`SOAT-01`. Respaldo de Movilidad `CARRO-01` → `BICI-01` (provisional). `APEXEQ-PAL-01` corregido a 2 buckets, con la regla general de que la escala única solo aplica a términos sin alcance explícito propio. Campo `flujo` nuevo en el CSV estructurado (21 → 24 filas). Salida: **`Usos_Productos_Afiliados_PRODUCTO_V2.csv`** — **el archivo vigente para el motor**. Verificado que los 9 productos no aparecen ni en `producto_top` ni en `productos_alternativos`. **Resultado central: 0 filas cambiaron de `producto_top`** — las tres decisiones formalizan en la estructura lo que los datos ya hacían, porque esos productos eran inalcanzables. Único cambio material: 2.083 filas donde `APEXEQ-PAL-01` deja de aparecer en alternativos. ⚠️ Los documentos citados como fuente (`Integracion_con_Nicolas.md`, `.md` de hipótesis actualizado) **no estaban en el repo**; se implementó con el pedido como fuente autoritativa (§ 16.1).

**#2 — 2026-07-24:** Bloque **completado**. Llegaron `catalogo_productos.csv` (24 productos — cifra zanjada, no 27 ni 30) y el `.md` actualizado con las 10 hipótesis resueltas, la escala única de salario y el producto de respaldo por categoría. PASO 0.5 rehecho: **9 → 21 filas**, formato cambiado a forma normal disyuntiva con campo `grupo_and` para soportar reglas compuestas. Pasos 1-3 ejecutados: **`Usos_Productos_Afiliados_PRODUCTO_V1.csv`**, 500.000 × 29 columnas — **el archivo vigente para el motor**. Verificación completa OK. Hallazgos: **H1** 74,76 % de filas con producto indiferenciado (92 % de ellas por respaldo), **H2** Crédito cubierto en 82,63 % por su producto de respaldo, **H3** `INCENDIO-DEUDOR-01` y `CARRO-01` **inalcanzables por construcción**, **H4** `APEXEQ-PAL-01` dominado por `ASMULT-01`, **H5** `ASMED-01` nunca top (intencional, sí aparece en alternativos 28.525 veces), **H6** `pendiente_confirmacion_edad` no protege nada hoy, **H7** los 4 CHUBB no participan. Solo **9 de 24 productos** llegan a recomendarse. Error propio corregido: desalineación `"Credito"`/`"Crédito"` entre artefactos dejaba 408.900 filas sin producto (§ 13).

**#1 — 2026-07-24:** Creación del documento. PASO 0 (aclaración de elegibilidad dura en `CLAUDE.md`, texto literal) y PASO 0.5 (estructuración de hipótesis → `hipotesis_producto_estructuradas.csv`, 9 filas: 4 de elegibilidad dura + 5 de propensión) completos. Tres avisos: 10 hipótesis no estructurables (6 de ellas por el mismo motivo — falta definir los tramos salariales), 5 productos sin hipótesis documentada, y discrepancia en el número de productos (pedido dice 30, `.md` dice 27, tablas nombran 24). **Bloqueado en PASO 0.75:** no existe el catálogo de la Base Maestra en formato estructurado; la lógica de emparejamiento (pasos 1-3) no se ejecutó y `PRODUCTO_V1.csv` no se generó. Hogar y Mascotas quedan hoy con cero reglas de propensión estructuradas.
