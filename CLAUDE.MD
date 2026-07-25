# CLAUDE.md — Motor genérico de reglas (nacido del reto Colsubsidio x 30X)

Este archivo existe porque el contexto completo del proyecto se construyó en una conversación de chat aparte, no aquí. Léelo completo antes de tocar cualquier archivo del repo.

## 🔀 CAMBIO DE ARQUITECTURA (25 julio 2026) — leer esto primero

**`motor.py` y `app.py` ya NO son especificos de Colsubsidio ni de seguros.** Se reescribieron como un **motor genérico de reglas de propensión**: recibe un perfil, la ruta a un dataset, y la ruta a un archivo de hipótesis (columna/operador/valor → categoría), y devuelve una recomendación. Ningún nombre de columna ni de categoría de negocio está hardcodeado en el código — todo vive en archivos de `data/`.

- **`recomendar(perfil, ruta_dataset, ruta_hipotesis)`** es la función central. El peso de cada regla se calcula automáticamente (frecuencia real en el dataset), no son pesos de negocio ajustados a mano.
- El caso de uso de Colsubsidio **sigue existiendo como uno de tres casos de prueba**, no como el único dominio: `data/hipotesis/hipotesis_colsubsidio_ejemplo.json` + `data/processed/*.csv`.
- Persistencia nueva: **`seguros.db`** (SQLite) — guarda cada perfil y cada recomendación completa, para poder reconstruir "por qué se recomendó X" después. **Esto NO es RAG**: es un log de auditoría transaccional, no hay embeddings ni búsqueda semántica ni vector store. La recomendación se calcula evaluando reglas directas contra el dataset; la DB solo registra el resultado después, no participa en calcularlo.
- **Todo el contenido de negocio de Colsubsidio que sigue abajo (categorías oficiales, hipótesis por producto, reglas de elegibilidad dura, el catálogo de 24 productos, etc.) sigue siendo válido como DOCUMENTACIÓN DE DOMINIO** — es el material que alimenta el caso de prueba `hipotesis_colsubsidio_ejemplo.json`. Lo que cambió es que el motor ya no lo tiene incrustado en Python: lo lee de un archivo.
- Detalle completo de la migración, qué se perdió en la traducción de reglas complejas al formato genérico, y las 3 pruebas de validación: **`RESUMEN_SESION.md`**.

---

## Qué es este proyecto (contexto original, Colsubsidio x 30X)

Motor de recomendación para el reto de Seguros del Hackathon Colsubsidio x 30X (22-26 julio 2026). Colsubsidio quiere pasar de "no sé qué seguro necesito" a "ya quedé asegurado" sin intervención humana. Este repo nació como **solo la pieza del motor de recomendación** de ese reto — no el bot conversacional, no la redacción de respuestas. El motor genérico de reglas de la sección de arriba es la evolución de esa pieza, capaz de servir a este caso Y a cualquier otro con la misma forma (perfil + dataset + hipótesis → categoría).

## Alcance de este repo — qué es tuyo y qué NO

**Sí es responsabilidad de este repo:**
- Etiquetar el dataset de afiliados con las hipótesis de negocio
- Calcular similitud entre un perfil nuevo y perfiles existentes
- Calcular propensión por categoría de seguro
- Entregar una respuesta estructurada (datos, no texto)

**NO es responsabilidad de este repo (lo hace otro miembro del equipo, Nicolás, en otro repo):**
- El bot conversacional que habla con el usuario final
- Redactar en lenguaje natural la recomendación (eso lo hace Nicolás con un LLM barato, tipo Mistral, tomando como insumo lo que este motor le entrega)
- Cualquier interfaz de usuario final

Si en algún punto el código de este repo empieza a generar frases para el usuario final en vez de datos estructurados, algo se torció — revisar contra este documento.

## Requisitos NO NEGOCIABLES del reto oficial (afectan cualquier decisión de diseño)

- La lógica debe ser **documentada y explicable** — nada de caja negra. Toda recomendación debe poder justificarse con reglas visibles, no con "el modelo lo decidió".
- Debe funcionar tanto para **afiliados como no afiliados** a Colsubsidio.
- El flujo debe funcionar de principio a fin sin intervención del equipo (el jurado lo prueba solo).
- README que permita ejecutar la solución en **menos de 2 minutos**.
- No se exige integración real con aseguradoras ni pasarela de pago real dentro del motor — el objetivo de negocio (llegar a "ya quedé asegurado") se mantiene, pero la ejecución de la transacción de pago se entrega a otro mecanismo fuera de este sistema.

