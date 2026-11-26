# Análisis técnico: por qué la API no encuentra sectores ni empareja empresas con socios

**Repositorio:** `ecosysval-python`  
**Fecha del análisis:** 24 de noviembre de 2026  
**Alcance:** código FastAPI, servicios de MIP/clasificación, archivos `data/MIP_2013.xlsx` y `data/clasificacion_2024.xlsx`, y pruebas HTTP reales contra la API.

---

## 1. Conclusión ejecutiva

La API **no está fallando principalmente por conectividad ni porque FastAPI esté caído**. De hecho, `/health` responde `200` y varios sectores válidos responden correctamente.

El problema es de **modelo de datos y de integración**:

1. **La API trabaja con sectores, no con empresas.** No existe ningún endpoint, modelo ni servicio que cargue empresas, busque socios ni devuelva datos de contacto. Por tanto, el emparejamiento empresa ↔ socio **no está implementado** en este repositorio.
2. **Los códigos de las empresas no coinciden con los sectores de la MIP.** La MIP contiene 262 ramas de 4 dígitos con una agregación particular. En la hoja de empresas hay 32 códigos distintos; solo **9 existen en la MIP** y **23 no existen**. Medido por registros, solo **55,481 de 238,943 empresas (23.2%)** podrían obtener análisis MIP; **183,462 (76.8%) quedarían sin sector**.
3. **La clasificación sí reconoce muchos códigos que la MIP no tiene.** El 98.8% de los registros de empresas obtiene alguna categoría, pero eso no significa que exista análisis sectorial. Esto produce el comportamiento confuso: una empresa puede aparecer “clasificada” y, al mismo tiempo, la API devuelve `404 Sector no encontrado`.
4. **La hoja que contiene las empresas (`Sheet1`) está explícitamente excluida.** La configuración solo carga 7 hojas de categorías; no carga la hoja con `entidad`, teléfono, correo, sitio web, actividad y código de cada empresa.
5. **No hay conexión implementada con NestJS, Supabase ni ninguna base de datos.** Aunque `.env.example` menciona `ECOSYSVAL_API_URL` y `DATABASE_URL`, el código no lee esas variables ni realiza peticiones o consultas.
6. **Cuando sí resuelve un sector, puede recomendar relaciones con coeficiente cero.** En 59 de 262 sectores, el top de clientes incluye al menos un coeficiente `0.0`; es decir, la API puede presentar como “cliente” a un sector sin relación registrada en la matriz.
7. **Las cascadas por truncamiento ocultan errores y generan inconsistencias.** Un código de 6 dígitos puede resolverse silenciosamente a otro de 4; además, `/recomendaciones/sector/{codigo}` no usa la misma lógica que `/recomendaciones/{codigo}`, por lo que un endpoint devuelve 404 y el otro 200 para el mismo código.

En resumen: **el sistema intenta conectar tres conjuntos de datos que no comparten el mismo catálogo de códigos y, además, nunca construye la capa empresa → sector → sectores relacionados → empresas socias**. Por eso no encuentra sectores y no puede emparejar empresas con sus socios.

---

## 2. Evidencia cuantitativa obtenida de los archivos reales

### 2.1 Matriz Insumo-Producto (`data/MIP_2013.xlsx`)

Al cargarla con el mismo criterio del servicio:

- La matriz cargada tiene **267 filas × 263 columnas**.
- Hay **262 sectores** utilizables, todos representados con códigos de **4 dígitos** tanto en filas como en columnas.
- Las 5 filas adicionales no son sectores productivos comparables: `UEION`, `IEI`, `IBSNS`, `B.1bV` y `P.1` (agregados/cuentas de cierre).
- El conjunto de códigos de filas sectoriales y columnas sectoriales coincide en los 262 sectores.

La MIP está identificada en el propio archivo como **“coeficientes técnicos / Rama SCIAN”** de 2013. No es un directorio de empresas ni una tabla de socios.

