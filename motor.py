"""Motor de recomendación de seguros.

recomendar(perfil) -> dict, según el contrato de datos de apuntes/Hipotesis_Generales_Seguros.md
y el catálogo de data/catalogo/catalogo_productos.csv.

Las hipótesis SI/ENTONCES (qué producto gana con qué condición) son reglas de negocio dadas
por el equipo -- no hay columna en el catálogo que las codifique, así que esos IDs sí aparecen
como literales en HIPOTESIS más abajo. Lo que el motor nunca hardcodea es el resto de metadata
(categoría, si el precio está verificado, cuántos campos del producto están verificados): eso
siempre se lee del catálogo. Al importar el módulo se valida además que todo ID mencionado en
HIPOTESIS/ELEGIBILIDAD_DURA/PRODUCTOS_RESPALDO exista realmente en el catálogo.
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent
RUTA_CATALOGO = RAIZ / "data" / "catalogo" / "catalogo_productos.csv"
RUTA_DB = RAIZ / "data" / "motor.db"
RUTA_PESOS = RAIZ / "data" / "modelos" / "pesos_hipotesis.json"

# Pesos fijos originales (scripts/entrenar_motor.py calcula estos mismos nombres de
# necesidad/clave a partir de data/sintetico/datos_sinteticos.csv). Sirven de fallback
# si data/modelos/pesos_hipotesis.json no existe o no se puede leer.
PESOS_FALLBACK = {
    "salud": {"drogueria_activa": 0.8, "tiene_dependientes_salud": 0.3},
    "familia": {
        "ahorro_mediano_plazo": 0.9, "salario_bajo_familia": 0.7, "mayor_55": 0.8,
        "salario_bajo_medio_familia": 0.5, "tiene_dependientes_familia": 0.6,
    },
    "hogar": {"salario_alto_hogar": 0.8, "salario_bajo_medio_hogar": 0.7, "vivienda_propia": 0.4},
    "movilidad": {
        "periferia_salario_bajo": 0.9, "edad_joven_bici": 0.6,
        "vehiculo_moto": 0.5, "vehiculo_bici": 0.4,
    },
    "mascotas": {"tiene_mascota": 0.9, "salario_bajo_medio_mascota": 0.3, "bucaramanga_mascota": -0.2},
    "credito": {"salario_medio_bajo_credito": 0.8},
}


def _cargar_pesos():
    """Lee data/modelos/pesos_hipotesis.json; si falta o está incompleto, usa PESOS_FALLBACK."""
    if not RUTA_PESOS.exists():
        return PESOS_FALLBACK

    try:
        with open(RUTA_PESOS, "r", encoding="utf-8") as archivo:
            entrenado = json.load(archivo)["pesos"]
        return {
            necesidad: {clave: entrenado[necesidad][clave]["peso"] for clave in claves}
            for necesidad, claves in PESOS_FALLBACK.items()
        }
    except Exception:
        return PESOS_FALLBACK


PESOS = _cargar_pesos()

CATALOGO = pd.read_csv(RUTA_CATALOGO).set_index("producto_id")
COLUMNAS_ESTADO = [c for c in CATALOGO.columns if c.startswith("estado_")]

RANGO_TIERS = {
    "menor_smlv": "bajo", "1_1.5": "bajo", "1.5_2": "bajo",
    "2_2.5": "medio", "2.5_3": "medio", "3_4": "medio",
    "4_6": "medio_alto", "6_8": "medio_alto",
    "8_10": "alto", "10_20": "alto", "20_30": "alto", "mayor_30": "alto",
}

MUNICIPIOS_PERIFERICOS = {"Soacha", "Mosquera", "Zipaquirá", "Funza"}

UMBRAL_RESPALDO = 0.3
UMBRAL_ALTA = 0.7
UMBRAL_MEDIA = 0.4

# --- CAPA 1: elegibilidad dura (dato real de Chubb, filtro antes de calcular propensión) ---
ELEGIBILIDAD_DURA = {
    "AP-CHUBB-01": (18, 65),
    "APDIG-CHUBB-01": (18, 65),
    "ONCO-CHUBB-01": (18, 64),
}

# Nunca compiten por propensión (declaración directa / sin hipótesis estructurable).
PRODUCTOS_EXCLUIDOS_SIEMPRE = {"INCENDIO-DEUDOR-01", "CARRO-01", "DESEMP-01", "SOAT-01", "VIAJE-01"}

# Productos de respaldo por necesidad, si ningún candidato supera UMBRAL_RESPALDO.
PRODUCTOS_RESPALDO = {
    "salud": "SALUD-01",
    "familia": "VIDA-01",
    "hogar": "HOGAR-01",
    "movilidad": "BICI-01",
    "mascotas": "PET-SEG-01",
    "credito": "DEUDOR-VIDA-01",
}

# --- Validación de entrada (apuntes/contrato_campos_motor.md) ---
CAMPOS_OBLIGATORIOS = [
    "necesidad", "edad", "ciudad", "rango_salarial", "tipo_vivienda",
    "tiene_dependientes", "num_dependientes", "estado_civil", "usa_drogueria",
    "usa_hoteles", "usa_agencias", "tiene_mascota", "tipo_mascota", "tipo_vehiculo",
]

NECESIDADES_VALIDAS = list(PRODUCTOS_RESPALDO)
TIPOS_VIVIENDA_VALIDOS = ["propia", "arrendada", "familiar"]
ESTADOS_CIVILES_VALIDOS = ["soltero", "casado", "union_libre", "divorciado", "viudo"]
TIPOS_MASCOTA_VALIDOS = ["perro", "gato", "otro"]
TIPOS_VEHICULO_VALIDOS = ["carro", "moto", "bici", "ninguno"]

# --- CAPA 2: hipótesis de propensión por necesidad (delta = peso entrenado, PESOS[necesidad][clave]) ---
HIPOTESIS = {
    "salud": [
        {"cond": lambda p: p.get("usa_drogueria") is True, "delta": PESOS["salud"]["drogueria_activa"],
         "candidatos": ["SALUD-01", "ASMED-01"], "desc": "usa_drogueria=True"},
        {"cond": lambda p: p.get("tiene_dependientes") is True,
         "delta": PESOS["salud"]["tiene_dependientes_salud"],
         "candidatos": ["ASMED-01"], "desc": "tiene_dependientes=True"},
    ],
    "familia": [
        {"cond": lambda p: RANGO_TIERS.get(p.get("rango_salarial")) == "medio_alto"
                            and p.get("edad") is not None and 36 <= p["edad"] <= 55,
         "delta": PESOS["familia"]["ahorro_mediano_plazo"], "candidatos": ["VIDAAH-01"],
         "desc": "rango_salarial en Medio_alto y edad entre 36 y 55"},
        {"cond": lambda p: RANGO_TIERS.get(p.get("rango_salarial")) == "bajo",
         "delta": PESOS["familia"]["salario_bajo_familia"],
         "candidatos": ["APEXEQ-PAL-01"], "desc": "rango_salarial en Bajo"},
        {"cond": lambda p: p.get("edad") is not None and p["edad"] >= 55,
         "delta": PESOS["familia"]["mayor_55"],
         "candidatos": ["EXEQ-01"], "desc": "edad >= 55"},
        {"cond": lambda p: RANGO_TIERS.get(p.get("rango_salarial")) in ("bajo", "medio"),
         "delta": PESOS["familia"]["salario_bajo_medio_familia"],
         "candidatos": ["ASMULT-01"], "desc": "rango_salarial en Bajo o Medio"},
        {"cond": lambda p: p.get("tiene_dependientes") is True,
         "delta": PESOS["familia"]["tiene_dependientes_familia"],
         "candidatos": ["VIDA-01"], "desc": "tiene_dependientes=True"},
    ],
    "hogar": [
        {"cond": lambda p: RANGO_TIERS.get(p.get("rango_salarial")) in ("medio_alto", "alto"),
         "delta": PESOS["hogar"]["salario_alto_hogar"],
         "candidatos": ["HOGAR-01"], "desc": "rango_salarial en Medio_alto o Alto"},
        {"cond": lambda p: RANGO_TIERS.get(p.get("rango_salarial")) in ("bajo", "medio"),
         "delta": PESOS["hogar"]["salario_bajo_medio_hogar"],
         "candidatos": ["ARRENDA-01"], "desc": "rango_salarial en Bajo o Medio"},
        {"cond": lambda p: p.get("tipo_vivienda") == "propia",
         "delta": PESOS["hogar"]["vivienda_propia"],
         "candidatos": ["HOGAR-01"], "desc": "tipo_vivienda=propia"},
    ],
    "movilidad": [
        {"cond": lambda p: RANGO_TIERS.get(p.get("rango_salarial")) in ("bajo", "medio")
                            and p.get("ciudad") in MUNICIPIOS_PERIFERICOS,
         "delta": PESOS["movilidad"]["periferia_salario_bajo"], "candidatos": ["MOTO-01"],
         "desc": "rango_salarial en Bajo/Medio y ciudad periférica (Soacha/Mosquera/Zipaquirá/Funza)"},
        {"cond": lambda p: p.get("edad") is not None and 20 <= p["edad"] <= 35,
         "delta": PESOS["movilidad"]["edad_joven_bici"],
         "candidatos": ["BICI-01"], "desc": "edad entre 20 y 35"},
        {"cond": lambda p: p.get("tipo_vehiculo") == "moto",
         "delta": PESOS["movilidad"]["vehiculo_moto"],
         "candidatos": ["MOTO-01"], "desc": "tipo_vehiculo=moto"},
        {"cond": lambda p: p.get("tipo_vehiculo") == "bici",
         "delta": PESOS["movilidad"]["vehiculo_bici"],
         "candidatos": ["BICI-01"], "desc": "tipo_vehiculo=bici"},
    ],
    "mascotas": [
        {"cond": lambda p: p.get("tiene_mascota") is True,
         "delta": PESOS["mascotas"]["tiene_mascota"],
         "candidatos": ["PET-SEG-01"], "desc": "tiene_mascota=True"},
        {"cond": lambda p: RANGO_TIERS.get(p.get("rango_salarial")) in ("bajo", "medio"),
         "delta": PESOS["mascotas"]["salario_bajo_medio_mascota"],
         "candidatos": ["PET-PREP-01"], "desc": "rango_salarial en Bajo o Medio"},
    ],
    "credito": [
        {"cond": lambda p: RANGO_TIERS.get(p.get("rango_salarial")) in ("medio", "bajo"),
         "delta": PESOS["credito"]["salario_medio_bajo_credito"],
         "candidatos": ["DEUDOR-VIDA-01"], "desc": "rango_salarial en Medio o Bajo"},
    ],
}


def _ids_referenciados():
    ids = set(ELEGIBILIDAD_DURA) | PRODUCTOS_EXCLUIDOS_SIEMPRE | set(PRODUCTOS_RESPALDO.values())
    for reglas in HIPOTESIS.values():
        for regla in reglas:
            ids.update(regla["candidatos"])
    return ids


_ids_faltantes = _ids_referenciados() - set(CATALOGO.index)
if _ids_faltantes:
    raise ValueError(
        f"motor.py referencia IDs que no existen en {RUTA_CATALOGO.name}: {sorted(_ids_faltantes)}"
    )


def _productos_no_elegibles_por_edad(edad):
    if edad is None:
        return set()
    return {pid for pid, (minimo, maximo) in ELEGIBILIDAD_DURA.items() if not (minimo <= edad <= maximo)}


def _evaluar_necesidad(necesidad, perfil):
    """CAPA 1 + CAPA 2: filtra por elegibilidad dura y acumula score por hipótesis."""
    bloqueados = _productos_no_elegibles_por_edad(perfil.get("edad")) | PRODUCTOS_EXCLUIDOS_SIEMPRE

    scores = {}
    hipotesis_activadas = []

    for regla in HIPOTESIS.get(necesidad, []):
        if not regla["cond"](perfil):
            continue
        candidatos_validos = [c for c in regla["candidatos"] if c not in bloqueados]
        if not candidatos_validos:
            continue
        hipotesis_activadas.append(f"{regla['desc']} → +{regla['delta']} a {', '.join(candidatos_validos)}")
        for candidato in candidatos_validos:
            scores[candidato] = scores.get(candidato, 0.0) + regla["delta"]

    if necesidad == "mascotas" and perfil.get("ciudad") == "Bucaramanga" and scores:
        ajuste = PESOS["mascotas"]["bucaramanga_mascota"]
        for candidato in list(scores):
            scores[candidato] += ajuste
        hipotesis_activadas.append(f"ciudad=Bucaramanga → ajuste {ajuste:+.4f} a candidatos de mascotas (DANE)")

    return scores, hipotesis_activadas


def _campos_verificados(producto_id):
    fila = CATALOGO.loc[producto_id]
    return sum(1 for columna in COLUMNAS_ESTADO if fila[columna] == "verificado")


def _seleccionar(scores):
    """CAPA 3: producto_principal, producto_alternativa y desempate por campos verificados."""
    candidatos = [(pid, s) for pid, s in scores.items() if s > 0]
    if not candidatos:
        return None, None

    candidatos.sort(key=lambda item: (-item[1], -_campos_verificados(item[0])))
    principal = candidatos[0]

    alternativa_id = None
    if len(candidatos) > 1:
        segundo_id = candidatos[1][0]
        if CATALOGO.loc[segundo_id, "estado_precio"] == "verificado":
            alternativa_id = segundo_id

    return principal, alternativa_id


def _confianza(score):
    if score >= UMBRAL_ALTA:
        return "alta"
    if score >= UMBRAL_MEDIA:
        return "media"
    return "baja"


def _categoria(producto_id):
    return str(CATALOGO.loc[producto_id, "categoria"])


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _es_booleano(valor):
    return isinstance(valor, bool)


def _validar_perfil(perfil):
    """Valida perfil contra apuntes/contrato_campos_motor.md.

    Devuelve None si el perfil es válido, o el JSON de error (sin lanzar excepción)
    si falta algún campo obligatorio o alguno llegó con un valor inválido.
    """
    if not isinstance(perfil, dict):
        return {
            "error": True,
            "campos_faltantes": list(CAMPOS_OBLIGATORIOS),
            "campos_invalidos": [],
            "mensaje": "El perfil recibido no es un diccionario; no se puede validar ningún campo.",
        }

    campos_faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if campo not in perfil]
    campos_invalidos = []

    if not campos_faltantes:
        necesidad = perfil["necesidad"]
        if necesidad not in NECESIDADES_VALIDAS:
            campos_invalidos.append(f"necesidad: debe ser una de {NECESIDADES_VALIDAS}, llegó {necesidad!r}")

        edad = perfil["edad"]
        if not _es_entero(edad) or not (18 <= edad <= 75):
            campos_invalidos.append(f"edad: debe ser un entero entre 18 y 75, llegó {edad!r}")

        ciudad = perfil["ciudad"]
        if not isinstance(ciudad, str) or not ciudad.strip():
            campos_invalidos.append(f"ciudad: debe ser un string no vacío, llegó {ciudad!r}")

        rango_salarial = perfil["rango_salarial"]
        if rango_salarial not in RANGO_TIERS:
            campos_invalidos.append(
                f"rango_salarial: debe ser uno de {list(RANGO_TIERS)}, llegó {rango_salarial!r}"
            )

        tipo_vivienda = perfil["tipo_vivienda"]
        if tipo_vivienda not in TIPOS_VIVIENDA_VALIDOS:
            campos_invalidos.append(
                f"tipo_vivienda: debe ser uno de {TIPOS_VIVIENDA_VALIDOS}, llegó {tipo_vivienda!r}"
            )

        tiene_dependientes = perfil["tiene_dependientes"]
        if not _es_booleano(tiene_dependientes):
            campos_invalidos.append(f"tiene_dependientes: debe ser boolean, llegó {tiene_dependientes!r}")

        num_dependientes = perfil["num_dependientes"]
        if not _es_entero(num_dependientes) or not (0 <= num_dependientes <= 4):
            campos_invalidos.append(
                f"num_dependientes: debe ser un entero entre 0 y 4, llegó {num_dependientes!r}"
            )
        elif _es_booleano(tiene_dependientes):
            if tiene_dependientes is False and num_dependientes != 0:
                campos_invalidos.append("num_dependientes: debe ser 0 cuando tiene_dependientes es False")
            elif tiene_dependientes is True and not (1 <= num_dependientes <= 4):
                campos_invalidos.append("num_dependientes: debe ser entre 1 y 4 cuando tiene_dependientes es True")

        estado_civil = perfil["estado_civil"]
        if estado_civil not in ESTADOS_CIVILES_VALIDOS:
            campos_invalidos.append(
                f"estado_civil: debe ser uno de {ESTADOS_CIVILES_VALIDOS}, llegó {estado_civil!r}"
            )

        for campo in ("usa_drogueria", "usa_hoteles", "usa_agencias"):
            valor = perfil[campo]
            if not _es_booleano(valor):
                campos_invalidos.append(f"{campo}: debe ser boolean, llegó {valor!r}")

        tiene_mascota = perfil["tiene_mascota"]
        if not _es_booleano(tiene_mascota):
            campos_invalidos.append(f"tiene_mascota: debe ser boolean, llegó {tiene_mascota!r}")

        tipo_mascota = perfil["tipo_mascota"]
        if _es_booleano(tiene_mascota):
            if tiene_mascota is True and tipo_mascota not in TIPOS_MASCOTA_VALIDOS:
                campos_invalidos.append(
                    f"tipo_mascota: debe ser uno de {TIPOS_MASCOTA_VALIDOS} cuando tiene_mascota es True, "
                    f"llegó {tipo_mascota!r}"
                )
            elif tiene_mascota is False and tipo_mascota is not None:
                campos_invalidos.append("tipo_mascota: debe ser null cuando tiene_mascota es False")

        tipo_vehiculo = perfil["tipo_vehiculo"]
        if tipo_vehiculo not in TIPOS_VEHICULO_VALIDOS:
            campos_invalidos.append(
                f"tipo_vehiculo: debe ser uno de {TIPOS_VEHICULO_VALIDOS}, llegó {tipo_vehiculo!r}"
            )

    if not campos_faltantes and not campos_invalidos:
        return None

    partes = []
    if campos_faltantes:
        partes.append(f"faltan los campos {campos_faltantes}")
    if campos_invalidos:
        partes.append(f"hay {len(campos_invalidos)} campo(s) con valor inválido")
    mensaje = (
        "El perfil no se puede procesar porque " + " y ".join(partes) + ". "
        "Nicolás debe corregir esto en el bot antes de volver a llamar al motor."
    )

    return {
        "error": True,
        "campos_faltantes": campos_faltantes,
        "campos_invalidos": campos_invalidos,
        "mensaje": mensaje,
    }


def recomendar(perfil: dict) -> dict:
    error_validacion = _validar_perfil(perfil)
    if error_validacion is not None:
        return error_validacion

    try:
        necesidad = perfil.get("necesidad")
        if necesidad not in PRODUCTOS_RESPALDO:
            raise ValueError(f"necesidad no reconocida: {necesidad!r}")

        scores, hipotesis_activadas = _evaluar_necesidad(necesidad, perfil)
        seleccion, alternativa_id = _seleccionar(scores)

        if seleccion is None or seleccion[1] <= UMBRAL_RESPALDO:
            score_final = seleccion[1] if seleccion else 0.0
            producto_id = PRODUCTOS_RESPALDO[necesidad]
            return {
                "producto_principal": producto_id,
                "producto_alternativa": None,
                "categoria": _categoria(producto_id),
                "score": round(max(0.0, score_final), 2),
                "hipotesis_activadas": hipotesis_activadas,
                "razon": (
                    f"Ningún candidato superó el umbral de propensión ({UMBRAL_RESPALDO}) "
                    f"para la necesidad '{necesidad}'; se recomienda el producto de respaldo de la categoría."
                ),
                "confianza": _confianza(score_final),
            }

        producto_id, score_final = seleccion
        score_reportado = round(min(score_final, 1.0), 2)
        razones_principal = [h for h in hipotesis_activadas if producto_id in h]
        razon = (
            f"Se recomienda {producto_id} (necesidad: {necesidad}) por: "
            f"{'; '.join(razones_principal) if razones_principal else 'score acumulado de la categoría'}. "
            f"Score total: {score_reportado:.2f}."
        )

        return {
            "producto_principal": producto_id,
            "producto_alternativa": alternativa_id,
            "categoria": _categoria(producto_id),
            "score": score_reportado,
            "hipotesis_activadas": hipotesis_activadas,
            "razon": razon,
            "confianza": _confianza(score_final),
        }

    except Exception as error:
        necesidad = perfil.get("necesidad") if isinstance(perfil, dict) else None
        producto_id = PRODUCTOS_RESPALDO.get(necesidad, PRODUCTOS_RESPALDO["familia"])
        try:
            categoria = _categoria(producto_id)
        except Exception:
            categoria = "desconocida"
        return {
            "producto_principal": producto_id,
            "producto_alternativa": None,
            "categoria": categoria,
            "score": 0.0,
            "hipotesis_activadas": [],
            "razon": f"Fallo interno al calcular la recomendación ({error}); se devolvió el producto de respaldo.",
            "confianza": "baja",
        }


def registrar(perfil: dict, resultado: dict, canal: str = "prueba") -> None:
    """Guarda perfil en usuarios y resultado en recomendaciones (data/motor.db, scripts/crear_db.py).

    No registra nada si resultado trae "error": true (perfil inválido, nada que guardar).
    Nunca lanza excepción: si la DB no existe, no tiene las tablas, o falla por cualquier
    otra razón, el motor sigue funcionando igual -- registrar() simplemente no hace nada.
    """
    if not isinstance(resultado, dict) or resultado.get("error") is True:
        return

    try:
        conexion = sqlite3.connect(RUTA_DB)
        try:
            timestamp = datetime.now(timezone.utc).isoformat()

            cursor = conexion.execute(
                """
                INSERT INTO usuarios (
                    id_interno, id_contacto, necesidad, edad, ciudad, rango_salarial,
                    tipo_vivienda, tiene_dependientes, num_dependientes, estado_civil,
                    usa_drogueria, usa_hoteles, usa_agencias, tiene_mascota, tipo_mascota,
                    tipo_vehiculo, canal, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    perfil.get("id_interno"),
                    perfil.get("id_contacto"),
                    perfil.get("necesidad"),
                    perfil.get("edad"),
                    perfil.get("ciudad"),
                    perfil.get("rango_salarial"),
                    perfil.get("tipo_vivienda"),
                    int(bool(perfil.get("tiene_dependientes"))),
                    perfil.get("num_dependientes"),
                    perfil.get("estado_civil"),
                    int(bool(perfil.get("usa_drogueria"))),
                    int(bool(perfil.get("usa_hoteles"))),
                    int(bool(perfil.get("usa_agencias"))),
                    int(bool(perfil.get("tiene_mascota"))),
                    perfil.get("tipo_mascota"),
                    perfil.get("tipo_vehiculo"),
                    canal,
                    timestamp,
                ),
            )
            usuario_id = cursor.lastrowid

            conexion.execute(
                """
                INSERT INTO recomendaciones (
                    usuario_id, producto_principal, producto_alternativa, categoria,
                    score, confianza, hipotesis_activadas, razon, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    usuario_id,
                    resultado.get("producto_principal"),
                    resultado.get("producto_alternativa"),
                    resultado.get("categoria"),
                    resultado.get("score"),
                    resultado.get("confianza"),
                    json.dumps(resultado.get("hipotesis_activadas", []), ensure_ascii=False),
                    resultado.get("razon"),
                    timestamp,
                ),
            )
            conexion.commit()
        finally:
            conexion.close()
    except Exception:
        return


if __name__ == "__main__":
    perfil_base = {
        "edad": None, "ciudad": None, "rango_salarial": None, "tipo_vivienda": None,
        "tiene_dependientes": False, "num_dependientes": 0, "estado_civil": None,
        "usa_drogueria": False, "usa_hoteles": False, "usa_agencias": False,
        "tiene_mascota": False, "tipo_mascota": None, "tipo_vehiculo": "ninguno",
    }

    caso_1 = {**perfil_base, "necesidad": "salud", "edad": 30, "ciudad": "Bogotá",
              "rango_salarial": "3_4", "tipo_vivienda": "arrendada",
              "estado_civil": "soltero", "usa_drogueria": True}

    caso_2 = {**perfil_base, "necesidad": "familia", "edad": 45, "ciudad": "Medellín",
              "rango_salarial": "6_8", "tipo_vivienda": "propia",
              "tiene_dependientes": True, "num_dependientes": 2,
              "estado_civil": "casado", "tipo_vehiculo": "carro"}

    caso_3 = {**perfil_base, "necesidad": "movilidad", "edad": 28, "ciudad": "Soacha",
              "rango_salarial": "1.5_2", "tipo_vivienda": "familiar",
              "estado_civil": "soltero", "tipo_vehiculo": "moto"}

    casos = {
        "Caso 1 — droguería activa, necesidad salud": caso_1,
        "Caso 2 — salario medio-alto, edad 45, necesidad familia": caso_2,
        "Caso 3 — ciudad Soacha, salario bajo, necesidad movilidad": caso_3,
    }

    for nombre, perfil in casos.items():
        print(f"\n=== {nombre} ===")
        resultado = recomendar(perfil)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        registrar(perfil, resultado, canal="prueba")
