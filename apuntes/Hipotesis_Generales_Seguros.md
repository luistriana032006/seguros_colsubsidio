# Hipótesis generales de recomendación — consolidado del equipo

**Fuentes combinadas en este documento:**
1. Fichas de producto de la Base Maestra de Victor (**24 productos** — cifra corregida el 24 de julio: se había dicho "27" aquí y "30" en la conversación original con Claude; el conteo real, verificado tabla por tabla contra el Word, es 24. Catálogo estructurado completo: `catalogo_productos.csv`)
2. Hipótesis propuestas por Ana (23 julio, mensaje al equipo) — perfil del usuario → categoría de seguro

Ambas se cruzan contra las columnas reales de nuestra base de 500.000 afiliados para saber cuáles se pueden aplicar directo y cuáles dependen de lo que capture el bot en conversación.

**Dos tipos de regla, no los mezcles al construir el motor:**
- 🔒 **Elegibilidad dura** — dato verificado (viene de certificados/condiciones reales de la aseguradora). Si no se cumple, la persona NO califica, punto. No es propensión, es filtro obligatorio.
- 📊 **Hipótesis de propensión** — inferencia nuestra a partir del texto descriptivo de "perfil objetivo" de Victor. Es una regla de negocio que proponemos, no un dato verificado. Mismo estatus que las hipótesis que ya veníamos construyendo.

---

# FUENTE 1 — Base Maestra de Victor (fichas de producto)

> **>> ACTUALIZADO (24 julio 2026):** Claude Code, al construir el pendiente #6 (emparejar categoría → producto), encontró 10 de las 24 hipótesis de esta fuente con términos ambiguos ("bajo-medio", "medio-alto") o dependientes de códigos sin significado confirmado — no las forzó, las reportó. Se resolvieron todas abajo, con dos decisiones transversales que aplican a todo el documento:

**Escala única de `RANGO_SALARIAL_LIMPIO`** — de aquí en adelante, cualquier hipótesis que diga "bajo", "medio", "alto" se refiere exactamente a esto, no a una interpretación libre por producto:

| Tier | Buckets |
|---|---|
| Bajo | Menor al SMLV, Entre 1 y 1.5, Entre 1.5 y 2 |
| Medio | Entre 2 y 2.5, Entre 2.5 y 3, Entre 3 y 4 |
| Medio-alto | Entre 4 y 6, Entre 6 y 8 |
| Alto | Entre 8 y 10, Entre 10 y 20, Entre 20 y 30, Mayor a 30 |

**Producto general de respaldo por categoría** — cuando ningún producto con hipótesis específica aplica a una persona, se ofrece este en su lugar (evita dejar categorías completas sin producto asignable, que era un hueco real detectado al revisar esto):

> **>> CORREGIDO (24 julio 2026):** la corrida real del pendiente #6 encontró que CARRO-01 nunca puede ganar `categoria_top = Movilidad` por un choque con el score de Hogar — pasó a producto de declaración directa (ver sección nueva abajo). Movilidad cambia de respaldo a BICI-01, provisional.

| Categoría | Producto de respaldo |
|---|---|
| Crédito | DEUDOR-VIDA-01 |
| Personal y Familiar | VIDA-01 |
| Hogar | HOGAR-01 |
| Movilidad | ~~CARRO-01~~ → BICI-01 (provisional) |
| Mascotas | PET-SEG-01 |

## 🚪 Productos de declaración directa (fuera del motor de propensión)

**Origen: hallazgo real de la corrida del pendiente #6 (24 julio 2026), no una decisión de diseño anticipada.** Estos productos comparten algo que el motor no puede inferir del dataset — ninguna columna dice si alguien tiene un crédito hipotecario, un vehículo, o quiere un producto específico de Chubb con elegibilidad de edad. Se ofrecen solo cuando `categoria_interes_declarada` (ya en el contrato con Nicolás) confirma la intención directamente en la conversación — nunca compiten por `producto_top` en el ranking de propensión.

