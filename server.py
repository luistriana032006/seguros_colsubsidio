"""Servidor HTTP que expone motor.recomendar() como servicio para el bot de Nicolás.

Solo recibe JSON y devuelve JSON -- no maneja conversación, no guarda sesiones,
no conoce los 11 pasos del bot (ver apuntes/contrato_campos_motor.md).
"""
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import motor

app = FastAPI(title="Motor de recomendación de seguros", version="v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PerfilUsuario(BaseModel):
    id_interno: str
    id_contacto: Optional[str] = None
    necesidad: Literal["salud", "familia", "hogar", "movilidad", "mascotas", "credito"]
    edad: int = Field(ge=18, le=75)
    ciudad: str
    rango_salarial: Literal[
        "menor_smlv", "1_1.5", "1.5_2", "2_2.5", "2.5_3", "3_4",
        "4_6", "6_8", "8_10", "10_20", "20_30", "mayor_30",
    ]
    tipo_vivienda: Literal["propia", "arrendada", "familiar"]
    tiene_dependientes: bool
    num_dependientes: int = Field(ge=0, le=4)
    estado_civil: Literal["soltero", "casado", "union_libre", "divorciado", "viudo"]
    usa_drogueria: bool
    usa_hoteles: bool
    usa_agencias: bool
    tiene_mascota: bool
    tipo_mascota: Optional[str] = None
    tipo_vehiculo: Literal["carro", "moto", "bici", "ninguno"]
    canal: Optional[str] = "whatsapp"


@app.get("/salud")
def salud():
    return {
        "estado": "ok",
        "version": "v1",
        "motor": "activo",
        "pesos": "entrenados" if motor.RUTA_PESOS.exists() else "fallback",
    }


@app.post("/recomendar")
def recomendar(perfil: PerfilUsuario):
    perfil_dict = perfil.model_dump()

    try:
        resultado = motor.recomendar(perfil_dict)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Fallo inesperado del motor: {error}")

    if resultado.get("error") is True:
        raise HTTPException(status_code=422, detail=resultado)

    motor.registrar(perfil_dict, resultado, canal=perfil.canal)
    return resultado


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
