# Pipeline de Extracción de Ofertas Laborales Chile/LatAm

Construir un pipeline en Python que extraiga ofertas laborales de **3 fuentes prioritarias**: Get on Board (API pública), Chiletrabajos (RSS + HTML) y **BNE Chile** (sitemap + HTML/JSON-LD), las normalice con un parser estructural a un esquema JSON unificado y las almacene en archivos `.json`.

## User Review Required

> [!IMPORTANT]
> **Computrabajo descartado**: Durante la investigación, `cl.computrabajo.com` retorna HTTP 403 incluso para `/robots.txt`. Tiene protección anti-bot de nivel enterprise (Cloudflare/Imperva). Implementar su scraping requeriría proxies residenciales y herramientas anti-detección costosas.

> [!WARNING]
> **Trabajando.cl se degrada a fase opcional**: Aunque su `robots.txt` es permisivo, en las verificaciones recientes el sitio respondió `502` en la home y en rutas de búsqueda. Además, su contenido depende de JavaScript y requeriría Playwright. Por costo y fragilidad, no se incluye en la fase 1.

> [!NOTE]
> **BNE Chile se incorpora a fase 1**: Tiene `robots.txt` permisivo, un sitemap masivo de ofertas públicas y páginas de detalle accesibles con `JobPosting` JSON-LD más HTML estructurado. Es una fuente más sostenible que Trabajando.cl para una primera versión.

## Esquema JSON Unificado

Todas las ofertas se normalizarán al siguiente esquema:

```json
{
  "id": "getonboard-12345",
  "fuente": "getonboard",
  "titulo": "Data Engineer Senior",
  "empresa": "CoyanServices",
  "fecha_publicacion": "2026-03-28T00:00:00Z",
  "ubicacion": {
    "ciudad": "Santiago",
    "region": "Metropolitana",
    "pais": "Chile"
  },
  "modalidad": "remoto",
  "jornada": "full-time",
  "salario": {
    "min": 3000,
    "max": 5000,
    "moneda": null,
    "periodo": null
  },
  "seniority": "senior",
  "categoria": "Data Science & ML",
  "descripcion": "Texto completo de la oferta...",
  "requisitos": "Texto de requisitos...",
  "beneficios": "Texto de beneficios...",
  "tags": ["AWS", "Python", "ETL"],
  "url": "https://www.getonbrd.com/jobs/...",
  "fecha_extraccion": "2026-03-30T23:00:00Z"
}
```

> [!NOTE]
> Los campos que no estén disponibles en una fuente se guardan como `null`. No todas las fuentes exponen todos los campos (ej: Chiletrabajos rara vez incluye salario explícito).

> [!NOTE]
> No se inferirá `moneda` ni `periodo` salarial si la fuente no lo publica explícitamente. El pipeline prioriza fidelidad a la fuente por sobre supuestos.

## Arquitectura del Proyecto

```
miner-empleos/
├── requirements.txt
├── config.py                    # Configuración global (delays, rutas, etc.)
├── main.py                      # Orquestador principal del pipeline
├── schema.py                    # Dataclass/TypedDict del esquema unificado
├── state/                       # Checkpoints y cursores por fuente
│   ├── chiletrabajos.cursor.json
│   └── bne.cursor.json
│
├── extractors/                  # Fase 1: Extracción cruda
│   ├── __init__.py
│   ├── base.py                  # Clase abstracta BaseExtractor
│   ├── getonboard.py            # Extractor via API REST
│   ├── chiletrabajos.py         # Extractor via RSS + scraping HTML detalle
│   └── bne.py                   # Extractor via sitemap + detalle HTML
│
├── parsers/                     # Fase 2: Normalización estructural
│   ├── __init__.py
│   ├── base.py                  # Clase abstracta BaseParser
│   ├── getonboard_parser.py     # Mapeo directo JSON → esquema
│   ├── chiletrabajos_parser.py  # Extracción con regex + BeautifulSoup
│   └── bne_parser.py            # Extracción priorizando JSON-LD
│
├── storage/                     # Fase 3: Persistencia en archivos .json
│   ├── __init__.py
│   └── json_storage.py          # Deduplicación + guardado incremental
│
├── data/                        # Directorio de salida
│   ├── getonboard/
│   │   └── 2026-03-30.json
│   ├── chiletrabajos/
│   │   └── 2026-03-30.json
│   ├── bne/
│   │   └── 2026-03-30.json
│   └── consolidated/
│       └── 2026-03-30.json      # Merge de todas las fuentes
│
└── tests/
    ├── test_extractors.py
    ├── test_parsers.py
    ├── test_storage.py
    └── test_state.py
```

