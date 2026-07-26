# Para Nicolás — Cómo conectarte al motor

## El motor ya está corriendo
Levántalo así:
python3 server.py
Queda disponible en: http://127.0.0.1:8000

## Un solo endpoint que te importa
POST http://127.0.0.1:8000/recomendar

## Cuándo llamarlo
En el paso 4 (S4_PERFILAMIENTO), cuando ya tienes la respuesta del usuario
y construiste el perfil completo. Antes de ese momento no llames al motor.

## Qué me mandas
JSON con estos campos obligatorios — todos deben llegar, ninguno puede ser null
salvo los que dicen "opcional":

{
  "id_interno": "uuid que generas tú",
  "id_contacto": "correo o teléfono — opcional, null si no llegó aún",
  "necesidad": "salud|familia|hogar|movilidad|mascotas|credito",
  "edad": 34,
  "ciudad": "Bogotá",
  "rango_salarial": "menor_smlv|1_1.5|1.5_2|2_2.5|2.5_3|3_4|4_6|6_8|8_10|10_20|20_30|mayor_30",
  "tipo_vivienda": "propia|arrendada|familiar",
  "tiene_dependientes": true,
  "num_dependientes": 2,
  "estado_civil": "soltero|casado|union_libre|divorciado|viudo",
  "usa_drogueria": false,
  "usa_hoteles": false,
  "usa_agencias": false,
  "tiene_mascota": false,
  "tipo_mascota": null,
  "tipo_vehiculo": "carro|moto|bici|ninguno",
  "canal": "whatsapp"
}

## Qué te devuelvo yo
{
  "producto_principal": "ASMED-01",
  "producto_alternativa": "SALUD-01",
  "categoria": "Personal y Familiar",
  "score": 0.89,
  "hipotesis_activadas": ["drogueria_activa"],
  "razon": "El usuario usa droguería frecuentemente, señal de interés en cobertura de salud",
  "confianza": "alta"
}

## Qué haces tú con eso
- producto_principal → lo presentas en el paso 5 como primera opción
- producto_alternativa → lo presentas como segunda opción si existe
- razon → úsala para explicarle al usuario por qué le recomiendas ese seguro
- confianza → si es "baja" considera hacer una pregunta adicional antes de presentar

## Si mando algo mal qué pasa
Te devuelvo HTTP 422 con el detalle exacto de qué campo está mal o falta.
Ejemplo:
{
  "detail": [
    {
      "loc": ["body", "edad"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

## Si el servidor no responde
GET http://127.0.0.1:8000/salud
Debe devolver: {"estado":"ok","version":"v1","motor":"activo","pesos":"entrenados"}
Si no responde, el servidor no está corriendo — avísame.

## Documentación interactiva
http://127.0.0.1:8000/docs
Puedes probar el endpoint directamente desde el navegador sin escribir código.

## Reglas que no se rompen
- Mándame el perfil completo — si falta un campo te rechazo con 422
- No me llames antes del paso 4 — necesito que el usuario ya haya respondido sus preguntas
- El campo canal siempre debe ser "whatsapp" cuando viene de tu bot
- Si el usuario no dio su correo ni teléfono todavía, manda id_contacto: null — no inventes un valor

## Contacto
Cualquier duda sobre el contrato → Luis
