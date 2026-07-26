"""Conversión de timestamps a hora de Colombia -- compartido entre metricas.py y pesos.py.

motor.py guarda todo en UTC (datetime.now(timezone.utc).isoformat() en registrar()) a
propósito -- es la fuente de verdad en la base de datos y no depende de en qué zona
horaria corra el servidor. La conversión a hora de Colombia es solo para mostrar en
pantalla, nunca para almacenar.
"""
from zoneinfo import ZoneInfo

ZONA_COLOMBIA = ZoneInfo("America/Bogota")