### 2.2 Clasificación (`data/clasificacion_2024.xlsx`)

El servicio construye un diccionario con **319 claves**:

- **309** claves de 4 dígitos.
- **7** claves de 6 dígitos.
- **3** claves que no son códigos: una nota de texto, el encabezado `Código CIIU` y el texto `NO ARTICULADO ULTIMA ACTUALIZACION`.

Las 7 claves de 6 dígitos pertenecen a `NO ARTICULADO`:

- `525210`, `525110`
- `437111`, `437112`, `437113`, `437210`
- `518210`

Ninguna de esas claves, salvo cuando la cascada cae a un padre existente, puede coincidir directamente con una fila/columna de la MIP, porque la MIP solo contiene sectores de 4 dígitos.

### 2.3 Empresas reales (`Sheet1`, ignorada por la API)

La hoja `Sheet1` contiene el universo que debería usarse para emparejar:

- **238,943 registros de empresas**.
- **32 códigos distintos**, todos de 4 dígitos.
- Campos disponibles: `entidad`, `per_ocu`, `Código CIIU`, `telefono`, `correoelec`, `www`, `Descripción de la Actividad`, `Tipo_Cadena_Valor` y `Conteo`.
- El campo `Tipo_Cadena_Valor` vale **`No Asignado` en los 238,943 registros (100%)**. Es decir, incluso la fuente no trae una asignación previa de cadena de valor que la API pudiera reutilizar.

Cobertura real de esos códigos:

| Verificación | Códigos | Registros | Resultado |
|---|---:|---:|---|
| Empresas con código presente en la clasificación | 31/32 | 236,004/238,943 | 98.8% obtiene categoría |
| Empresas con código presente en la MIP | **9/32** | **55,481/238,943** | **solo 23.2% puede analizarse** |
| Empresas con código ausente en la MIP | **23/32** | **183,462/238,943** | **76.8% devuelve “sector no encontrado”** |
| Código presente en MIP pero sin categoría | 1 (`9313`) | 2,939 | sector existe, categoría = `Sin clasificar` |

Los 9 códigos de empresa que sí existen en la MIP son:

`1125`, `1151`, `1152`, `3113`, `3114`, `3119`, `7223`, `8132`, `9313`.

Los 23 códigos de empresa que **no existen** en la MIP son:

`2212`, `2213`, `4335`, `4353`, `4373`, `4622`, `4631`, `4659`, `4662`, `4663`, `4664`, `4681`, `4683`, `4684`, `4842`, `5131`, `5132`, `5161`, `5162`, `5173`, `5192`, `5622`, `5629`.

El caso más grave es `4659` (*comercio al por menor de otros artículos*): concentra **52,006 empresas**, es el código con más registros de toda la hoja, y **no existe en la MIP**. Solo ese código explica más de una quinta parte del universo de empresas sin análisis.

### 2.4 Intersección clasificación ↔ MIP

- Códigos de 4 dígitos en clasificación: **309**.
- Sectores en MIP: **262**.
- Coincidencias exactas: **259**.
- Sectores MIP sin categoría: **3 de 262 (1.1%)** → `1129`, `1142`, `9313` devuelven `Sin clasificar`.
- Códigos clasificados que no existen en la MIP: **50**. Esos códigos pueden tener categoría, pero cualquier consulta de análisis termina en 404.

Esta es la explicación matemática del síntoma “suele no encontrar el sector”: **los catálogos no están alineados y no existe una tabla puente (crosswalk) entre el código de la empresa y la rama MIP**.

---

## 3. Causas raíz del síntoma 1: “no encuentra el sector”

### Causa 1 — Incompatibilidad de catálogos: códigos de empresa detallados vs. ramas MIP agregadas

La MIP no contiene la granularidad comercial que usan las empresas. Por ejemplo, en toda la división de comercio la MIP solo conserva, entre otros, `4311` y `4611`, mientras que las empresas y la clasificación usan decenas de códigos detallados `43xx` y `46xx` (mayoreo/menudeo por tipo de mercancía).

