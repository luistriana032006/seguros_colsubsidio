"""Servidor MCP que expone motor.recomendar() como herramienta para un LLM.

No reemplaza server.py -- conviven. server.py es para llamadas HTTP directas;
este es para que un LLM (el bot de Nicolás) invoque la recomendación como tool
call, vía stdio, sin hacer HTTP. Contrato de campos: apuntes/contrato_campos_motor.md.
Cómo conectarlo: apuntes/PARA_NICOLAS.md, sección "Conexión vía MCP".
"""
import asyncio
import json

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

import motor

NOMBRE_HERRAMIENTA = "recomendar_seguro"

ESQUEMA_ENTRADA = {
    "type": "object",
    "properties": {
        "necesidad": {
            "type": "string",
            "enum": ["salud", "familia", "hogar", "movilidad", "mascotas", "credito"],
        },
        "edad": {"type": "integer", "minimum": 18, "maximum": 75},
        "ciudad": {"type": "string"},
        "rango_salarial": {
            "type": "string",
            "enum": [
                "menor_smlv", "1_1.5", "1.5_2", "2_2.5", "2.5_3", "3_4",
                "4_6", "6_8", "8_10", "10_20", "20_30", "mayor_30",
            ],
        },
        "tipo_vivienda": {"type": "string", "enum": ["propia", "arrendada", "familiar"]},
        "tiene_dependientes": {"type": "boolean"},
        "num_dependientes": {"type": "integer", "minimum": 0, "maximum": 4},
        "estado_civil": {
            "type": "string",
            "enum": ["soltero", "casado", "union_libre", "divorciado", "viudo"],
        },
        "usa_drogueria": {"type": "boolean"},
        "usa_hoteles": {"type": "boolean"},
        "usa_agencias": {"type": "boolean"},
        "tiene_mascota": {"type": "boolean"},
        "tipo_mascota": {"type": ["string", "null"], "enum": ["perro", "gato", "otro", None]},
        "tipo_vehiculo": {"type": "string", "enum": ["carro", "moto", "bici", "ninguno"]},
        "id_interno": {"type": "string", "description": "UUID que genera Nicolás"},
        "id_contacto": {
            "type": ["string", "null"],
            "description": "Correo o teléfono; null si todavía no llegó",
        },
    },
    "required": [
        "necesidad", "edad", "ciudad", "rango_salarial", "tipo_vivienda",
        "tiene_dependientes", "num_dependientes", "estado_civil", "usa_drogueria",
        "usa_hoteles", "usa_agencias", "tiene_mascota", "tipo_mascota",
        "tipo_vehiculo", "id_interno", "id_contacto",
    ],
}

app = Server("motor_seguros")


@app.list_tools()
async def listar_herramientas() -> list[types.Tool]:
    return [
        types.Tool(
            name=NOMBRE_HERRAMIENTA,
            description=(
                "Recibe el perfil completo de un usuario y devuelve las 3 mejores "
                "recomendaciones de seguro ordenadas por score. Llama esta herramienta "
                "en el paso 4 del flujo, cuando ya tienes toda la información del usuario."
            ),
            inputSchema=ESQUEMA_ENTRADA,
        )
    ]


@app.call_tool()
async def llamar_herramienta(nombre: str, argumentos: dict) -> list[types.TextContent]:
    if nombre != NOMBRE_HERRAMIENTA:
        raise ValueError(f"Herramienta desconocida: {nombre!r}")

    perfil = dict(argumentos)
    resultado = motor.recomendar(perfil)
    motor.registrar(perfil, resultado, canal="whatsapp")

    return [types.TextContent(type="text", text=json.dumps(resultado, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