---

## Proposed Changes

### Dependencias

#### [NEW] [requirements.txt](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/requirements.txt)

```
requests>=2.31.0          # HTTP client para API y scraping
beautifulsoup4>=4.12.0    # Parsing HTML
lxml>=5.1.0               # Parser rápido para XML (RSS) y HTML
python-dateutil>=2.8.0    # Parsing de fechas en español
pytest>=8.0.0             # Test runner
```

> [!NOTE]
> `playwright` queda fuera de la fase 1. Solo se agregará si más adelante se implementa un spike para Trabajando.cl.

---

### Configuración y Esquema

#### [NEW] [config.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/config.py)

Configuración centralizada del pipeline:
- `DATA_DIR`: ruta de salida (`data/`)
- `STATE_DIR`: ruta de checkpoints (`state/`)
- `REQUEST_DELAY`: delay base entre peticiones HTTP
- `REQUEST_TIMEOUT`: timeout por request (ej: 20 segundos)
- `GETONBOARD_BASE_URL`: `https://www.getonbrd.com/api/v0`
- `GETONBOARD_PER_PAGE`: 120 (máximo permitido)
- `CHILETRABAJOS_RSS_URL`: `https://www.chiletrabajos.cl/rss.xml`
- `CHILETRABAJOS_BASE_URL`: `https://www.chiletrabajos.cl`
- `BNE_BASE_URL`: `https://www.bne.gob.cl`
- `BNE_SITEMAP_URL`: `https://www.bne.gob.cl/sitemap.xml`
- `USER_AGENT`: user-agent realista (no "Scrapy", que está bloqueado)
- `CHECKPOINT_EVERY`: número de ofertas tras el cual se persiste cursor y progreso (ej: 100)
- `MAX_HOURS_PER_SOURCE`: presupuesto máximo de tiempo por fuente (default: 2 horas). El extractor se detendrá limpiamente al alcanzar este límite, guardando todo lo recolectado hasta ese momento.
- `MAX_HOURS_TOTAL`: presupuesto máximo de tiempo total del pipeline (default: 5 horas). Evita que el pipeline total se extienda indefinidamente.
- `MAX_ITEMS`: límite opcional por fuente para QA/manual verification. Si se define, corta aunque el presupuesto horario no se haya agotado.

#### [NEW] [schema.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/schema.py)

Dataclass `JobOffer` que representa el esquema JSON unificado, con método `to_dict()` para serialización y validación de campos obligatorios (`id`, `fuente`, `titulo`, `url`).

---

### Extractors (Fase 1: Extracción)

#### [NEW] [extractors/base.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/extractors/base.py)

Clase abstracta `BaseExtractor` con:
- `extract() -> list[dict]`: retorna datos crudos (JSON o HTML parseado)
- `get_name() -> str`: nombre de la fuente
- Manejo de logging y errores comunes

#### [NEW] [extractors/getonboard.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/extractors/getonboard.py)

**Estrategia**: Extracción exhaustiva y simple usando el endpoint público de búsqueda con paginación y `expand[]`.

Endpoints a usar:
1. `GET /api/v0/search/jobs?per_page=120&page=N&lang=es`
2. `expand[]=company&expand[]=seniority&expand[]=modality&expand[]=location_cities&expand[]=tags`
3. Fallback opcional: endpoints por categoría solo si el endpoint de búsqueda cambia de comportamiento