| Producto | Por qué salió de la competencia por propensión |
|---|---|
| INCENDIO-DEUDOR-01 | Su hipótesis (salario Alto) es estructuralmente inalcanzable: nadie con salario Alto llega nunca a `categoria_top = Crédito` — Hogar le gana antes, por diseño del score de categoría (H2). No hay forma de saber si alguien tiene crédito hipotecario sin que lo diga. |
| CARRO-01 | Mismo problema: nadie con salario Alto/Medio-alto llega a `categoria_top = Movilidad` — Hogar también le gana ahí. **Ya no es el producto general de respaldo de Movilidad** (ver corrección abajo). |
| AP-CHUBB-01, APDIG-CHUBB-01, ONCO-CHUBB-01, URB-CHUBB-01 | Tienen elegibilidad dura verificada (edad real) pero ninguna hipótesis de propensión — nunca compitieron por diseño, no por error. Su chequeo `pendiente_confirmacion_edad` se mantiene activo para cuando lleguen por declaración directa. |
| DESEMP-01 | Ya establecido: sin hipótesis estructurable (dependía de `EMPRESA_FOCO`, no verificable). |

**Corrección al producto general de respaldo de Movilidad:** con CARRO-01 fuera de la competencia por propensión, Movilidad queda sin respaldo designado. **BICI-01 pasa a ser el producto general de respaldo de Movilidad** — no es ideal (su hipótesis original es específica de edad 20-35, no un perfil amplio), pero es preferible a dejar la categoría sin respaldo. Marcado como decisión provisional, revisar si aparece tiempo para diseñar algo mejor.

---

## 🔒 Reglas de elegibilidad dura (dato real, no inferencia)

Victor sí encontró edades de elegibilidad verificadas para 4 productos — esto no estaba en nuestro análisis del CSV porque no viene del dataset, viene de los certificados de Chubb:

| Producto | Categoría | Regla de elegibilidad verificada |
|---|---|---|
| AP-CHUBB-01 (Accidentes personales) | Personal y Familiar | Ingreso 18 a 65 años + 364 días; permanencia hasta 69 años + 364 días (cobertura adicional de fracturas) |
| APDIG-CHUBB-01 (Accidentes personales digital) | Personal y Familiar | Ingreso 18 a 65 años + 364 días; permanencia hasta 69 años + 364 días |
| ONCO-CHUBB-01 (Oncológico) | Personal y Familiar | Ingreso 18 a 64 años + 364 días; permanencia hasta 65 años + 364 días |
| URB-CHUBB-01 (Protección Urbana) | Personal y Familiar | El bien debe cumplir reglas de compra/medio de pago/establecimiento definidas por el certificado (no es edad, es condición de compra) |

**Uso en el motor:** `RANGO_EDAD` de nuestra base sí permite aplicar esto como filtro previo — antes de calcular propensión, descarta productos donde la persona no califica por edad. Ojo con ONCO-CHUBB-01: nuestra categoría `RANGO_EDAD` más cercana ("Mayor de 55 años") probablemente incluye personas de más de 65, que ya NO calificarían — este es un caso donde el bucketing de nuestra base es más ancho que la regla real y hay que decidir cómo manejarlo (¿preguntar edad exacta en conversación para este producto específico?).

---

## 📊 Hipótesis de propensión por categoría — perfil objetivo traducido a SI/ENTONCES

### Crédito — confianza ya era ALTA, esto la refuerza

