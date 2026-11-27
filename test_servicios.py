"""
Prueba rapida de los servicios
"""

from app.services.mip_service import analizar_sector, listar_sectores
from app.services.clasificacion_service import obtener_estadisticas

print("=" * 60)
print(" probando servicios")
print("=" * 60)

# Estadísticas
print("\n Estadísticas de clasificación:")
stats = obtener_estadisticas()
print(f"   Total: {stats['total']} sectores")
for cat, count in stats['por_categoria'].items():
    print(f"   • {cat}: {count}")

# Listar sectores
print(f"\n Total sectores en MIP:")
sectores = listar_sectores()
print(f"   {len(sectores)} sectores encontrados")
print(f"   Primeros 3:")
for s in sectores[:3]:
    print(f"      • {s['nombre']}")

# Analizar un sector
print(f"\n Analisis del sector 3111:")
resultado = analizar_sector("3111")
if resultado:
    print(f"   Sector: {resultado['sector']}")
    print(f"   Categoría: {resultado['categoria']}")
    print(f"   Top 3 clientes:")
    for c in resultado['top_clientes'][:3]:
        print(f"      • [{c['categoria']}] {c['sector']} ({c['porcentaje']}%)")

print("\n Todo funciona!")

# probar modelos pidantyc

print("\n" + "=" * 60)
print(" probando modelos pidantyc")
print("=" * 60)

from app.models.recomendacion import RecomendacionCompleta

# convertir el resultado a modelo Pydantic
resultado_modelo = RecomendacionCompleta(**resultado)

print(f"\n Modelo creado exitosamente")
print(f"   Tipo: {type(resultado_modelo).__name__}")
print(f"   Sector: {resultado_modelo.sector}")
print(f"   Total clientes: {len(resultado_modelo.top_clientes)}")
print(f"   Primer cliente: {resultado_modelo.top_clientes[0].sector}")

# convertir de vuelta a dict/JSON
print(f"\n Convertido a JSON:")
import json
json_str = resultado_modelo.model_dump_json(indent=2)
# solo mostrar los primeros 300 caracteres
print(json_str[:300] + "...")