Flujo:
1. Consumir `search/jobs` comenzando en `page=1`
2. Iterar por páginas hasta que `page > total_pages` o `data` esté vacío
3. Pedir las relaciones necesarias vía `expand[]` para evitar N+1 requests
4. Acumular los resultados en una lista de diccionarios crudos, deduplicando por `id`
5. Respetar un delay bajo (0.25s a 0.5s) entre peticiones
6. **Condiciones de parada**: se detiene cuando (a) se agotaron las páginas, (b) la API devuelve un error HTTP persistente, (c) se alcanzó `MAX_HOURS_PER_SOURCE`, o (d) se alcanzó `MAX_ITEMS`

#### [NEW] [extractors/chiletrabajos.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/extractors/chiletrabajos.py)

**Estrategia combinada**: RSS feed para leer el listado masivo + scraping HTML del detalle de cada oferta.

Flujo:
1. Parsear el RSS feed (`/rss.xml`) con `lxml.etree` para obtener la lista completa de ofertas con: `title`, `link`, `description` (resumen), `category`, `pubDate`, `guid`
2. Ordenar las ofertas del RSS por fecha descendente (más recientes primero)
3. Para cada oferta, hacer GET a su URL de detalle (`/trabajo/{slug}`) 
4. Con `BeautifulSoup`, extraer del HTML de detalle: descripción completa, empresa, ubicación, requisitos y cualquier metadata adicional disponible
5. Respetar delay de 2 segundos entre peticiones de detalle
6. Persistir checkpoint en `state/chiletrabajos.cursor.json` con `rss_index`, `last_guid` y timestamp del último guardado
7. Reanudar desde checkpoint cuando se ejecute con `--resume`, evitando reiniciar siempre desde el primer item del RSS
8. **Condiciones de parada**: se detiene cuando (a) se procesaron todos los items del RSS, (b) ocurre un error HTTP persistente (3 reintentos fallidos), (c) se alcanzó `MAX_HOURS_PER_SOURCE`, o (d) se alcanzó `MAX_ITEMS`
9. **Guardado progresivo**: cada `CHECKPOINT_EVERY` ofertas procesadas se guarda a disco y se actualiza el cursor

> [!NOTE]
> El RSS tiene ~37k items. Con un delay de 2s, procesar todo tomaría ~20 horas. Con `MAX_HOURS_PER_SOURCE=2` (default), se extraerán ~3,600 ofertas por ejecución, priorizando las más recientes.

> [!NOTE]
> El `robots.txt` de Chiletrabajos bloquea específicamente el user-agent `Scrapy`, pero permite todos los demás. Se usará un user-agent de navegador estándar.

#### [NEW] [extractors/bne.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/extractors/bne.py)

**Estrategia**: Parsear el sitemap público y luego scrapear el detalle HTML de cada oferta priorizando los datos estructurados (`JobPosting` JSON-LD).

**Prioridad**: Alta — implementar después de Get on Board y antes de cualquier spike con navegador.

Flujo:
1. Parsear `https://www.bne.gob.cl/sitemap.xml` para obtener todas las URLs `/oferta/{id}`
2. Recorrer las ofertas en el orden del sitemap, persistiendo checkpoint por índice
3. Para cada detalle, hacer GET a la página pública de oferta
4. Extraer primero el bloque `application/ld+json` tipo `JobPosting`
5. Completar campos faltantes desde el HTML estructurado: jornada, tipo de contrato, nivel de cargo, requisitos, etc.
6. Respetar delay de 1 segundo entre peticiones de detalle
7. Persistir checkpoint en `state/bne.cursor.json` con `sitemap_index` y `last_offer_url`
8. **Condiciones de parada**: se detiene cuando (a) se agotó el sitemap, (b) ocurre un error HTTP persistente, (c) se alcanzó `MAX_HOURS_PER_SOURCE`, o (d) se alcanzó `MAX_ITEMS`

> [!NOTE]
> El sitemap de BNE no expone `lastmod`, por lo que la reanudación por índice es obligatoria para backfill progresivo.

### Fuente futura opcional: Trabajando.cl

**Estado**: Fuera de fase 1.

Si se retoma más adelante:
- Requiere `playwright` y navegadores instalados
- Debe abordarse como spike técnico separado
- Solo se recomienda si el sitio recupera estabilidad y entrega valor diferencial respecto de BNE/Chiletrabajos

