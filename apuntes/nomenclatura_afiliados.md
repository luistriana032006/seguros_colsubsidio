# Nomenclatura de códigos (LAMBDA, SIGMA, BETA, etc.) — aclaración de negocio

> Responde a la duda abierta en [`exploracion_dataset_nuevo.md`](./exploracion_dataset_nuevo.md), sección 2: *"usan códigos en letras griegas sin diccionario de equivalencias"*. Este documento registra la respuesta recibida de negocio/Colsubsidio.

---

## Qué respondió negocio (2026-07-23)

> "Las nomenclaturas corresponden a un proceso de anonimización de la información. Para proteger datos y clasificaciones internas, los nombres los van a encontrar de esta forma (LAMBDA, SIGMA, BETA, etc.). El objetivo de esto es preservar la consistencia de los datos para realizar análisis, agrupaciones y conteos, sin divulgar la clasificación original utilizada por Colsubsidio."

Contexto adicional que dieron sobre qué mide cada columna:

| Columna | Qué representa (confirmado por negocio) |
|---|---|
| `CATEGORIA` | Categoría del afiliado dentro del sistema de subsidio familiar |
| `SEGMENTO_GRUPO_FAMILIAR` | Clasifica la composición del hogar / estructura familiar del afiliado |
| `SEGMENTO_POBLACIONAL` | Segmentación individual del afiliado, construida a partir de ingresos, edad y PAC |
| `PIRAMIDE_NUEVA` | Clasifica la empresa aportante dentro de la pirámide empresarial de Colsubsidio |

## Qué sabemos ahora vs. qué seguimos sin saber

- **Sabemos (nuevo):** el propósito de negocio de cada *columna* — para qué se usa esa segmentación en general.
- **Seguimos sin saber:** el mapeo específico *código → significado* dentro de cada columna. No sabemos qué distingue a alguien en `LAMBDA` de alguien en `RHO` dentro de `SEGMENTO_GRUPO_FAMILIAR`, ni cuál código de `CATEGORIA` es "mejor" o "más alto" que otro.
- Esto **no es un dato pendiente de pedir** — es anonimización intencional. Negocio no va a entregar el diccionario código→significado porque eso divulgaría la clasificación interna real. No insistir en pedirlo.
- Lo que sí sostiene un análisis: **mismo código = mismo grupo real** en todo el dataset. Sirve para agrupar, contar y comparar segmentos entre sí (p. ej. "el segmento X usa droguería más que el segmento Y"), aunque no sepamos cómo se llama X en el sistema original de Colsubsidio.

## Impacto en el análisis existente

Esto **no resuelve** el hueco transversal de la sección 6 de `exploracion_dataset_nuevo.md` (seguimos sin poder etiquetar cada código con su significado exacto), pero sí sube el nivel de confianza de que:
- `SEGMENTO_GRUPO_FAMILIAR` es un proxy válido para preguntas de **Hogar** y **Personal y Familiar** (mide composición del hogar, no otra cosa).
- `SEGMENTO_POBLACIONAL` es un proxy válido para preguntas de **Crédito** (está construido con ingresos, edad y PAC — variables típicas de scoring).
- `PIRAMIDE_NUEVA` describe la *empresa*, no al afiliado directamente — útil si el análisis se hace a nivel de empresa aportante, menos directo para perfilar personas.
- `CATEGORIA` sigue siendo la más ambigua de las cuatro: solo sabemos que es "categoría dentro del sistema de subsidio familiar", sin más detalle de qué distingue a un nivel de otro.

Ver actualización correspondiente en `exploracion_dataset_nuevo.md` (sección 2, 4 y 6) y en el artifact publicado.

## Pendiente

- Tipos de seguro que ofrece Colsubsidio (Mascotas, Hogar, Crédito, Movilidad, Personal y Familiar según el Word del reto) — el usuario los va a pasar aparte para poder cruzarlos con estas columnas.
