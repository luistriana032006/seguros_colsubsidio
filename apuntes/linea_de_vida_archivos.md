# Línea de vida de los archivos

Registro cronológico de **qué archivo se generó, cuándo, y si fue iterado después**.

**Qué NO va acá:** el *porqué* de cada cambio. Eso vive en el documento correspondiente
(ver columna "Dónde está el porqué"). Este archivo solo responde *qué pasó y en qué orden*.

**Cómo leerlo:** las iteraciones van numeradas y en orden. `CREADO` = nació ahí.
`ITERADO` = ya existía y se modificó. `MOVIDO` = cambió de ubicación. `ELIMINADO` = dejó de existir.

---

## Estado actual — qué existe hoy

| Archivo | Nació en | Última iteración | Estado |
|---|---|---|---|
| `reglas_documentacion_agent.md` | It. 0 | It. 0 | 📄 sin cambios |
| `Usos_Productos_Afiliados_SIN_ID.xlsx` | It. 0 | It. 0 | 🔒 fuente original, **nunca se modifica** |
| `apuntes/Cómo usar los recursos del Reto Seguros (1).docx` | It. 0 | It. 0 | 📄 sin cambios |
| `apuntes/nomenclatura_afiliados.md` | It. 0 | It. 0 | 📄 sin cambios |
| `artifacts/dataset_afiliados.html` | It. 0 | It. 0 | 📄 sin cambios |
| `apuntes/exploracion_dataset_nuevo.md` | It. 0 | **It. 2** | ♻️ iterado |
| `CLAUDE.MD` | It. 0 | **It. 14** | ♻️ iterado |
| `motor.py` | It. 9 | **It. 14** | 🔀 **reescrito — motor genérico, ya no sabe de Colsubsidio** |
| `app.py` | It. 9 | **It. 14** | 🔀 reescrito — selectores de dataset/hipótesis |
| `data/hipotesis/hipotesis_colsubsidio_ejemplo.json` | **It. 14** | It. 14 | ✅ caso de prueba (dominio viejo) |
| `data/datasets/clientes_socioeconomico.json` | **It. 14** | It. 14 | ✅ 500 filas sintéticas |
| `data/hipotesis/hipotesis_socioeconomico.json` | **It. 14** | It. 14 | ✅ caso de prueba |
| `data/hipotesis/hipotesis_prueba_c.json` | **It. 14** | It. 14 | ✅ caso de prueba (agnosticismo) |
| `scripts/generar_dataset_sintetico.py` | **It. 14** | It. 14 | ✅ vigente |
| `seguros.db` | **It. 14** | It. 14 | ✅ SQLite, 3 tablas |
| `RESUMEN_SESION.md` | **It. 14** | It. 14 | ✅ vigente |
| `apuntes/db.md` | **It. 7** | It. 7 | ✅ análisis de la base |
| `Hipotesis_Generales_Seguros.md` | **It. 8** | **It. 9** | 🔒 fuente externa (la itera el usuario) |
| `catalogo_productos.csv` | **It. 9** | It. 9 | 🔒 fuente externa — 24 productos |
| `estructurar_hipotesis.py` | **It. 8** | **It. 10** | ♻️ iterado |
| `hipotesis_producto_estructuradas.csv` | **It. 8** | **It. 10** | ♻️ iterado (24 filas) |
| `emparejar_producto.py` | **It. 9** | **It. 10** | ♻️ iterado |
| `apuntes/decisiones_producto_especifico.md` | **It. 8** | **It. 10** | ♻️ iterado (cubre las 3 rondas) |
| `Usos_Productos_Afiliados_ETIQUETADO_V3.csv` | It. 6 | It. 6 | 📦 evidencia del antes (superado) |
| `Usos_Productos_Afiliados_PRODUCTO_V1.csv` | **It. 9** | It. 9 | 📦 evidencia del antes (superado) |
| `Usos_Productos_Afiliados_PRODUCTO_V2.csv` | **It. 10** | It. 10 | ✅ **archivo de trabajo del motor** |
| `limpieza_rango_salarial.py` | **It. 1** | **It. 2** | ♻️ iterado |
| `Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv` | **It. 1** | It. 1 | ✅ vigente (insumo del etiquetado) |
| `apuntes/decisiones_limpieza_rango_salarial.md` | **It. 1** | **It. 2** | ♻️ iterado + movido |
| `apuntes/linea_de_vida_archivos.md` | **It. 3** | **It. 14** | ♻️ este archivo |
| `etiquetado_hipotesis.py` | **It. 4** | **It. 6** | ♻️ iterado (hoy produce la v3) |
| `Usos_Productos_Afiliados_ETIQUETADO.csv` | **It. 4** | It. 4 | 📦 evidencia del antes (v1, superado) |
| `apuntes/decisiones_etiquetado_hipotesis.md` | **It. 4** | **It. 6** | ♻️ iterado (cubre v1, v2 y v3) |
| `Usos_Productos_Afiliados_ETIQUETADO_V2.csv` | **It. 5** | It. 5 | 📦 evidencia del antes (v2, superado) |

