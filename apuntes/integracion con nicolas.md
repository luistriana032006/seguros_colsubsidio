# Integración con Nicolás (bot conversacional)

Documento de trabajo personal, no del equipo — para que yo sepa qué necesito pedirle a Nicolás, qué necesito confirmarle, y qué reglas del motor le afectan a él directamente aunque el motor sea mío. Se actualiza cada vez que algo del lado del motor tenga una consecuencia del lado del bot.

---

## Estado del contrato

**Mi lado (definido, estable):** el esquema de entrada que necesito recibir de su bot.

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

**Su lado:** sin definir todavía. Cuando lo defina, ajustar con capa de traducción, no reescribiendo el motor.

**Objeto de salida que yo le entrego a él (datos, nunca texto redactado):**

```json
{
  "producto_id": "...",
  "categoria_top": "...",
  "categoria_secundaria": "...",
  "score_propension": 0.0,
  "confianza": "alta|media|baja",
  "reglas_activadas": ["..."],
  "alternativas_descartadas": ["..."],
  "requiere_escalamiento": false,
  "fuentes": ["..."],
  "estado_dato": "verificado|supuesto_demo|no_disponible"
}
```

---

## Reglas que le afectan a él directamente, aunque el motor sea mío

### 1. Debe mostrar `categoria_top` Y `categoria_secundaria` siempre juntas — no solo la principal

**Por qué:** al correr el motor real sobre las 500.000 filas (24 julio 2026), Mascotas gana como `categoria_top` en 0 de 500.000 filas — pero aparece como `categoria_secundaria` en el 69.5% de los casos. No es un error del motor: Mascotas es la única categoría sin columna propia en el dataset, así que compite en desventaja real contra categorías con dato interno fuerte como Crédito. Si su bot solo contempla ofrecer la categoría principal, **Mascotas no se le ofrece a nadie**, a pesar de que la mayoría de personas sí tiene alguna señal real hacia esa categoría como segunda opción.

**Qué necesito confirmarle:** que su diseño de conversación ya contempla mostrar las dos categorías, no solo prepararse para agregarlo después.

### 2. Nunca debe mostrarle al usuario los códigos internos (LAMBDA, SIGMA, etc.)

`reglas_activadas` puede traer cosas como `SEGMENTO_GRUPO_FAMILIAR=LAMBDA` — eso sirve para el motor (calcular similitud), pero no significa nada legible fuera de Colsubsidio. Si su bot redacta la explicación directamente desde ese campo sin filtrar, se le va a colar un código sin sentido al usuario final.

**Qué necesito confirmarle:** que su capa de redacción (Mistral) tiene instrucción explícita de nunca reproducir esos códigos tal cual, solo las columnas legibles (edad, salario, droguería, etc.).

### 3. `requiere_escalamiento = true` necesita un manejo explícito de su parte

Hay perfiles sin ninguna señal real donde el motor no fuerza ninguna categoría — devuelve `categoria_top = "Sin señal suficiente"` y `requiere_escalamiento = true`. Su bot necesita saber qué hacer en ese caso (¿pedir más información en la conversación? ¿derivar a humano/canal alterno?), no asumir que siempre va a recibir una categoría con la que trabajar.

**Por qué esto importa más de lo que parece:** dentro de los 500.000 afiliados este caso es raro (0.7%, ~1 de cada 142 — un patrón específico ligado a `CATEGORIA=MU`/`SEGMENTO_POBLACIONAL=OMEGA`, probablemente gente sin ingreso propio registrado). No vale la pena diseñar nada especial para ese patrón puntual, es demasiado pequeño. **Pero para usuarios NO afiliados esta misma ruta se va a activar con más frecuencia por una razón distinta:** alguien sin registro en la base depende 100% de lo que la conversación capture, así que va a pasar por un estado "sin señal" cada vez que empiece una conversación nueva, antes de que el bot alcance a preguntar lo suficiente. La prioridad no es un manejo especial para el patrón MU/OMEGA — es que la ruta genérica de `requiere_escalamiento` esté bien resuelta desde el principio, porque un no afiliado la va a pisar seguido.

### 4. A veces va a necesitar pedir edad exacta, no solo el rango

Tres productos de Personal y Familiar (accidentes personales, accidentes personales digital, oncológico) tienen límite real de edad (18 a 65-69 según el producto) más preciso que los rangos que maneja el motor. Cuando el perfil cae en el rango "menor de 19" o "mayor de 55" y el producto candidato es uno de esos tres, la salida trae `pendiente_confirmacion_edad = true`.

**Qué necesito de su bot:** cuando reciba ese flag, debe hacer una pregunta puntual de edad exacta antes de confirmar ese producto específico — no como pregunta general al inicio de la conversación, solo cuando surge este caso concreto. Para el resto de productos/rangos no hace falta preguntar nada de esto.

### 5. `categoria_interes_declarada` ya no es un campo genérico — tiene un uso concreto y crítico

Al construir el pendiente #6, se encontró que 6 productos (INCENDIO-DEUDOR-01, CARRO-01, y los 4 con elegibilidad dura de Chubb: AP-CHUBB-01, APDIG-CHUBB-01, ONCO-CHUBB-01, URB-CHUBB-01) **nunca pueden salir del motor de propensión** — no hay columna en la base que diga si alguien tiene crédito hipotecario, vehículo, o quiere específicamente uno de estos productos de Chubb. Solo se pueden ofrecer si la persona lo dice directamente.

**Qué necesito de su bot:** cuando en la conversación la persona mencione explícitamente uno de estos 6 productos o algo que claramente los implique ("tengo una hipoteca", "quiero asegurar mi carro", "necesito algo para cáncer"), debe llenar `categoria_interes_declarada` con el valor correspondiente. Sin eso, esos 6 productos **nunca van a aparecer** en ninguna recomendación, sin importar qué tan bueno sea el perfil de la persona para ellos — el motor no tiene otra forma de llegar a ellos.

### 6. Campo opcional nuevo: `producto_interes_declarado`

Se agregó junto a `categoria_interes_declarada` — permite apuntar a un producto específico de declaración directa (ej. ONCO-CHUBB-01) en vez de solo a la categoría. Opcional, no rompe nada si no lo manda. Sin él, declarar interés en "Personal y Familiar" devuelve varios productos de declaración directa a la vez en vez de uno solo.

### 7. `segmento_grupo_familiar` — confirmado que NO hace falta pedirlo

Se probó explícitamente: sin ese campo, la función reproduce el motor de lote en 93.10% de los casos reales — ese es el número esperado en producción, no un caso degradado. Es un código interno de Colsubsidio que ni el bot ni la persona pueden conocer. No hace falta agregarlo al contrato.

---

## Pendiente de resolver con él (no solo informarle, decidir juntos)

- [ ] Su esquema de entrada — nombres de campo exactos que su bot va a extraer
- [ ] Qué pasa en la conversación cuando `requiere_escalamiento = true`
- [ ] Cómo su bot va a presentar `categoria_secundaria` sin que se sienta como "premio de consolación" — esto es más de él/Ana que mío, pero afecta si vale la pena que el motor siga calculando la secundaria con el mismo detalle que la principal

---

## Bitácora

**24 julio 2026:** creado el documento. Primera regla documentada: mostrar top + secundaria siempre juntas, a raíz del hallazgo de que Mascotas nunca gana como principal.