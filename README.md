# Motor de recomendación de seguros — Colsubsidio × 30X

Recibe el perfil de una persona y devuelve **qué seguro recomendarle, con qué producto
específico y por qué**. Devuelve datos estructurados (JSON), no texto redactado: la
redacción al usuario final la hace el bot conversacional, no este motor.

## Correr la demo (menos de 2 minutos)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en `http://localhost:8501`. Trae **5 casos de prueba con un clic** y un
formulario libre para armar cualquier perfil.

Sin instalar nada extra, para ver los 5 casos por consola:

```bash
python3 motor.py
```

## Usarlo como librería

```python
from motor import recomendar

recomendar({
    "rango_edad": "46 a 55 años",
    "rango_salarial": "Entre 8 y 10 SMLV",
    "usa_drogueria": True,
})
# -> {"producto_top": "SALUD-01", "categoria_top": "Personal y Familiar",
#     "score_propension": 0.7, "reglas_activadas": [...], ...}
```

Todos los campos son opcionales. Si falta un dato, **la regla que lo usa se omite**:
no suma, no resta, no cuenta como cero. Un perfil vacío devuelve
`"Sin señal suficiente"` con `requiere_escalamiento = true`, nunca una recomendación
inventada.

### Entrada (contrato con el bot)

`afiliado`, `genero`, `rango_edad`, `rango_salarial`, `ciudad`, `usa_drogueria`,
`tiene_vehiculo`, `tiene_mascota`, `viaja_frecuente`, `tiene_dependientes`,
`estado_civil`, `vive_solo`, `tiene_vivienda_propia`, `categoria_interes_declarada`.

Dos campos extra, opcionales: `producto_interes_declarado` y
`segmento_grupo_familiar` (este último solo si la persona ya está en la base de afiliados).

### Salida

`producto_top` / `producto_id`, `categoria_top`, `categoria_secundaria`,
`score_propension`, `confianza`, `reglas_activadas`, `alternativas_descartadas`,
`productos_alternativos`, `producto_indiferenciado`, `requiere_escalamiento`,
`fuentes`, `estado_dato`, `pendiente_confirmacion_edad`, `scores_por_categoria`,
`reglas_omitidas`, `via`.

## Cómo decide

1. **Categoría de interés declarada** → si la persona pide una categoría, se le ofrece
   directo el producto de *declaración directa* correspondiente, sin pasar por el ranking.
2. **Score de propensión** por las 5 categorías oficiales (Crédito, Personal y Familiar,
   Hogar, Movilidad, Mascotas), con las reglas y pesos ya validados sobre 500.000 afiliados.
3. **Ranking de producto** dentro de la categoría ganadora. Si ninguno cumple su hipótesis,
   se usa el producto de respaldo de esa categoría y se marca `producto_indiferenciado`.
4. **Elegibilidad dura**: cuando el bucket de edad es más ancho que el límite real de la
   aseguradora, marca `pendiente_confirmacion_edad` en vez de inventar certeza.

Toda recomendación viene con `reglas_activadas`: las reglas exactas que se dispararon.
Nada de caja negra.

## Verificación

La función reproduce la corrida en lote sobre las 500.000 filas:

| Escenario | Paridad con el lote |
|---|---|
| Perfil de afiliado (con `segmento_grupo_familiar`) | **100 %** |
| Perfil externo (sin ese dato) | **93,10 %** |

La diferencia del 6,90 % es una sola regla que no se puede evaluar sin ese campo
(`SEGMENTO_GRUPO_FAMILIAR`, código interno de Colsubsidio) — está declarada en
`reglas_omitidas` de cada respuesta, no es una divergencia silenciosa.

## Estructura

```
├── motor.py            recomendar(perfil) — la función que consume el bot
├── app.py              demo Streamlit
├── data/
│   ├── raw/            el .xlsx original (fuente, nunca se modifica)
│   ├── processed/      los CSV derivados del pipeline de lote
│   └── catalogo/       24 productos + reglas estructuradas
├── scripts/            los 4 scripts de lote (no hacen falta para correr la demo)
└── apuntes/            todas las decisiones y su razonamiento
```

`motor.py` y `app.py` viven en la raíz a propósito: `streamlit run app.py` sin prefijos.

Los scripts de lote se corren **desde la raíz** y solo hacen falta para regenerar los datos:

```bash
python3 scripts/limpieza_rango_salarial.py   # .xlsx  → RANGO_SALARIAL_LIMPIO.csv
python3 scripts/etiquetado_hipotesis.py      # → ETIQUETADO_V3.csv (score por categoría)
python3 scripts/estructurar_hipotesis.py     # .md    → hipotesis_producto_estructuradas.csv
python3 scripts/emparejar_producto.py        # → PRODUCTO_V2.csv (producto específico)
```
