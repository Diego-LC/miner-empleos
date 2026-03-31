# Minero de Empleos Chile/LatAm

Pipeline en Python para extraer, normalizar y consolidar ofertas laborales desde múltiples plataformas hacia un esquema JSON unificado.

## Fuentes Soportadas (Fase 1)

1. **Get on Board**: Extracción exhaustiva vía API `{URL}/search/jobs`.
2. **Chiletrabajos**: Extracción híbrida mediante RSS Feed (`/rss.xml`) para listado masivo y scraping HTML (BeautifulSoup) para el detalle de la oferta.
3. **BNE Chile**: Traversing público vía `sitemap.xml` más extracción híbrida priorizando `JobPosting` JSON-LD estructural combinado con fallbacks a etiquetas de texto HTML.

## Características

- 🛡️ **Extracción Tolerante a Fallos & Checkpoints**: Los extractores (ej. Chiletrabajos, BNE) guardan su estado (`state/cursor.json`) tras un lote de peticiones. Si el proceso falla, aborta o se detiene, puede reanudarse transparentemente.
- ⏱️ **Control de Tiempo & Delays (`config.py`)**: Incluye presupuestos horarios (`MAX_HOURS_PER_SOURCE`, `MAX_HOURS_TOTAL`) para frenar la ejecución sin perder los datos ya scrapeados si el servidor de origen tiene alta latencia o el volumen es masivo.
- 🧹 **Normalización a Dataschema (`schema.py`)**: Estandariza modalidad (remoto/híbrido/presencial), tipos de jornada, ubicación en `[Ciudad, Región, País]`, limpiado de HTML e inferencia Regex del salario con priorización del `max_salary`.
- 📁 **Almacenamiento Consolidado (`storage/json_storage.py`)**: Merge local de metadatos con deduplicación por `id`. 

---

## 🛠 Instalación

El pipeline funciona con librerías nativas estándar (`requests`, `beautifulsoup4`, `lxml`):

```bash
# Entorno virtual (opcional pero recomendado)
python -m venv .venv

# Activar en Windows
.\.venv\Scripts\activate

# Activar en macOS/Linux
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🚀 Uso Rápido (CLI)

Ejecuta el orquestador principal indicando qué fuentes deseas extraer. Las fuentes serán ejecutadas bajo un orden de prioridad heurística estricto: `Get on Board` -> `Chiletrabajos` -> `BNE`.

```bash
# 1. Pipeline Completo (Tomará el presupuesto de horas de config.py) 
python main.py --fuentes all

# 2. Especificando Fuentes puntuales
python main.py --fuentes getonboard chiletrabajos

# 3. Limitar Items (Excelente para pruebas técnicas rápidas/QA)
python main.py --fuentes all --max-items 10

# 4. Modificar Límite de Horas en caliente
python main.py --fuentes bne --max-hours 1.5

# 5. Reanudar Extracción desde los Checkpoints (State)
python main.py --fuentes chiletrabajos bne --resume
```

### Dónde se guarda la data extraída

El progreso se escribe en el directorio `data/` separado por fecha:

```text
data/
 ├── getonboard/2026-X-X.json       # Datos en crudo+normalizado  
 ├── chiletrabajos/2026-X-X.json
 ├── bne/2026-X-X.json
 └── consolidated/2026-X-X.json     # Merge del día con totales
```

---

## 🧪 Pruebas (Tests Unitarios)

Se provee una suite básica de `PyTest` implementada para verificar los fallbacks de los parsers (Regex de modaliad, salarios líquidos explícitos en HTML) y la persistencia segura en los Scrappers.

```bash
# Correr assertions
pytest tests/ -v
```

### Personalizar / Ajustar Configuraciones

Edita el archivo **`config.py`** si deseas ajustar manualmente los retardos (delay), los user-agents o los presupuestos base para los flujos de extracción. Creado sin usar navegadores sin cabeza que lo ralentizan (como Playwright/Selenium).