---

## Iteración 0 — antes de la primera sesión de código
**Hasta 2026-07-23** · contexto y exploración previos

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `reglas_documentacion_agent.md` | CREADO · 2026-07-22 18:42 | el archivo mismo |
| `Usos_Productos_Afiliados_SIN_ID.xlsx` | CREADO · 2026-07-23 12:00 | entregado por el reto |
| `apuntes/Cómo usar los recursos del Reto Seguros (1).docx` | CREADO · 2026-07-23 12:56 | entregado por el reto |
| `apuntes/exploracion_dataset_nuevo.md` | CREADO · 2026-07-23 14:43 | el archivo mismo |
| `apuntes/nomenclatura_afiliados.md` | CREADO · 2026-07-23 14:43 | el archivo mismo |
| `artifacts/dataset_afiliados.html` | CREADO · 2026-07-23 14:44 | el archivo mismo |
| `CLAUDE.MD` | CREADO | el archivo mismo |

> Nota: las fechas de it. 0 son las que reporta el sistema de archivos (última modificación),
> no necesariamente el instante exacto de creación.

---

## Iteración 1 — limpieza de `RANGO_SALARIAL`
**2026-07-24** · pedido: limpiar una sola columna, sin tocar nada más

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `limpieza_rango_salarial.py` | **CREADO** · 15:40 | [`decisiones_limpieza_rango_salarial.md`](./decisiones_limpieza_rango_salarial.md) |
| `Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv` | **CREADO** · 15:40 | ídem, § 4 y § 5 |
| `decisiones_limpieza_rango_salarial.md` | **CREADO** en la raíz del proyecto | el archivo mismo |
| `CLAUDE.MD` | **ITERADO** | ídem, § 1 |
| `Usos_Productos_Afiliados_SIN_ID.xlsx` | **sin tocar** (leído, nunca escrito) | — |

---

## Iteración 2 — documentación bajo marco AR
**2026-07-24** · pedido: aplicar el marco de `reglas_documentacion_agent.md` y mover a `apuntes/`

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `decisiones_limpieza_rango_salarial.md` | **ITERADO + MOVIDO** · raíz → `apuntes/` · 15:44 | el archivo mismo, § 8 y Bitácora #1 |
| `apuntes/exploracion_dataset_nuevo.md` | **ITERADO** · 15:45 | su propia Bitácora #2 |
| `CLAUDE.MD` | **ITERADO** · 15:45 | [`decisiones_limpieza_rango_salarial.md`](./decisiones_limpieza_rango_salarial.md) § 8 |
| `limpieza_rango_salarial.py` | **ITERADO** · 15:45 | ídem (solo una ruta en un comentario) |

> El `.md` de decisiones **no se duplicó**: es el mismo archivo evolucionado, no un archivo nuevo
> junto al viejo. No existe una copia de su versión de it. 1.

---

## Iteración 3 — creación de este registro
**2026-07-24** · pedido: dejar en `apuntes/` la línea de vida de los archivos

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `apuntes/linea_de_vida_archivos.md` | **CREADO** | este archivo (encabezado) |
| `CLAUDE.MD` | **ITERADO** | se le agregó el puntero a este registro, en "Convención de documentación" |

---

## Iteración 4 — etiquetado con hipótesis de negocio
**2026-07-24** · pedido: score de propensión por las 5 categorías sobre las 500.000 filas

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `etiquetado_hipotesis.py` | **CREADO** | [`decisiones_etiquetado_hipotesis.md`](./decisiones_etiquetado_hipotesis.md) |
| `Usos_Productos_Afiliados_ETIQUETADO.csv` | **CREADO** | ídem, § 5 y § 9 |
| `apuntes/decisiones_etiquetado_hipotesis.md` | **CREADO** | el archivo mismo |
| `CLAUDE.MD` | **ITERADO** | ídem, § 11 |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |
| `Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv` | **sin tocar** (leído, nunca escrito) | — |

