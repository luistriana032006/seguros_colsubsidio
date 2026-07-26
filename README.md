# Asesor de Seguros — Motor de Recomendación

## Estado
Reseteo completo — 2026-07-25. Nuevo marco desde cero.

## Qué es
Motor de recomendación de seguros que:
1. Recibe el perfil de un usuario (histórico o nuevo)
2. Detecta patrones estadísticos basados en hipótesis validadas
3. Recomienda el producto más adecuado con razón explícita

## Dos fuentes de usuarios
- **Usuario conocido**: perfil viene del dataset histórico
- **Usuario nuevo**: perfil viene del bot conversacional (contrato con Nicolás)

## Contrato de datos (campos que llegan del bot)
| Campo | Tipo | Valores posibles |
|---|---|---|
| id_interno | string | UUID generado por nosotros |
| id_contacto | string | correo o teléfono (el primero que llegue) |
| edad | integer | años cumplidos |
| ciudad | string | ciudad de residencia |
| tipo_documento | string | CC, CE, PA |
| rango_salarial | string | menor_smlv, 1_1.5, 1.5_2, 2_2.5, 2.5_3, 3_4, 4_6, 6_8, 8_10, 10_20, 20_30, mayor_30 |
| tipo_vivienda | string | propia, arrendada, familiar |
| tiene_dependientes | boolean | true, false |
| num_dependientes | integer | 0 si no tiene |
| estado_civil | string | soltero, casado, union_libre, divorciado, viudo |
| usa_drogueria | boolean | true, false |
| usa_hoteles | boolean | true, false |
| usa_agencias | boolean | true, false |
| tiene_mascota | boolean | true, false |
| tipo_mascota | string | perro, gato, otro, null |
| tipo_vehiculo | string | carro, moto, bici, ninguno |
| producto_comprado | string | ID del producto — null para usuarios nuevos |

## Primary key
Compuesta: (id_interno, id_contacto)
id_contacto puede ser null en el primer registro.

## Estructura del proyecto

├── data/
│ ├── raw/ Dataset original (no tocar)
│ ├── sintetico/ Dataset de 5.000 registros generado por script
│ ├── catalogo/ Catálogo de 24 productos
│ └── modelos/ Modelos entrenados serializados
├── scripts/ Scripts de generación y entrenamiento
├── apuntes/
│ └── deprecados/ Documentación del marco anterior
└── README.md


## Regla crítica
Las hipótesis las escribe un humano. El motor las consume, no las inventa.