---

### Parsers (Fase 2: Normalización Estructural)

#### [NEW] [parsers/base.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/parsers/base.py)

Clase abstracta `BaseParser` con:
- `parse(raw_data: dict) -> JobOffer`: convierte datos crudos al esquema unificado
- Métodos auxiliares compartidos: `extract_salary_from_text()`, `normalize_date()`, `normalize_modality()`, `normalize_location()`

#### [NEW] [parsers/getonboard_parser.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/parsers/getonboard_parser.py)

**Mapeo directo** de campos de la API al esquema:
| API Get on Board | Esquema | Notas |
|---|---|---|
| `attributes.title` | `titulo` | Directo |
| `company.attributes.name` | `empresa` | Requiere expand de company |
| `attributes.published_at` | `fecha_publicacion` | Epoch → ISO 8601 |
| `attributes.countries` | `ubicacion.pais` | Array de strings |
| `attributes.location_cities` | `ubicacion.ciudad` | Requiere expand |
| `attributes.remote_modality` | `modalidad` | "fully_remote", "hybrid", etc. |
| `attributes.min_salary` / `max_salary` | `salario.min/max` | No asumir moneda/período si no vienen explícitos |
| `seniority.attributes.name` | `seniority` | Requiere expand |
| `attributes.category_name` | `categoria` | Directo |
| `attributes.description` | `descripcion` | HTML, limpiar a texto |
| `attributes.functions` | `requisitos` | HTML, limpiar a texto |
| `attributes.benefits` | `beneficios` | HTML, limpiar a texto |
| `attributes.desirable` | (adjuntar a requisitos) | HTML, limpiar a texto |
| `tags[].attributes.name` | `tags` | Requiere expand |

#### [NEW] [parsers/chiletrabajos_parser.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/parsers/chiletrabajos_parser.py)

**Estrategia de parsing**: Combinación de datos del RSS + datos del HTML de detalle.

Del RSS:
- `title` → `titulo` (parsear: a veces incluye ubicación y salario, ej: "LAS CONDES . ANALISTA $750.000")
- `category` → `categoria`
- `pubDate` → `fecha_publicacion`
- `link` → `url`
- `guid` → `id` (prefijado como `chiletrabajos-{guid}`)

Del HTML de detalle:
- Nombre de empresa → `empresa` (extraer del selector correspondiente)
- Ciudad → `ubicacion.ciudad` (enlace a `/ciudad/{slug}`)
- Descripción completa → `descripcion`
- Regex para extraer salario del texto: patrones como `$750.000`, `$1.200.000`
- Regex para detectar modalidad: "remoto", "teletrabajo", "presencial", "híbrido"
- Regex para detectar jornada: "part-time", "full-time", "jornada completa"

#### [NEW] [parsers/bne_parser.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/parsers/bne_parser.py)

**Estrategia**: Priorizar el `JobPosting` JSON-LD y complementar con el HTML del detalle.

Mapeo base desde JSON-LD:
- `title` → `titulo`
- `hiringOrganization.name` → `empresa`
- `datePosted` → `fecha_publicacion`
- `validThrough` → campo auxiliar interno o descarte si el esquema no lo usa
- `jobLocation.address.addressLocality` → `ubicacion.ciudad`
- `jobLocation.address.addressRegion` → `ubicacion.region`
- `jobLocation.address.addressCountry` → `ubicacion.pais`
- `description` → `descripcion`

Campos complementarios desde HTML:
- Jornada
- Tipo de contrato
- Nivel de cargo ofrecido
- Requisitos solicitados
- Texto extendido de la oferta si el JSON-LD está truncado

Funciones complementarias:
- Limpieza de HTML a texto
- Normalización de fechas ISO/HTML
- Detección conservadora de modalidad si aparece en el texto

---

### Storage (Fase 3: Almacenamiento en JSON)

#### [NEW] [storage/json_storage.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/storage/json_storage.py)