| Producto | Perfil objetivo (texto de Victor) | Hipótesis SI/ENTONCES | Columna(s) |
|---|---|---|---|
| DEUDOR-VIDA-01 | "Titulares de crédito que deben proteger el saldo y a sus herederos" | SI `RANGO_SALARIAL` sugiere capacidad de endeudamiento (ej. >1.5 SMLV) ENTONCES propensión a Vida Deudor. **Nota (24 jul):** este umbral excluye el pico real de la categoría Crédito (1-1.5 SMLV). Por eso se designa **DEUDOR-VIDA-01 como producto general de respaldo de Crédito** — se ofrece igual aunque no cumpla el umbral exacto, ya que aplica a cualquier titular de crédito sin importar el monto. | RANGO_SALARIAL |
| DESEMP-01 | "Empleados con riesgo de desempleo involuntario e independientes con riesgo de incapacidad" | **⚠️ Sin hipótesis estructurable (24 jul):** dependía de `EMPRESA_FOCO`, pero solo hay 2 valores (`EMP_000001`/`EMP_000002`) sin significado confirmado — no se puede saber cuál representa relación laboral formal. Sin condición verificable, no se estructura. | — |
| INCENDIO-DEUDOR-01 | "Deudores hipotecarios obligados a proteger el inmueble en garantía" | **⚠️→🚪 Reclasificado (24 jul):** su hipótesis (salario Alto) quedaba estructuralmente inalcanzable — nadie con ese perfil llega nunca a `categoria_top = Crédito`. Pasó a **producto de declaración directa** (ver sección nueva). | — |

### Personal y Familiar — confianza ya era ALTA, aquí es donde más material nuevo hay

| Producto | Perfil objetivo | Hipótesis SI/ENTONCES | Columna(s) |
|---|---|---|---|
| SALUD-01 | "Complementar atención de salud, acceso preferencial a clínicas" | **SI `DROGUERIA` = SI ENTONCES propensión a Póliza de Salud** | DROGUERIA — coincide exacto con el "Uso permitido" del PDF de Victor ("Droguería → abrir preguntas de salud") |
| ASMED-01 | "Familias que buscan orientación y acceso rápido a servicios médicos" | **Resuelto (24 jul):** se cae la condición de `SEGMENTO_GRUPO_FAMILIAR` (código sin significado confirmado, no verificable). Queda solo: SI `DROGUERIA` = SI ENTONCES propensión a Asistencias médicas familiares — misma condición que SALUD-01, van a empatar cuando ambas apliquen (honesto: no hay forma de diferenciarlas con lo que sabemos hoy) | DROGUERIA |
| VIDAAH-01 | "Protección familiar y ahorro disciplinado de mediano/largo plazo" | **Resuelto (24 jul):** SI `RANGO_SALARIAL` en tier **Medio-alto** (Entre 4 y 8 SMLV) Y `RANGO_EDAD` en 36-55 ENTONCES propensión a Vida y Ahorro | RANGO_SALARIAL, RANGO_EDAD |
| ASMULT-01 | "Hogares que valoran paquete económico de ayuda cotidiana" | **Resuelto (24 jul):** SI `RANGO_SALARIAL` en tier **Bajo o Medio** (hasta 4 SMLV) ENTONCES propensión a Asistencias múltiples | RANGO_SALARIAL |
| VIDA-01 | "Personas con dependientes que desean proteger el ingreso familiar" | **⚠️→✅ Reconvertido (24 jul):** dependía 100% de `SEGMENTO_GRUPO_FAMILIAR` sin significado confirmado, no verificable. En vez de forzar la hipótesis, se designa **VIDA-01 como el producto general de respaldo de Personal y Familiar** — se ofrece cuando ningún otro producto de la categoría aplica. Tiene sentido: es el seguro de vida genérico, la opción por defecto más natural | — (producto de respaldo, no hipótesis) |
| APEXEQ-PAL-01 | "Personas sensibles al precio que buscan protección básica" | SI `RANGO_SALARIAL` bajo (Menor al SMLV a 1.5 SMLV) ENTONCES propensión a este producto económico | RANGO_SALARIAL |
| EXEQ-01 | "Familias que desean evitar impacto financiero de un fallecimiento" | SI `RANGO_EDAD` = "Mayor de 55 años" ENTONCES propensión a Exequial | RANGO_EDAD |
| VIAJE-01 | "Viajeros con fecha/destino definidos" | **Sin columna candidata real.** Depende 100% de lo que capture el bot en conversación. | — |

