# Contrato de campos — Motor de Recomendación

## Quién llena estos campos
Nicolás los recoge en los 11 pasos del bot conversacional y los envía al motor completos.
El motor no acepta perfiles incompletos — rechaza con error explícito si falta algo.

## Campos obligatorios

| Campo | Tipo | Valores válidos | Paso donde se recoge |
|---|---|---|---|
| necesidad | string | salud, familia, hogar, movilidad, mascotas, credito | Paso 3 — S3_DIAGNOSTICO |
| edad | integer | 18 a 75 | Paso 1 — S1_INGRESO o Paso 4 |
| ciudad | string | cualquier string no vacío | Paso 1 — S1_INGRESO |
| rango_salarial | string | menor_smlv, 1_1.5, 1.5_2, 2_2.5, 2.5_3, 3_4, 4_6, 6_8, 8_10, 10_20, 20_30, mayor_30 | Paso 4 — S4_PERFILAMIENTO |
| tipo_vivienda | string | propia, arrendada, familiar | Paso 4 — S4_PERFILAMIENTO |
| tiene_dependientes | boolean | true, false | Paso 4 — S4_PERFILAMIENTO |
| num_dependientes | integer | 0 a 4 | Paso 4 — S4_PERFILAMIENTO |
| estado_civil | string | soltero, casado, union_libre, divorciado, viudo | Paso 4 — S4_PERFILAMIENTO |
| usa_drogueria | boolean | true, false | Paso 4 — S4_PERFILAMIENTO |
| usa_hoteles | boolean | true, false | Paso 4 — S4_PERFILAMIENTO |
| usa_agencias | boolean | true, false | Paso 4 — S4_PERFILAMIENTO |
| tiene_mascota | boolean | true, false | Paso 4 — S4_PERFILAMIENTO |
| tipo_mascota | string o null | perro, gato, otro — null si tiene_mascota es False | Paso 4 — S4_PERFILAMIENTO |
| tipo_vehiculo | string | carro, moto, bici, ninguno | Paso 4 — S4_PERFILAMIENTO |

## Regla de num_dependientes
Si tiene_dependientes es False → num_dependientes debe ser 0.
Si tiene_dependientes es True → num_dependientes debe ser entre 1 y 4.

## Regla de tipo_mascota
Si tiene_mascota es False → tipo_mascota debe ser null.
Si tiene_mascota es True → tipo_mascota debe ser "perro", "gato" o "otro".

## Qué pasa si llega incompleto
El motor devuelve un JSON de error con:
- campos_faltantes: lista de campos que no llegaron
- campos_invalidos: lista de campos con valor fuera de rango o tipo incorrecto
- mensaje: texto explicando qué corregir

El motor nunca explota silenciosamente — siempre responde algo.

## Lo que decide el motor
El motor recibe estos campos y devuelve:
- producto_principal: ID del producto recomendado
- producto_alternativa: ID del segundo producto o null
- categoria: categoría del producto
- score: float entre 0 y 1
- hipotesis_activadas: lista de hipótesis que se dispararon
- razon: texto explicando la recomendación
- confianza: alta, media o baja

## Lo que NO decide el motor
- No conduce la conversación
- No maneja objeciones
- No captura consentimientos
- No genera enlaces de compra
- No decide si el usuario es afiliado o no
Todo eso es responsabilidad del bot de Nicolás.