---

## Iteración 5 — corrección de H1, H2 y H3 del etiquetado (v2)
**2026-07-24** · pedido: graduar Crédito, rebalancear Hogar, restringir Mascotas en `categoria_top`

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `etiquetado_hipotesis.py` | **ITERADO** · ahora produce la v2 | [`decisiones_etiquetado_hipotesis.md`](./decisiones_etiquetado_hipotesis.md) § 12 |
| `Usos_Productos_Afiliados_ETIQUETADO_V2.csv` | **CREADO** | ídem, § 12.2 y § 12.4 |
| `apuntes/decisiones_etiquetado_hipotesis.md` | **ITERADO** · § 12 agregada, § 1-11 conservadas | su propia Bitácora #2 |
| `CLAUDE.MD` | **ITERADO** | ídem, § 12.7 |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |
| `Usos_Productos_Afiliados_ETIQUETADO.csv` | **sin tocar** (leído como entrada) · pasa a evidencia del antes | — |

> ⚠️ `etiquetado_hipotesis.py` fue iterado en el sitio: hoy produce la **v2**. La v1 ya no es
> re-ejecutable desde el script actual; su salida (`ETIQUETADO.csv`) y sus números se conservan.

---

## Iteración 6 — filas sin ninguna señal (v3)
**2026-07-24** · pedido: no forzar desempate entre ceros; marcar esas filas para escalamiento

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `etiquetado_hipotesis.py` | **ITERADO** · ahora produce la v3 | [`decisiones_etiquetado_hipotesis.md`](./decisiones_etiquetado_hipotesis.md) § 14 |
| `Usos_Productos_Afiliados_ETIQUETADO_V3.csv` | **CREADO** · 25 columnas | ídem, § 14.2 y § 14.3 |
| `apuntes/decisiones_etiquetado_hipotesis.md` | **ITERADO** · § 13 y § 14 agregadas | su propia Bitácora #3 |
| `CLAUDE.MD` | **ITERADO** | ídem, § 14.5 |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |
| `Usos_Productos_Afiliados_ETIQUETADO_V2.csv` | **sin tocar** (leído como entrada) · pasa a evidencia del antes | — |

---

## Iteración 7 — análisis de la base documentado
**2026-07-24** · pedido: documentar las cualidades de las 3.534 filas sin señal, como análisis de la db

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `apuntes/db.md` | **CREADO** · análisis del dataset, solo hechos | el archivo mismo |
| `CLAUDE.MD` | **ITERADO** · puntero a `db.md` | ídem |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |
| `apuntes/exploracion_dataset_nuevo.md` | **sin tocar** · su dato de `PISCILAGO` se corrige en `db.md` A3, no en el sitio | [`db.md`](./db.md) A3 |

> Sin cambios de datos ni de código en esta iteración: `ETIQUETADO_V3.csv` sigue vigente sin modificar.

---