Sin una tabla de equivalencias, buscar `4659`, `4663`, `4631`, `4353` o `4373` en la MIP es buscar algo que **no existe en el archivo**. Ningún ajuste menor de búsqueda lo resolverá: hay que mapear explícitamente cada código de empresa a su rama MIP equivalente o incorporar una matriz/catálogo con esa granularidad.

### Causa 2 — La cascada de truncamiento es una solución parcial y silenciosa

En `app/services/mip_service.py:35-67`, `_encontrar_codigo_mip()` elimina dígitos hasta encontrar coincidencia simultánea en fila y columna:

```python
while len(codigo) >= 3:
    ...
    if col_encontrada and fila_encontrada:
        return codigo, col_encontrada, fila_encontrada
    codigo = codigo[:-1]
```

Resultados verificados ejecutando el servicio real:

| Código consultado | Resultado MIP | Categoría | Interpretación |
|---|---|---|---|
| `311811` | resuelve a `3118` | `ARTICULADOS GRISES` | El truncamiento “funciona”, pero responde otro sector sin advertencia semántica |
| `518210` | resuelve a `5182` | `NO ARTICULADO` | Exacto en clasificación, agregado en MIP |
| `437111` | **404** | `NO ARTICULADO` | Ni `43711`, ni `4371`, ni `437` existen en la MIP |
| `525210` | **404** | `NO ARTICULADO` | Ni `5252`, ni `525` existen en la MIP |
| `43711` (5 dígitos) | **404** | `Sin clasificar` | La cascada no encuentra ningún ancestro válido |

Es decir, la cascada solo salva los códigos cuyo ancestro de 4 dígitos coincide con una rama MIP. Para comercio e intermediación (`43xx/46xx/437xxx`), que es justo donde están la mayoría de las empresas, **no hay ancestro válido y el resultado es 404**.

Además, cuando la cascada sí resuelve, lo hace **en silencio**: `311811` se convierte en `3118`. La respuesta incluye `codigo_resuelto`, pero si el frontend muestra el sector como si fuera el código exacto de la empresa, el usuario verá recomendaciones de una rama más general sin saber que hubo agregación.

### Causa 3 — Los dos endpoints resuelven de forma distinta (inconsistencia verificada)

- `GET /recomendaciones/{codigo}` usa `analizar_sector()`, que aplica la cascada.
- `GET /recomendaciones/sector/{codigo}` (`app/api/recomendaciones.py:73-97`) hace comparación exacta `s["codigo"] == codigo`, sin cascada ni normalización.

Pruebas HTTP reales contra la API en ejecución:

| Petición | HTTP | Resultado |
|---|---|---|
| `GET /recomendaciones/sector/311811` | **404** | “Sector '311811' no encontrado en la MIP” |
| `GET /recomendaciones/311811` | **200** | resuelve a `3118` |
| `GET /recomendaciones/sector/4659` | **404** | no existe en MIP |
| `GET /recomendaciones/4659` | **404** | no existe en MIP |

Si el frontend usa un endpoint para validar el sector y otro para pedir recomendaciones, el mismo código puede ser “válido” e “inválido” a la vez. Esto por sí solo genera reportes de “a veces encuentra y a veces no”.

### Causa 4 — No existe una normalización única del código de entrada

Cada función “limpia” a su manera:

- `cargar_clasificacion()` (`app/services/clasificacion_service.py:30-37`) quita espacios y el sufijo `.0` **solo a las claves del Excel**.
- `obtener_categoria()` (líneas 43-55) no normaliza el código consultado: no quita `.0`, no valida que sean dígitos, no conserva ceros a la izquierda ni rechaza formatos inválidos; simplemente va truncando.
- `_encontrar_codigo_mip()` solo hace `str(...).strip()`.

