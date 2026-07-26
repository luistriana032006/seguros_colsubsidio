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
Ya no es un producto único — son las 3 mejores opciones, ordenadas por score:
{
  "recomendaciones": [
    {
      "posicion": 1,
      "producto_id": "ASMED-01",
      "nombre": "Asistencias médicas familiares",
      "categoria": "Personal y Familiar",
      "score": 0.89,
      "confianza": "alta",
      "razon": "drogueria_activa. Score total: 0.89."
    },
    {
      "posicion": 2,
      "producto_id": "SALUD-01",
      "nombre": "Póliza de salud Colsubsidio",
      "categoria": "Personal y Familiar",
      "score": 0.71,
      "confianza": "alta",
      "razon": "drogueria_activa. Score total: 0.71."
    },
    {
      "posicion": 3,
      "producto_id": "VIDA-01",
      "nombre": "Seguro de vida Colsubsidio",
      "categoria": "Personal y Familiar",
      "score": 0.0,
      "confianza": "baja",
      "razon": "Producto de respaldo general -- no hay señal suficiente en tu perfil para la necesidad 'salud' como para llenar las 3 posiciones."
    }
  ],
  "hipotesis_activadas": ["drogueria_activa"],
  "necesidad": "salud"
}

Siempre son exactamente 3 posiciones. Si no hay suficiente señal real, las que
faltan se rellenan con productos de respaldo de otras categorías — vienen con
`"score": 0.0` y `"confianza": "baja"`, para que sepas distinguirlas de una
recomendación real.

## Qué haces tú con eso
- recomendaciones[0] (posición 1) → la presentas en el paso 5 como primera opción
- recomendaciones[1] y [2] → segunda y tercera opción, si el usuario quiere ver más
- razon de cada una → úsala para explicarle al usuario por qué le recomiendas ese seguro
- confianza → si la de posición 1 es "baja" considera hacer una pregunta adicional antes de presentar
- necesidad → viene de vuelta tal cual la mandaste, útil para loggear/depurar en tu lado

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

## Conexión vía MCP (para el LLM)

### Qué es
El motor también está disponible como herramienta MCP para que tu LLM
lo llame directamente sin hacer HTTP. El LLM detecta cuándo tiene
el perfil completo y llama la herramienta solo.

### Cómo configurarlo en tu proyecto
Crea o actualiza tu .mcp.json con esto:

{
  "mcpServers": {
    "motor_seguros": {
      "command": "python3",
      "args": ["ruta/absoluta/a/mcp_server.py"],
      "description": "Motor de recomendación de seguros — devuelve las 3 mejores opciones para un perfil de usuario"
    }
  }
}

Reemplaza "ruta/absoluta/a/mcp_server.py" con la ruta real en tu máquina.

### La herramienta disponible
Nombre: recomendar_seguro
Cuándo usarla: en el paso 4, cuando ya tienes el perfil completo del usuario
Qué devuelve: las 3 mejores recomendaciones de seguro con score, razón y confianza

### Qué le dices al LLM en el system prompt
Agrega esto a tu system prompt:

"Tienes acceso a la herramienta recomendar_seguro. Úsala en el paso 4
del flujo, cuando el usuario haya respondido todas las preguntas de
perfilamiento. Nunca inventes una recomendación — siempre llama la
herramienta primero y usa su respuesta para presentarle las opciones al usuario."

### Ejemplo de lo que devuelve la herramienta
{
  "recomendaciones": [
    {
      "posicion": 1,
      "producto_id": "ASMED-01",
      "nombre": "Asistencias médicas familiares",
      "categoria": "Personal y Familiar",
      "score": 0.89,
      "confianza": "alta",
      "razon": "El usuario usa droguería frecuentemente, señal de interés en cobertura de salud"
    },
    {
      "posicion": 2,
      "producto_id": "SALUD-01",
      "nombre": "Póliza de Salud",
      "categoria": "Personal y Familiar", 
      "score": 0.71,
      "confianza": "alta",
      "razon": "..."
    },
    {
      "posicion": 3,
      "producto_id": "VIDA-01",
      "nombre": "Seguro de Vida",
      "categoria": "Personal y Familiar",
      "score": 0.45,
      "confianza": "media",
      "razon": "..."
    }
  ],
  "hipotesis_activadas": ["drogueria_activa"],
  "necesidad": "salud"
}