Responsabilidades:
1. **Guardado diario por fuente**: `data/{fuente}/{YYYY-MM-DD}.json`
2. **Consolidación**: Merge de todas las fuentes en `data/consolidated/{YYYY-MM-DD}.json`
3. **Deduplicación**: Al guardar, verificar si el `id` ya existe en el archivo del día. Si existe, actualizar; si no, agregar. Usar diccionario indexado por `id` internamente.
4. **Formato de archivo**: JSON object con `_meta` y `ofertas`, usando `indent=2` y `ensure_ascii=False`.
5. **Metadatos del archivo**: Incluir un objeto `_meta` al inicio con: `fecha_extraccion`, `fuente`, `total_ofertas`, `version_schema`.

Ejemplo de estructura del archivo:

```json
{
  "_meta": {
    "fecha_extraccion": "2026-03-30T23:00:00Z",
    "fuente": "getonboard",
    "total_ofertas": 245,
    "version_schema": "1.0"
  },
  "ofertas": [
    { ... },
    { ... }
  ]
}
```

---

### Orquestador

#### [NEW] [main.py](file:///e:/UFRO/5to-2026/mineria-repositorio/miner-empleos/main.py)

Script principal que:
1. Acepta argumentos CLI: `--fuentes` (getonboard, chiletrabajos, bne, all), `--max-hours`, `--max-items`, `--resume`, `--output-dir`
2. Instancia los extractors según las fuentes seleccionadas, **en orden de prioridad**: Get on Board → Chiletrabajos → BNE
3. Ejecuta la extracción en secuencia (para manejar delays y presupuesto de tiempo correctamente)
4. Pasa los datos crudos por los parsers correspondientes
5. Almacena los resultados mediante `json_storage`
6. Genera un resumen al final con: ofertas extraídas por fuente, errores, tiempo total
7. Logging a consola y a archivo con `logging` module
8. **Control de tiempo global**: si se alcanza `MAX_HOURS_TOTAL`, las fuentes pendientes se saltan y se guarda lo recolectado
9. Si `--resume` está activo, los extractors que soportan checkpoint continúan desde `state/`

---

## Decisiones Resueltas

- ✅ **Get on Board**: extracción exhaustiva vía `search/jobs` + `expand[]`, sin complejidad innecesaria por categorías
- ✅ **Chiletrabajos y BNE**: controlados por presupuesto de tiempo y por checkpoint persistente para evitar reinicios completos
- ✅ **CLI de QA**: se incorpora `--max-items` para verificaciones rápidas y repetibles
- ✅ **Orden de implementación**: Get on Board → Chiletrabajos → BNE
- ✅ **Trabajando.cl**: fuera de fase 1; queda como spike técnico opcional

## Verification Plan

### Automated Tests

1. **Tests unitarios del parser**: Crear archivos de ejemplo (mock JSON/HTML) y validar que el parser transforma correctamente al esquema unificado
2. **Test de integración del extractor Get on Board**: Hacer una petición real a `/api/v0/search/jobs?per_page=1` y validar que devuelve JSON correcto
3. **Test de estado/checkpoint**: Verificar que Chiletrabajos y BNE guardan y reanudan correctamente su cursor
4. **Test de validación del esquema**: Verificar que el JSON de salida cumple el esquema definido (campos obligatorios presentes, tipos correctos)

```bash
python -m pytest tests/ -v
```

### Manual Verification

1. Ejecutar `python main.py --fuentes getonboard --max-items 10` y verificar que `data/getonboard/{fecha}.json` contiene 10 ofertas con el esquema correcto
2. Ejecutar `python main.py --fuentes chiletrabajos --max-items 5` y verificar que el detalle HTML se extrajo correctamente
3. Ejecutar `python main.py --fuentes bne --max-items 5` y verificar que el parser usa JSON-LD y completa datos desde HTML cuando falta información
4. Ejecutar `python main.py --fuentes chiletrabajos --max-items 5 --resume` y verificar que retoma desde el checkpoint en lugar de reiniciar
5. Ejecutar `python main.py --fuentes all --max-items 5` y verificar que `data/consolidated/{fecha}.json` consolida las 3 fuentes
6. Validar que la deduplicación funciona ejecutando el pipeline dos veces y comprobando que no hay duplicados