Consecuencia verificada: `03118` no se resuelve ni obtiene categoría, aunque representa el mismo sector que `3118` con un cero inicial; y un código inválido de 5 dígitos como `46591` recibe la categoría de `4659` en vez de ser rechazado como error de captura. El sistema no distingue entre “código válido agregado”, “código válido sin equivalencia” y “código mal formado”: todo se reduce a truncar o devolver 404.

### Causa 5 — La clasificación se sobrescribe en silencio y contiene basura

En `app/services/clasificacion_service.py:18-37`, las 7 hojas se cargan en orden y cada código se guarda con `clasificacion[codigo_limpio] = nombre_hoja`. Si un código aparece en varias hojas, **gana la última hoja leída**, sin registrar el conflicto.

Conflictos reales detectados (9 códigos):

| Código | Hojas donde aparece | Categoría final (la que devuelve la API) |
|---|---|---|
| `3111` | Clave, Articulador | Articulador |
| `3241` | Clave, Articulador, ARTICULADOS GRISES | ARTICULADOS GRISES |
| `3251` | Clave, ARTICULADOS GRISES | ARTICULADOS GRISES |
| `3314` | Clave, ARTICULADOS GRISES | ARTICULADOS GRISES |
| `3336` | Clave, Articulador | Articulador |
| `3371` | Multicadena impulsor, ARTICULADOS GRISES (×2) | ARTICULADOS GRISES |
| `3399` | Clave, Potenciales | Potenciales |
| `4341` | Articulador, ARTICULADOS GRISES | ARTICULADOS GRISES |
| `4342` | Articulador, ARTICULADOS GRISES | ARTICULADOS GRISES |

Además hay **18 códigos duplicados dentro de `ARTICULADOS GRISES`** y el cargador admite claves que no son códigos (notas y encabezados repetidos dentro de la hoja). Por eso `/recomendaciones/estadisticas` reporta un total de **319** “sectores clasificados” cuando solo hay **309 códigos de 4 dígitos** y únicamente **259** coinciden con la MIP. Las estadísticas del sistema sobreestiman la cobertura real.

### Causa 6 — Hay sectores MIP que nunca tendrán categoría

De los 262 sectores MIP, `1129`, `1142` y `9313` no aparecen en ninguna hoja de clasificación. Para ellos la API responde categoría `Sin clasificar`. El caso `9313` es especialmente visible porque corresponde a **2,939 empresas** de la hoja `Sheet1`: el análisis MIP existe, pero el sistema las presenta como no clasificadas.

---

## 4. Causas raíz del síntoma 2: “no empareja las empresas con sus debidos socios”

### Causa 7 — El emparejamiento de empresas no está implementado (causa principal)

Este es el punto más importante del diagnóstico. Revisando todo el repositorio:

- `main.py:52` solo incluye un router: `recomendaciones.router`.
- Los únicos endpoints son listar sectores, estadísticas, información de un sector y recomendaciones **entre sectores** (`app/api/recomendaciones.py`).
- El modelo de respuesta `RecomendacionCompleta` (`app/models/recomendacion.py:28-36`) solo contiene `codigo`, `sector`, `categoria`, `top_clientes` y `top_proveedores`, donde cada nodo es **un sector**, no una empresa.
- No existe modelo `Empresa` ni `Socio`, ni campos de nombre comercial, entidad, teléfono, correo o sitio web en ninguna respuesta.
- No hay ningún código que lea la hoja `Sheet1`, que es donde están las empresas. La configuración `HOJAS_CATEGORIAS` (`app/core/config.py:25-33`) incluye solo las 7 hojas de categorías y excluye `Sheet1`.
- No hay consultas a base de datos ni peticiones HTTP a otro backend: `app/core/config.py` solo define rutas locales y constantes. Las variables `DATABASE_URL`, `ECOSYSVAL_API_URL`, `BANXICO_TOKEN` e `INEGI_TOKEN` aparecen únicamente en `.env.example` y **no se usan en ninguna parte del código**.