### Hogar — confianza era MEDIA, sigue igual pero con un producto más para repartir la señal

| Producto | Perfil objetivo | Hipótesis SI/ENTONCES | Columna(s) |
|---|---|---|---|
| HOGAR-01 | "Propietarios o arrendatarios que desean proteger vivienda, contenido" | **Resuelto — precedencia explícita (24 jul):** SI (`RANGO_SALARIAL` en tier Medio-alto o Alto Y `CIUDAD_AFILIADO` no nula) O `VIVIENDA` = SI ENTONCES propensión a Hogar. `VIVIENDA=SI` califica solo, sin depender de lo demás. **Producto general de respaldo de la categoría Hogar.** | VIVIENDA, RANGO_SALARIAL, CIUDAD_AFILIADO |
| ARRENDA-01 | "Propietarios ante impago / arrendatarios que requieren respaldo" | **Resuelto (24 jul):** SI `RANGO_SALARIAL` en tier **Bajo o Medio** (hasta 4 SMLV) ENTONCES propensión a Seguro de Arrendamiento | RANGO_SALARIAL |

### Movilidad — confianza era BAJA, aquí sí aparece una combinación mejor que la que teníamos

| Producto | Perfil objetivo | Hipótesis SI/ENTONCES | Columna(s) |
|---|---|---|---|
| MOTO-01 | "Motociclistas, especialmente quienes usan la moto para trabajo" | **Resuelto (24 jul):** SI `RANGO_SALARIAL` en tier **Bajo o Medio** (hasta 4 SMLV) Y `CIUDAD_AFILIADO` en municipio periférico (Soacha, Mosquera, Zipaquirá, Funza) ENTONCES propensión a Moto | RANGO_SALARIAL, CIUDAD_AFILIADO |
| CARRO-01 | "Propietarios/conductores que desean cubrir daños, hurto" | **⚠️→🚪 Reclasificado (24 jul):** su hipótesis original quedaba estructuralmente inalcanzable — nadie con ese perfil llega nunca a `categoria_top = Movilidad`. Pasó a **producto de declaración directa** (ver sección nueva), ya no compite por propensión ni es respaldo de la categoría. | — |
| BICI-01 | "Usuarios de bici, scooter o patineta" | SI `RANGO_EDAD` = "20 a 35 años" (proxy débil, sin evidencia fuerte) ENTONCES propensión a Bici/Patineta. **Producto general de respaldo de Movilidad (provisional, 24 jul)** — no es ideal por lo específico de su hipótesis original, pero evita dejar la categoría sin respaldo tras la salida de CARRO-01. | RANGO_EDAD |
| SOAT-01 | "Propietarios de vehículos obligados a mantener SOAT" | No es propensión, es obligación legal — solo aplica una vez el bot confirma que la persona tiene vehículo. No se puede anticipar desde el dataset. | — |

### Mascotas — ya no es NULA del todo, ver Fuente 3

| Producto | Perfil objetivo | Hipótesis SI/ENTONCES |
|---|---|---|
| PET-SEG-01, PET-PREP-01, PET-ASIS-01 | "Tutores que buscan respaldo/acceso/orientación" | **Ninguna columna candidata dentro de nuestra base.** Las tres fichas de Victor tampoco traen ninguna pista de dataset. Pero sí existe una tasa base nacional (DANE) y correlatos direccionales (estrato/ingreso, hijos) que permiten una propensión previa — ver **Fuente 3** más abajo. **Decisión (24 jul):** entre los tres, ninguno tiene hipótesis diferenciadora — se designa **PET-SEG-01 como producto general de respaldo de Mascotas** (es el seguro propiamente dicho, más amplio que PET-PREP-01 que es solo un plan prepago, y que PET-ASIS-01 que es solo asistencia/orientación). |