## El dataset

Archivo: `data/raw/Usos_Productos_Afiliados_SIN_ID.xlsx` — 500.000 filas, una por afiliado, 15 columnas. **No existe ninguna columna con qué seguro compró cada persona** — toda propensión que calcule este motor es una regla de negocio definida por el equipo, no un patrón entrenado contra un histórico real.

### Columnas y su estado

| Columna | Completitud | Notas |
|---|---|---|
| RANGO_SALARIAL | 99% | ✅ **Limpieza cerrada (24 julio 2026).** Tenía dos esquemas de bucketing mezclados: 140 filas (no 17 — cifra corregida, el 17 original era la cardinalidad de la columna, no el conteo de filas afectadas) en el esquema minoritario, remapeadas al bucket fino con más población dentro del rango que cubrían. Ver `apuntes/decisiones_limpieza_rango_salarial.md`. **Columna de trabajo desde ahora: `RANGO_SALARIAL_LIMPIO`, en `data/processed/Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv` — no usar el `.xlsx` original ni la columna sin limpiar.** |
| RANGO_EDAD | 100% | — |
| GENERO | 100% | — |
| CIUDAD_AFILIADO | 42.32% | 57.68% de nulos — no se borran esas filas, se tratan como categoría "Desconocida" |
| DROGUERIA | 100% | 17.65% de activación en "SI" — la señal de comportamiento más fuerte que existe |
| VIVIENDA, HOTELES, AGENCIAS | 100% | Activación casi nula (0.007%, 0.03%, 0.02%). Son dato real, no error — se usan con peso bajo, no se "corrigen" |
| PISCILAGO | 100% | Constante (siempre el mismo valor) — se excluye del modelo, no aporta nada. No es un problema de limpieza, es una decisión de qué variables usar |
| CATEGORIA, SEGMENTO_GRUPO_FAMILIAR, SEGMENTO_POBLACIONAL, PIRAMIDE_NUEVA | 100% | Códigos anonimizados intencionalmente (LAMBDA, SIGMA, etc.), confirmado directamente por el negocio — no es un hueco de información, es una decisión de diseño de Colsubsidio. Propósito de cada columna confirmado (ver abajo), significado de cada código individual NO divulgado |
| EMPRESA_FOCO | 100% | Empresa empleadora anonimizada |
| SERIE | 100% | Solo identificador de fila, no se usa como variable |

**Qué significa cada columna de códigos anonimizados (confirmado por negocio, fuente directa, 23 julio 2026):**
- `CATEGORIA` — categoría del afiliado dentro del sistema de subsidio familiar
- `SEGMENTO_GRUPO_FAMILIAR` — clasifica la composición del hogar / estructura familiar del afiliado
- `SEGMENTO_POBLACIONAL` — segmentación individual construida a partir de ingresos, edad y PAC
- `PIRAMIDE_NUEVA` — clasifica la **empresa aportante** (no al afiliado directamente) dentro de la pirámide empresarial de Colsubsidio

**Regla de uso de estos 4 códigos:** sirven para calcular similitud entre perfiles (mismo código = mismo grupo real, eso es suficiente para comparar). **Nunca se usan para redactar la explicación que ve el usuario final** — no significan nada legible para una persona fuera de Colsubsidio.

### Qué NO se limpia, y por qué (importante — no repetir este trabajo)

- **Los ~15.560 grupos de filas "duplicadas" NO son duplicados reales.** Son personas distintas que comparten valores en columnas de baja cardinalidad (género, rango de edad, etc.) — con 500.000 filas y pocas categorías posibles por columna, es matemáticamente normal. **No aplicar deduplicación bajo ningún criterio.**
- **PISCILAGO no se "arregla"**, se excluye de las variables del modelo.
- **HOTELES, AGENCIAS, VIVIENDA no se "corrigen"** por tener poca activación — son datos reales, solo raros.
- **Los códigos griegos no se traducen ni se infieren** — su significado individual no está disponible y no hay que inventarlo.

### ✅ Limpieza de `RANGO_SALARIAL` — CERRADA (24 julio 2026)