Por tanto, aunque el sector se resuelva perfectamente, la respuesta máxima que esta API puede dar es: *“el sector X se relaciona con los sectores A, B y C”*. Nunca podrá decir *“la empresa Juan Pérez S.A. puede venderle a estas 5 empresas”*, porque:

1. no carga las empresas;
2. no conoce la identidad de la empresa que consulta (no hay endpoint por empresa);
3. no hace el join sector relacionado → empresas de ese sector;
4. no tiene criterios de emparejamiento (ubicación, tamaño, contacto válido, etc.).

**Conclusión:** el “no empareja empresas con socios” no es un error de búsqueda; es una funcionalidad ausente. Lo que hoy existe es solo la primera mitad del algoritmo (relaciones entre sectores).

### Causa 8 — Aun a nivel sector, genera socios falsos con coeficiente cero

En `app/services/mip_service.py:69-85`, `_crear_lista_enriquecida()` filtra que el nombre empiece con dígito, ordena por coeficiente descendente y toma el top N, **pero no exige que el coeficiente sea mayor que cero**.

Impacto medido ejecutando el servicio sobre los 262 sectores:

- **59 de 262 sectores (22.5%)** incluyen al menos un “cliente” con coeficiente `0.0` en su top 5.
- Hay **30 filas sectoriales cuya suma es cero**.
- Ejemplo real: para `8132` (asociaciones religiosas), la API devuelve como top clientes a `1111`, `1112`, `1113`, `1114` y `1119` (cultivos), **todos con coeficiente 0.0 y porcentaje 0.0**. Esos sectores aparecen simplemente porque van primero en la matriz cuando todo vale cero.

Si el frontend presenta esa lista como “posibles socios/clientes”, el sistema está emparejando empresas con sectores **sin ninguna relación económica registrada**. Esto explica la percepción de que empareja “con los socios incorrectos”.

### Causa 9 — El “porcentaje” no es una participación real del socio

El archivo MIP contiene **coeficientes técnicos** `a_ij` (insumo del sector *i* requerido por unidad de producción del sector *j*). Sin embargo, en `app/services/mip_service.py:83` la API calcula:

```python
"porcentaje": round(float(row["coeficiente"]) * 100, 2)
```

Eso presenta el coeficiente técnico como si fuera un porcentaje de participación, pero:

- Para proveedores (columna), el coeficiente no es la participación del proveedor en las compras del sector; las columnas no suman 1.
- Para clientes (fila), el coeficiente técnico tampoco es la participación de ese cliente en las ventas del sector.

El ordenamiento por coeficiente puede servir como una primera medida de intensidad, pero **etiquetarlo como porcentaje induce a elegir “socios debidos” con una métrica que no significa lo que la interfaz sugiere**. Para hablar de participaciones habría que normalizar: proveedores como `a_ij / Σ_i a_ij` sobre insumos intermedios, y clientes con una matriz de distribución/ventas o normalizando la fila sobre flujos positivos, aclarando que es una intensidad relativa.

### Causa 10 — La categoría puede venir de un ancestro y no del sector exacto

`obtener_categoria()` (`app/services/clasificacion_service.py:43-55`) también trunca hasta 3 dígitos. Como la clasificación solo tiene claves de 4 y 6 dígitos, un código de 6 dígitos no clasificado exactamente hereda la categoría del padre de 4. Ejemplo verificado: `311811` no está como tal en la clasificación, pero devuelve la categoría de `3118`.

Esto puede ser aceptable como agregación, **pero la API no informa que la categoría es heredada**. Si la categoría se usa para decidir el tipo de socio o la prioridad comercial (Clave, Articulador, Multicadena, etc.), se están tomando decisiones con una clasificación aproximada presentada como exacta.

### Causa 11 — Las “pruebas” del repo no prueban el comportamiento real de la API

Los archivos `test_*.py` no son una suite automatizada: son scripts exploratorios que **duplican la lógica** en vez de importar los servicios. Peor aún, lo hacen con reglas distintas:

- `test_sistema_completo.py:107,125,148` usa `clasificacion.get(codigo, "Sin clasificar")`, **sin cascada**.
- `test_clasificacion_v2.py:90` hace lo mismo.
- El servicio real sí usa cascada (`clasificacion_service.py:43-55`).

Por eso los scripts pueden “pasar” mientras la API se comporta de otra manera: nadie está verificando el código que corre en producción, ni los casos críticos (`4659`, `311811`, `9313`, `8132`, conflictos de hojas). No hay ni un solo test que detecte que el 76.8% de las empresas no tiene sector MIP.

---

## 5. Qué NO es la causa principal

Para evitar diagnósticos equivocados:

- **No es un problema de que la API esté caída:** `/health` responde 200 y sectores como `3118` responden correctamente.
- **No es principalmente CORS:** `main.py:29-48` permite `localhost:3000/3001/5173`, el dominio de Vercel y orígenes extra por `EXTRA_CORS_ORIGINS`. Un origen no permitido bloquearía en el navegador *todas* las peticiones, no produciría 404 selectivos por código. Aun así, conviene confirmar que el dominio real del frontend esté en la lista.
- **No es un problema de rendimiento/caché:** los Excel se cargan una vez y quedan en memoria (`_mip_cache`, `_clasificacion_cache`).
- **No basta con “arreglar la búsqueda”:** aunque la búsqueda fuera perfecta, seguiría sin existir la capa que convierte sectores relacionados en empresas socias concretas.

Sí es un riesgo secundario de despliegue que `requirements.txt` está guardado en UTF-16 con CRLF y con versiones muy nuevas/poco comunes; puede dificultar reproducir el entorno, pero no explica los 404 por código.

---

## 6. Cómo debería funcionar la conexión (flujo correcto)

Hoy el flujo implementado es solo:

```text
código → (cascada) → sector MIP → sectores relacionados
```

El flujo necesario para cumplir lo que el sistema promete es:

```text
Empresa (id/código SCIAN de 6 o 4 dígitos)
  → normalización del código
  → equivalencia explícita a rama MIP (tabla crosswalk versionada)
  → análisis MIP (proveedores/clientes sectoriales, solo coeficientes > 0)
  → para cada sector relacionado: buscar EMPRESAS de ese sector en Sheet1/DB
  → ranking de socios (intensidad sectorial + misma entidad + tamaño + contacto válido)
  → respuesta con empresas reales y trazabilidad del mapeo
```

Sin los pasos 2, 4 y 5, el emparejamiento empresa ↔ socio es imposible por diseño.

---

## 7. Plan de corrección concreto (priorizado)

### P0 — Sin esto, el sistema seguirá sin conectar empresas

1. **Crear una tabla puente SCIAN → rama MIP** (CSV o tabla en BD, versionada y revisada por negocio), en lugar de depender del truncamiento. Debe cubrir al menos los 23 códigos de empresa hoy huérfanos y los códigos de 6 dígitos de `NO ARTICULADO`.  
   Ejemplos del tipo de decisión que debe quedar explícita: códigos comerciales detallados `43xx/46xx` deben mapearse a las ramas comerciales de la MIP (`4311`/`4611`) o a la rama que el equipo defina; el mapeo no debe inferirse borrando dígitos.  
   La respuesta debe incluir `codigo_original`, `codigo_mip`, `metodo_mapeo` (`exacto`, `crosswalk`, `padre`) y `nivel_agregacion`.
2. **Cargar las empresas**: incorporar `Sheet1` (o, mejor, la base de datos real de Ecosysval) con un servicio `empresas_service` y modelos `Empresa`/`SocioRecomendado` que incluyan nombre/actividad, entidad, tamaño, teléfono, correo y web.
3. **Crear el endpoint de socios**, por ejemplo `GET /empresas/{empresa_id}/socios?rol=proveedor|cliente`, que ejecute el flujo completo de la sección 6 y devuelva empresas, no solo sectores.
4. **Conectar o eliminar la integración prometida**: si las empresas viven en el backend NestJS/Supabase, implementar el cliente con `ECOSYSVAL_API_URL`/`DATABASE_URL`; si no, cargar el Excel de empresas y documentar que esa es la fuente. Hoy esas variables son decorativas.