## Iteración 8 — estructuración de hipótesis de producto (bloque parcial)
**2026-07-24** · pedido: emparejar categoría → producto específico (pendiente #6)

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `Hipotesis_Generales_Seguros.md` | **RECIBIDO** · copiado al repo por el usuario | fuente externa |
| `estructurar_hipotesis.py` | **CREADO** | [`decisiones_producto_especifico.md`](./decisiones_producto_especifico.md) § 2 |
| `hipotesis_producto_estructuradas.csv` | **CREADO** · 9 filas | ídem, § 2.2 |
| `apuntes/decisiones_producto_especifico.md` | **CREADO** | el archivo mismo |
| `CLAUDE.MD` | **ITERADO** · aclaración de elegibilidad + estado del pendiente #6 | ídem, § 1 y § 6 |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |
| `Usos_Productos_Afiliados_ETIQUETADO_V3.csv` | **sin tocar** · no llegó a consumirse | — |

> 🚧 **Bloque parcial.** `Usos_Productos_Afiliados_PRODUCTO_V1.csv` **no se generó**: falta el catálogo
> de la Base Maestra en formato estructurado. Ver [`decisiones_producto_especifico.md`](./decisiones_producto_especifico.md) § 3.

---

## Iteración 9 — emparejamiento categoría → producto (bloque completado)
**2026-07-24** · pedido: retomar el pendiente #6 con el catálogo ya disponible

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `catalogo_productos.csv` | **RECIBIDO** · 24 productos, aportado por el usuario | fuente externa |
| `Hipotesis_Generales_Seguros.md` | **ITERADO** · por el usuario: 10 hipótesis resueltas + 2 decisiones transversales | el archivo mismo |
| `estructurar_hipotesis.py` | **ITERADO** · 9 → 21 filas, formato en forma normal disyuntiva | [`decisiones_producto_especifico.md`](./decisiones_producto_especifico.md) § 8 |
| `hipotesis_producto_estructuradas.csv` | **ITERADO** · 21 filas | ídem, § 8.2 |
| `emparejar_producto.py` | **CREADO** | ídem, § 9 |
| `Usos_Productos_Afiliados_PRODUCTO_V1.csv` | **CREADO** · 29 columnas | ídem, § 10 |
| `apuntes/decisiones_producto_especifico.md` | **ITERADO** · § 7-15 agregadas, § 1-6 conservadas | su propia Bitácora #2 |
| `CLAUDE.MD` | **ITERADO** · pendiente #6 → decisión #6 | ídem, § 15 |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |
| `Usos_Productos_Afiliados_ETIQUETADO_V3.csv` | **sin tocar** (leído como entrada) · pasa a evidencia del antes | — |

---

## Iteración 10 — declaración directa y corrección de `APEXEQ-PAL-01` (V2)
**2026-07-24** · pedido: 3 decisiones de negocio + respuesta a la pregunta pendiente

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `estructurar_hipotesis.py` | **ITERADO** · campo `flujo`, 21 → 24 filas | [`decisiones_producto_especifico.md`](./decisiones_producto_especifico.md) § 16.4 |
| `hipotesis_producto_estructuradas.csv` | **ITERADO** · 24 filas | ídem, § 16.2 |
| `emparejar_producto.py` | **ITERADO** · excluye declaración directa, respaldo Movilidad → BICI-01 | ídem, § 16.2 |
| `Usos_Productos_Afiliados_PRODUCTO_V2.csv` | **CREADO** · 29 columnas | ídem, § 16.5 y § 16.6 |
| `apuntes/decisiones_producto_especifico.md` | **ITERADO** · § 16 agregada, § 1-15 conservadas | su propia Bitácora #3 |
| `CLAUDE.MD` | **ITERADO** | ídem, § 16.9 |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |
| `Usos_Productos_Afiliados_PRODUCTO_V1.csv` | **sin tocar** (leído como entrada) · pasa a evidencia del antes | — |

> ⚠️ Los documentos citados como fuente del pedido (`Integracion_con_Nicolas.md`,
> `Hipotesis_Generales_Seguros.md` actualizado) **no estaban en el repo**. `Integracion_con_Nicolas.md`
> nunca se creó; el `.md` de hipótesis conserva su versión de la it. 9. Se implementó con el pedido
> como fuente. Ver [`decisiones_producto_especifico.md`](./decisiones_producto_especifico.md) § 16.1.

---

## Iteración 11 — función individual + demo Streamlit
**2026-07-24** · pedido: envolver todo lo hecho en `recomendar(perfil)` + demo. 2 horas.

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `motor.py` | **CREADO** · `recomendar(perfil)` + 5 casos de prueba | docstring del módulo |
| `app.py` | **CREADO** · demo Streamlit de una página | `README.md` |
| `README.md` | **CREADO** · ejecutable en <2 min (requisito del brief) | el archivo mismo |
| `requirements.txt` | **CREADO** | ídem |
| `Usos_Productos_Afiliados_PRODUCTO_V2.csv` | **sin tocar** · usado solo para verificar paridad | — |

> **Paridad verificada contra el lote** (2.000 filas reales): **100 %** con
> `segmento_grupo_familiar`, **93,10 %** sin él. La diferencia es una sola regla no
> evaluable sin ese campo, declarada en `reglas_omitidas` de cada respuesta.
> Sin documento de decisiones nuevo: por tiempo, el razonamiento está en el docstring
> de `motor.py`.

---

## Iteración 12 — reorganización de la estructura de carpetas
**2026-07-24** · pedido: sacar datos y scripts de la raíz. Cierra el pendiente #5 de `CLAUDE.MD`.

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `Usos_Productos_Afiliados_SIN_ID.xlsx` | **MOVIDO** → `data/raw/` | `CLAUDE.MD`, decisión #7 |
| Los 6 CSV derivados | **MOVIDOS** → `data/processed/` | ídem |
| `catalogo_productos.csv`, `hipotesis_producto_estructuradas.csv` | **MOVIDOS** → `data/catalogo/` | ídem |
| `limpieza_rango_salarial.py`, `etiquetado_hipotesis.py`, `estructurar_hipotesis.py`, `emparejar_producto.py` | **MOVIDOS** → `scripts/` · 15 referencias de ruta actualizadas | ídem |
| `motor.py` | **ITERADO** · 2 rutas · **no se movió** (arranque sin prefijos) | ídem |
| `app.py` | **sin tocar** · no tenía rutas propias | — |
| `README.md`, `CLAUDE.MD` | **ITERADOS** · rutas + sección de estructura | ídem |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |

> Verificado **antes y después**: los 5 casos de prueba y Streamlit (HTTP 200, log sin errores).
> Además se ejecutó `scripts/estructurar_hipotesis.py` de verdad para confirmar que *escribe*
> en la ruta nueva, no solo que la lee.

---

## Iteración 13 — campo `diferencia_clave` en la salida
**2026-07-24** · pedido: cambio aditivo chico, sin tocar la lógica existente

| Archivo | Acción | Dónde está el porqué |
|---|---|---|
| `motor.py` | **ITERADO** · campo nuevo `diferencia_clave`, solo cuando `producto_indiferenciado = true` | docstring de `_diferencia_clave()` |
| `apuntes/linea_de_vida_archivos.md` | **ITERADO** | este registro |

> Arma el texto con el `perfil_objetivo` de `catalogo_productos.csv` para el `producto_top` y
> cada alternativo. Si un producto no está en el catálogo se omite del texto, no falla.
> Cuando `producto_indiferenciado = false`, el campo **no aparece** (no se manda como `null`).
> Verificado: caso 2 correcto, los 5 casos consistentes, Streamlit HTTP 200 sin errores.
> Sin documento de decisiones ni cambios en `CLAUDE.MD`, por tiempo.

---

## Iteración 14 — motor genérico de reglas (reescritura de `motor.py`)
**2026-07-25** · pedido: motor agnóstico de dominio, con 3 datasets/hipótesis de prueba

| Archivo | Acción |
|---|---|
| `motor.py` | **REESCRITO por completo** — ya no sabe nada de Colsubsidio, ver `RESUMEN_SESION.md` |
| `app.py` | **REESCRITO** — selectores de dataset/hipótesis, formulario dinámico |
| `data/hipotesis/hipotesis_colsubsidio_ejemplo.json` | **CREADO** — caso de prueba, el dominio viejo conservado como ejemplo |
| `data/datasets/clientes_socioeconomico.json` | **CREADO** — 500 filas sintéticas |
| `data/hipotesis/hipotesis_socioeconomico.json` | **CREADO** |
| `data/hipotesis/hipotesis_prueba_c.json` | **CREADO** — hipótesis inventada para probar agnosticismo |
| `scripts/generar_dataset_sintetico.py` | **CREADO** |
| `seguros.db` | **CREADO** — SQLite, 3 tablas (`perfiles`, `recomendaciones`, `hipotesis_log`) |
| `CLAUDE.MD` | **ITERADO** — sección de cambio de arquitectura al inicio |
| `RESUMEN_SESION.md` | **CREADO** |

> Las 3 pruebas pasaron. Prueba B (dataset Colsubsidio) da la misma `categoria_top` que el
> motor viejo pero **score distinto** (0.7566 vs 1.0) — reportado, no oculto: el formato
> genérico no puede expresar buckets graduados ni pesos de negocio, solo frecuencia real.
> Detalle completo en `RESUMEN_SESION.md`.

---

## Cómo agregar una iteración nueva

1. Agregá una sección `## Iteración N — <título corto>` **al final**, con la fecha y el pedido en una línea.
2. Una fila por archivo tocado: `CREADO` / `ITERADO` / `MOVIDO` / `ELIMINADO`, y el puntero a dónde está el porqué.
3. Actualizá la tabla **Estado actual** de arriba (columna "Última iteración").
4. **No expliques el motivo del cambio acá** — va en el documento del archivo o en su bitácora.