---

# FUENTE 2 — Hipótesis de Ana (perfil de usuario → categoría)

> **>> CAMBIO (23 julio 2026):** Ana mandó esto como texto corrido, en párrafos, no en tabla ni en formato SI/ENTONCES. Lo que sigue es una **reestructuración hecha por Claude**, no una cita textual reformateada sola: la columna "Hipótesis de Ana (texto original)" preserva su idea central de cada párrafo casi palabra por palabra, pero la columna "Reformulada SI/ENTONCES" y el cruce contra columnas de la base **son interpretación y trabajo añadido**, no algo que Ana escribió. Si alguna reformulación no refleja bien lo que ella quiso decir, hay que corregirla con ella directamente, no asumir que la tabla es su versión final.

**Origen:** mensaje de Ana al equipo, 23 julio 2026, 5:01 p.m. Propone hipótesis directamente en lógica condicional, ya cercanas al formato SI/ENTONCES — se traducen aquí y se cruzan contra las columnas reales de la base.

**Principio que Ana dejó explícito y que debe regir todo el documento, no solo su parte:** estas son hipótesis iniciales, no recomendaciones automáticas. El agente conversacional debe **confirmar cada hipótesis con preguntas inteligentes antes de sugerir un seguro** — la señal del dato (sea del dataset o de Victor) dispara la pregunta, nunca la respuesta final. Esto aplica igual a las hipótesis de la Fuente 1.

| Hipótesis de Ana (texto original) | Reformulada SI/ENTONCES | Columna real disponible | Confianza |
|---|---|---|---|
| "Si tiene hijos → seguro de vida" | SI tiene dependientes económicos ENTONCES propensión a Vida | `SEGMENTO_GRUPO_FAMILIAR` (proxy sin diccionario — sirve para similitud, no para explicar) | Media, indirecta |
| "Si está casado o vive en pareja → vida o salud" | SI tiene pareja/responsabilidad compartida ENTONCES propensión a Vida/Salud | `SEGMENTO_GRUPO_FAMILIAR` (mismo proxy sin diccionario) | Media, indirecta |
| "Si tiene vivienda propia → seguro de hogar" | SI es propietario ENTONCES propensión a Hogar | ⚠️ **Ver nota de conflicto abajo — `VIVIENDA` NO significa esto en nuestra base** | Baja tal como está planteada |
| "Si posee carro o moto → seguro vehicular" | SI tiene vehículo ENTONCES propensión a Movilidad | Ninguna — no existe columna de tenencia de vehículo | Nula desde el dataset, 100% conversación |
| "Si viaja frecuente / usa hoteles y agencias de Colsubsidio → seguro de viaje" | SI `HOTELES`=SI O `AGENCIAS`=SI ENTONCES propensión a Viaje | `HOTELES` (0.03% activación), `AGENCIAS` (0.02% activación) — columnas reales, pero casi nunca se disparan | Baja, señal casi inexistente en volumen |
| "Si tiene mascotas → seguro para mascotas" | SI tiene mascota ENTONCES propensión a Mascotas | Ninguna directa — pero ver **Fuente 3**: sí hay tasa base nacional y correlatos aplicables | Baja pero ya no nula |
| "Rango salarial alto → plan premium; bajo → plan accesible" | SI `RANGO_SALARIAL` alto ENTONCES ofrecer cobertura premium; SI bajo ENTONCES priorizar plan accesible | `RANGO_SALARIAL` (99% completo) | **Alta** — esta es la más sólida de todo el mensaje de Ana |
| "Familia numerosa → combinar vida + salud" | SI núcleo familiar grande ENTONCES propensión combinada Vida + Salud | `SEGMENTO_GRUPO_FAMILIAR` (proxy sin diccionario) | Media, indirecta |
| "Vive solo → accidentes personales o salud" | SI vive solo (sin red de apoyo inmediata) ENTONCES propensión a Accidentes Personales/Salud | `SEGMENTO_GRUPO_FAMILIAR` (proxy sin diccionario) | Media, indirecta |
| "Joven y soltero → accidentes personales, a validar" | SI `RANGO_EDAD`="20 a 35 años" Y soltero ENTONCES propensión inicial a Accidentes Personales, validar en conversación | `RANGO_EDAD` (100% completo) + `SEGMENTO_GRUPO_FAMILIAR` (proxy) | Media — la propia Ana ya marcó esta como la que más necesita confirmación conversacional |