### P1 — Correctitud de lo que ya existe

5. **Unificar la resolución de códigos** en una sola función usada por todos los endpoints: normalizar (solo dígitos, quitar `.0` final, validar longitud 4/6, decidir cómo tratar ceros a la izquierda) y resolver con el crosswalk. Que `/recomendaciones/sector/{codigo}` y `/recomendaciones/{codigo}` nunca vuelvan a discrepar.
6. **Filtrar coeficientes `<= 0` y nulos** antes del top N en `_crear_lista_enriquecida()`, y devolver menos resultados si no hay relaciones reales. Nunca rellenar con sectores en cero.
7. **Corregir la métrica**: renombrar `porcentaje` a algo fiel (`coeficiente_tecnico`) o calcular participaciones normalizadas y documentar su significado.
8. **Resolver conflictos de clasificación de forma explícita**: detectar códigos en varias hojas al cargar, registrar advertencia y aplicar una prioridad documentada (o soportar multiclase). Validar que las claves cumplan `^\d{4}$` o `^\d{6}$` y enviar notas/encabezados a una lista de rechazados, no al diccionario.
9. **Completar o marcar los 3 sectores sin categoría** (`1129`, `1142`, `9313`) para que la UI no los presente como error de datos del usuario.
10. **Distinguir errores**: `422` para código mal formado, `404` con motivo (`sin_equivalencia_mip`, `sector_inexistente`) y sugerencias de ramos válidos. No usar el mismo “no encontrado” para todo.

### P2 — Calidad y prevención

11. **Reemplazar los scripts `test_*.py` por pruebas pytest** que importen los servicios reales e incluyan casos dorados: `3118` exacto, `311811` agregado, `4659` con crosswalk, `437111`, `9313`, `8132` sin clientes en cero, y detección de conflictos entre hojas.
12. **Registrar métricas de cobertura** al arrancar: cuántos códigos de empresa tienen equivalencia MIP y cuántos registros representan; alertar si baja del umbral definido.
13. **Actualizar la documentación**: el README promete recopilación Banxico/INEGI y reportes que este servicio no implementa; debe describir el alcance real para que el frontend no consuma contratos inexistentes.

---

## 8. Casos de aceptación mínimos para verificar la corrección

| Caso | Entrada | Comportamiento esperado tras corregir |
|---|---|---|
| Sector exacto | `3118` | 200 en ambos endpoints, mismo resultado |
| Clase SCIAN de 6 dígitos | `311811` | 200 indicando agregación a `3118` (`metodo_mapeo=padre`) en ambos endpoints |
| Código comercial huérfano | `4659` | 200 vía crosswalk explícito, indicando la rama MIP usada |
| Código sin equivalencia definida | uno no contemplado | 404 con motivo `sin_equivalencia_mip`, no un genérico |
| Sector sin clientes reales | `8132` | `top_clientes` vacío o solo con coeficientes > 0; nunca cultivos con 0.0 |
| Sector sin categoría | `9313` | categoría asignada o advertencia explícita de dato faltante |
| Empresa real | una empresa con código `4659` | devuelve empresas socias (proveedoras/clientes) con datos de contacto y criterio de ranking |
| Conflicto de clasificación | `3241` | una sola categoría según prioridad documentada, con el conflicto registrado en logs |

---

## 9. Resumen final en una frase

La API no conecta bien las empresas porque **busca códigos de empresa en un catálogo sectorial que no los contiene (76.8% de las empresas queda fuera), resuelve con truncamientos inconsistentes entre endpoints, y nunca implementó la capa que carga las empresas y las empareja entre sí**: hoy, en el mejor de los casos, solo relaciona sectores, y en el 22.5% de ellos incluso recomienda relaciones con coeficiente cero.