140 filas remapeadas (no 17 — ver corrección arriba) al esquema dominante, por máxima población dentro del rango que cubrían. 4.988 nulos (0.998%) recategorizados como `"Desconocido"`, ninguna fila borrada. Detalle completo, tabla de equivalencias y verificación en `apuntes/decisiones_limpieza_rango_salarial.md`. Pendiente heredado de este bloque: decidir si `"Desconocido" = "Desconocido"` cuenta como match en la función de similitud (recomendación ya dada, no implementada — ver pendiente #2 abajo).

## Categorías oficiales de seguro (son exactamente estas 5, no agregar ni inventar subcategorías)

Mascotas, Hogar, Crédito, Movilidad, Personal y Familiar.

## Nivel de confianza de las hipótesis por categoría

| Categoría | Confianza | Columnas clave |
|---|---|---|
| Crédito | Alta | RANGO_SALARIAL |
| Personal y Familiar | Alta | DROGUERIA, SEGMENTO_GRUPO_FAMILIAR, RANGO_EDAD |
| Hogar | Media | RANGO_SALARIAL + CIUDAD_AFILIADO combinados (VIVIENDA sola casi no activa) |
| Movilidad | Baja-media | RANGO_SALARIAL + CIUDAD_AFILIADO periférica (mejor para Moto específicamente) |
| Mascotas | Baja, no nula | Sin columna propia en el dataset — se apoya en `fuente_3_contexto_nacional.csv` (estadística externa: DANE + estudio de mercado) |

Detalle completo de cada hipótesis, producto por producto: ver `Hipotesis_Generales_Seguros.md` (debe copiarse a este repo si no está ya).

## Arquitectura decidida

**Stack: Python, un solo lenguaje.**
- Datos y etiquetado: pandas + duckdb
- Motor de similitud: `scikit-learn NearestNeighbors` — **NO usar base de datos vectorial / embeddings para esto.** Los datos son estructurados (columnas con categorías), no texto libre. Un vector DB está pensado para similitud semántica de texto; forzarlo aquí sería más lento de construir y menos explicable. `NearestNeighbors` calcula distancia directa entre columnas y permite justificar cada match con las columnas exactas que coincidieron — eso es lo que exige el requisito de "no caja negra".
- Si en algún momento se indexa texto libre (ej. las fichas de producto en prosa), ahí sí es válido usar un vector DB simple (ChromaDB) — pero es una fuente aparte, no el corazón del motor.
- Exposición del contrato hacia el bot de Nicolás: **FastAPI** (genera documentación automática que sirve como el contrato mismo).
- Demo interna para mostrar avances al equipo sin depender del bot: **Streamlit**.

## Las tres fuentes que consulta el motor (patrón RAG — Retrieval-Augmented Generation)

Este motor es la parte de **Retrieval** de un sistema RAG completo (el bot de Nicolás con Mistral es la parte de Generation). "Retrieval" no implica necesariamente embeddings — aquí se implementa como comparación estructurada.

1. **La consulta** — el perfil que llega del bot (no es una fuente, es el input que dispara la búsqueda)
2. **Fuente interna** — los 500.000 afiliados, ya etiquetados con las hipótesis. Motor: `NearestNeighbors`
3. **Fuente externa** — `fuente_3_contexto_nacional.csv`, correlatos de estadística nacional (DANE, estudios de mercado) para categorías donde el dataset interno no alcanza (hoy: Mascotas). Ver `Fuente_3_README.md` para el esquema de columnas y cómo agregar filas nuevas.

**Fórmula de combinación:** `score_final = score_reglas_internas (Fuente 2) + ajustes_fuente_3`, recortado entre 0 y 1.

## Reglas de elegibilidad dura (van ANTES de calcular propensión, no junto con ella)

4 productos con elegibilidad por edad verificada (no es hipótesis, es dato real de los certificados de la aseguradora):
- AP-CHUBB-01, APDIG-CHUBB-01: 18 a 65 años (permanencia hasta 69+364)
- ONCO-CHUBB-01: 18 a 64 años (permanencia hasta 65+364)
- URB-CHUBB-01: condición de compra/medio de pago, no es regla de edad

**Desajuste resuelto (24 julio 2026) — regla, no corrección de dato:** el problema no es solo ONCO-CHUBB-01, es estructural: los buckets `RANGO_EDAD = "Mayor de 55 años"` (sin techo) y `RANGO_EDAD = "Menor de 19 años"` (sin piso) no tienen la precisión que los 3 productos con edad dura necesitan (mínimo 18, máximo 65-69 según el producto). No se ajustan los buckets del dataset para calzar con esto — degradaría el dato para el resto de hipótesis que sí los usan bien.

**Regla de elegibilidad para el pendiente #6 (emparejar categoría → producto específico), a implementar cuando se construya ese paso, no antes:** cualquier producto con límite de edad duro cuyo umbral caiga dentro de un bucket (no coincida con su borde) no se ofrece con certeza solo con el bucket disponible. Si el perfil cae en `"Menor de 19 años"` o `"Mayor de 55 años"` y el producto candidato es uno de los 3 con regla de edad, la salida debe marcar `pendiente_confirmacion_edad = true` en vez de confirmar o descartar el producto. Para los demás buckets (20-35, 36-45, 46-55) no aplica — están completamente dentro del rango permitido de los tres productos, sin ambigüedad.

## El contrato (bot Nicolás → este motor)

Definido de este lado, pendiente de que Nicolás confirme el suyo — si hay diferencias de nombres de campo, resolver con una capa de traducción, no reescribiendo el motor:

```json
{
  "afiliado": true,
  "genero": "M",
  "rango_edad": "20 a 35 años",
  "rango_salarial": "Entre 1 y 1.5 SMLV",
  "ciudad": "SOACHA",
  "tiene_dependientes": null,
  "estado_civil": null,
  "vive_solo": null,
  "tiene_vivienda_propia": null,
  "tiene_vehiculo": {"tipo": null, "posee": null},
  "tiene_mascota": null,
  "viaja_frecuente": null,
  "usa_drogueria": null,
  "categoria_interes_declarada": null
}
```

Nota importante: `tiene_vivienda_propia` es un campo NUEVO que captura el bot en conversación — **no es lo mismo** que la columna `VIVIENDA` del dataset, que mide uso del beneficio de vivienda de Colsubsidio, no propiedad real. No confundir los dos al programar.

## Lo que este motor debe devolver (objeto de salida — datos, nunca texto redactado)

```json
{
  "producto_id": "...",
  "categoria": "...",
  "score_propension": 0.0,
  "confianza": "alta|media|baja",
  "reglas_activadas": ["..."],
  "alternativas_descartadas": ["..."],
  "requiere_escalamiento": false,
  "fuentes": ["..."],
  "estado_dato": "verificado|supuesto_demo|no_disponible"
}
```

## Decisiones ya tomadas (log — actualizar cada vez que se cierre una)

1. ✅ **Limpieza de datos (cerrada 24 julio 2026):** solo `RANGO_SALARIAL` se limpió. 140 filas remapeadas al esquema dominante (no 17 — corrección de cifra), 4.988 nulos a `"Desconocido"`. Ninguna otra columna se tocó, ninguna fila se eliminó (500.000 entran, 500.000 salen). Detalle en `apuntes/decisiones_limpieza_rango_salarial.md`.
2. ✅ **Regla de elegibilidad por edad (cerrada 24 julio 2026):** el desajuste entre buckets de `RANGO_EDAD` y los límites reales de 3 productos (AP-CHUBB-01, APDIG-CHUBB-01, ONCO-CHUBB-01) se resuelve con `pendiente_confirmacion_edad = true` cuando el perfil cae en `"Menor de 19 años"` o `"Mayor de 55 años"`. Ver detalle completo en la sección de reglas de elegibilidad dura arriba.
3. ✅ **Etiquetado de las 500.000 filas con las hipótesis de negocio (cerrada 24 julio 2026, 3 iteraciones — V1/V2/V3):** score de propensión por categoría implementado, con escala graduada de `RANGO_SALARIAL_LIMPIO` (no binaria), regla de "Desconocido" neutro, y ruta explícita `requiere_escalamiento` para perfiles sin ninguna señal. Archivo vigente: `data/processed/Usos_Productos_Afiliados_ETIQUETADO_V3.csv`.
4. ✅ **Emparejamiento categoría → producto específico (cerrada 24 julio 2026, 2 iteraciones — V1/V2):** catálogo real de 24 productos construido (`data/catalogo/catalogo_productos.csv`, no 27 ni 30 — cifras corregidas). Hipótesis de producto estructuradas con escala única de salario. 9 productos (INCENDIO-DEUDOR-01, CARRO-01, los 4 de Chubb con edad dura, DESEMP-01, VIAJE-01, SOAT-01) confirmados como **inalcanzables por el motor de propensión** — se ofrecen solo por declaración directa del usuario (`categoria_interes_declarada`), nunca compiten por score. Solo 9 de 24 productos llegan a ser recomendados por propensión — documentado y explicado, no es una falla. Archivo vigente: `data/processed/Usos_Productos_Afiliados_PRODUCTO_V2.csv`. Detalle completo en `Hipotesis_Generales_Seguros.md` y `apuntes/decisiones_producto_especifico.md`.
5. ✅ **Arquitectura de similitud (cerrada 24 julio 2026, bajo presión de tiempo):** fórmula directa confirmada — no se construye capa de `NearestNeighbors`. Los pesos por categoría y la combinación con Fuente 3 (Mascotas) ya están implementados dentro del etiquetado V3 y el producto V2, no son trabajo aparte. Los 3 puntos que estaban pendientes por esto (arquitectura, pesos, fórmula de combinación) se cierran juntos porque el trabajo ya construido los resuelve.

6. ✅ **Motor envuelto como función llamable + validado (cerrada 24 julio 2026, bajo presión de 2 horas):** `motor.py` con `recomendar(perfil: dict) -> dict`, demo en Streamlit (`app.py`) verificada corriendo (HTTP 200). Validado con 5 casos de prueba + paridad medida contra 2.000 filas reales del lote: **93.10% de paridad exacta sin `segmento_grupo_familiar`** (número realista de producción, ese campo nunca va a estar disponible en vivo) vs. 100% con él (escenario teórico). Divergencias 100% explicadas por una sola regla omitida correctamente, no improvisada. README mínimo incluido (`requirements.txt` + instrucciones). Sin FastAPI, sin reestructurar carpetas — decisión consciente por tiempo, no pendiente.

7. ✅ **Estructura de carpetas del repo (cerrada 24 julio 2026) — cierra el pendiente #5.** Los datos y los scripts salieron de la raíz; `motor.py` y `app.py` **se quedan en la raíz a propósito**, para que `streamlit run app.py` siga siendo el comando de arranque sin prefijos.

```
├── motor.py            recomendar(perfil) — la función que consume el bot
├── app.py              demo Streamlit
├── README.md           cómo correrlo en <2 min
├── requirements.txt
├── CLAUDE.MD
├── data/
│   ├── raw/            Usos_Productos_Afiliados_SIN_ID.xlsx (fuente, nunca se modifica)
│   ├── processed/      los 6 CSV derivados (limpieza → etiquetado V1/V2/V3 → producto V1/V2)
│   └── catalogo/       catalogo_productos.csv, hipotesis_producto_estructuradas.csv
├── scripts/            los 4 scripts de lote (limpieza, etiquetado, estructuración, emparejamiento)
└── apuntes/            decisiones, análisis y línea de vida
```

**Convención de rutas, para no volver a romperla:** todas las rutas de archivo se declaran como constantes `BASE / "..."` al inicio de cada módulo, nunca inline. En `motor.py` y `app.py`, `BASE` es la raíz (`Path(__file__).parent`); en `scripts/*.py` es `Path(__file__).parent.parent`, porque viven un nivel más abajo. Los scripts se corren desde la raíz: `python3 scripts/etiquetado_hipotesis.py`.

## Pendiente (actualizar según se resuelva)

6. Confirmación del esquema de Nicolás (su lado del contrato) — dos campos nuevos de nuestro lado ya documentados en `Integracion_con_Nicolas.md`: `producto_interes_declarado` (opcional) y confirmación de que `segmento_grupo_familiar` NO hace falta pedirlo

## Convención de documentación de decisiones

Cada decisión de limpieza, arquitectura o regla de negocio que se tome mientras se programa debe quedar en un archivo `.md` dentro del repo (ej. `decisiones_limpieza_rango_salarial.md`), con el razonamiento explicado en una frase simple — no solo el cambio, el porqué. Este `CLAUDE.md` se actualiza también, moviendo puntos de "Pendiente" a "Decisiones ya tomadas" conforme se cierren.

**Lección de sincronización (24 julio 2026, ocurrió dos veces):** los documentos de esta conversación con Claude (chat aparte de Claude Code) no llegan solos al repo — hay que copiarlos a mano cada vez. Cuando un prompt dice "confirma X.md como fuente", verificar PRIMERO que X.md exista y esté actualizado (timestamp, no solo presencia) antes de ejecutar nada — no asumir que ya está ahí. Si no está, usar el prompt mismo como fuente autoritativa si trae las decisiones completas, documentarlo explícitamente como se hizo en `apuntes/decisiones_producto_especifico.md` § 16.1, y avisar en vez de fallar en silencio o inventar contenido.