### ⚠️ Conflicto a resolver con Ana: "vivienda propia" ≠ columna `VIVIENDA`

Ana asume que la columna `VIVIENDA` de la base indica propiedad de una casa. **No es así según la exploración del dataset:** `VIVIENDA` es un flag de "¿usó el beneficio de vivienda de Colsubsidio?" (activación del 0.007%, ~36 personas de 500.000), no "¿tiene casa propia?". Son cosas distintas — alguien puede ser propietario sin haber usado nunca ese beneficio específico, y viceversa. Esto no invalida la hipótesis de negocio (sigue teniendo sentido ofrecer Hogar a quien parece tener vivienda), pero si se implementa literal como "SI VIVIENDA=SI" el motor va a fallar en detectar a casi todos los propietarios reales. Vale la pena que el equipo decida: o se usa `VIVIENDA` sabiendo que es una señal muy débil y distinta a "propiedad", o se pregunta tenencia de vivienda directamente en la conversación (que es justo lo que ya proponía el PDF de Victor: "¿Vives en propiedad o arriendo?").

---

# FUENTE 3 — Estadística nacional externa (para resolver el hueco de Mascotas)

**Origen:** búsqueda web dirigida, 23 julio 2026, específicamente para responder si existe algo mejor que "cero información" para Mascotas antes de tener que decírselo al jurado como excusa.

**Dos capas de fuente, con distinto nivel de autoridad — no tratarlas igual al citarlas:**

### Capa sólida — DANE, Encuesta Multipropósito 2021 (fuente oficial)
- **67% de los hogares colombianos tiene al menos una mascota** (~4.4 millones de familias).
- **60% tiene perro** específicamente.
- Uso recomendado: como **tasa base nacional (prior)** — si no se sabe nada más de una persona, la probabilidad de que tenga mascota ya no es "desconocida", es ~67% según la fuente oficial más reciente disponible. Se puede citar como "según el DANE" sin matiz adicional.

### Capa direccional — BrandStrat/Offerwise 2024 (estudio de mercado privado, 1.000 encuestas, 8 ciudades, estratos 2-6, no es censo)
- **Correlación inversa con estrato/ingreso:** estratos 2-4 → 62-65% de tenencia; estratos 5-6 → cae a 47%.
- **Hogares con hijos → más mascotas:** 67% de tenencia en hogares con hijos vs. 45% en hogares sin hijos.
- **Variación por ciudad:** la mayoría de ciudades entre 61-69%, pero Bucaramanga notablemente más baja, 40%.
- Uso recomendado: como **correlato direccional**, no como cifra exacta a citar frente al jurado con el mismo peso que el dato del DANE — decir "estudios de mercado sugieren" en vez de "está confirmado que".

### Traducción a hipótesis SI/ENTONCES, usando columnas que ya existen en la base

| Hipótesis | Columna(s) | Fuente que la respalda |
|---|---|---|
| Tasa base: toda persona parte de ~67% de probabilidad de tener mascota, antes de preguntar nada | Ninguna (aplica parejo a todos) | DANE |
| SI `RANGO_SALARIAL` bajo-medio ENTONCES propensión a Mascotas más alta que el promedio | RANGO_SALARIAL | BrandStrat (proxy ingreso↔estrato, no es exacto pero direccionalmente correlacionan en Colombia) |
| SI `SEGMENTO_GRUPO_FAMILIAR` indica presencia de hijos ENTONCES propensión a Mascotas más alta | SEGMENTO_GRUPO_FAMILIAR (código sin diccionario — usar solo para similitud interna) | BrandStrat |
| SI `CIUDAD_AFILIADO` = "BUCARAMANGA" ENTONCES ajustar la propensión a la baja (40% vs. 61-69% del resto de ciudades) | CIUDAD_AFILIADO | BrandStrat |

**Lo que esto cambia de fondo:** Mascotas pasa de "sin ningún punto de partida, resolver 100% en conversación" a "propensión previa calculable con dato poblacional real, que la conversación después confirma o corrige". Es el mismo diseño bayesiano correcto que ya se usa implícitamente en las otras categorías, solo que aquí el "prior" viene de estadística nacional en vez de la base interna de 500.000 — que para esta categoría específica no tiene nada que aportar.

---

## Resumen para llevar a la reunión con el equipo

**De la Base Maestra de Victor:**
- **Personal y Familiar** pasó de "alta confianza en general" a tener **8 hipótesis concretas, producto por producto**, con una particularmente fuerte y ya validada dos veces (Droguería → Salud).
- **Movilidad** mejora: la combinación RANGO_SALARIAL + CIUDAD_AFILIADO (para Moto específicamente) es más defendible que la ciudad sola que teníamos antes.
- **Crédito** y **Hogar** no ganan columnas nuevas, pero ahora tienen la hipótesis repartida entre 2-3 productos específicos de la categoría, en vez de una sola regla genérica.
- **Elegibilidad por edad** (4 productos con dato duro de Chubb) es un tipo de regla nuevo que no habíamos incorporado — hay que decidir si el motor la aplica como filtro previo antes de calcular propensión.

**De las hipótesis de Ana:**
- La más sólida de todo su mensaje es rango salarial → nivel de plan (premium vs. accesible) — coincide con lo que ya sabíamos que `RANGO_SALARIAL` es la columna más completa y confiable de la base.
- La mitad de sus hipótesis (hijos, pareja, familia numerosa, vive solo) dependen de `SEGMENTO_GRUPO_FAMILIAR`, que sigue siendo un código sin diccionario — son usables para el cálculo de similitud interno del motor, pero no se puede confirmar con certeza qué significan.
- **Hay un conflicto real que resolver con Ana antes de construir nada:** su hipótesis de "vivienda propia" no corresponde a lo que la columna `VIVIENDA` mide en realidad. Ver la nota de arriba.
- Confirma, por cuarta vez ya entre distintas fuentes internas (dataset, Victor, Ana), que **Mascotas no tiene ninguna columna propia en la base de 500.000** — pero la Fuente 3 (estadística nacional) le da un punto de partida real que antes no tenía, así que ya no es 100% conversación desde cero.
- **Tenencia de vehículo (carro/moto) sigue sin ningún proxy, interno ni externo** — a diferencia de Mascotas, no se encontró estadística nacional fácilmente aplicable en esta búsqueda. Sigue siendo 100% conversación, a menos que se investigue aparte.

**De la Fuente 3 (estadística nacional externa):**
- Mascotas deja de estar en confianza NULA — pasa a tener una tasa base oficial del DANE (67%) más dos correlatos direccionales aplicables con columnas que ya existen (`RANGO_SALARIAL`, `CIUDAD_AFILIADO`, y `SEGMENTO_GRUPO_FAMILIAR` si se confirma que codifica hijos).
- Importante mantener la jerarquía de la fuente al comunicarlo: el 67% del DANE se puede citar como dato duro; los cruces por estrato e hijos son de un estudio de mercado privado más pequeño y deben presentarse como "sugiere", no como hecho confirmado.
- Su principio de "toda hipótesis se confirma con preguntas antes de recomendar" queda establecido como regla general del documento, no solo de su parte — aplica igual a las hipótesis de la Base Maestra de Victor.