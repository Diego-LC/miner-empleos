# Minero de Empleos Global Tech

Pipeline en Python para extraer, normalizar y consolidar ofertas laborales desde múltiples plataformas remotas y tecnológicas hacia un esquema JSON unificado. Este proyecto prioriza arquitecturas de llamadas oficiales **vía APIs REST públicas**, descartando el uso de Web Scraping por fiabilidad.

## Fuentes Soportadas (Fase 1)

1. **Get on Board**: Fuente principal LATAM y global tech. Extraída vía `api/v0/search/jobs`.
2. **Remotive**: Plataforma de trabajos remotos. Extraída vía `api/remote-jobs`. Retorna Metadata rica.
3. **RemoteOK**: Plataforma internacional global tech. Extraída vía base `/api`. 

## Características

- 🛡️ **Tolerante a limitantes APIs**: Los extractores gestionan límites de APIs sin requerir keys.
- ⏱️ **Control de Tiempo & Delays (`config.py`)**: Incluye presupuestos horarios (`MAX_HOURS_TOTAL`) para frenar la ejecución de conjuntos excesivamente largos.
- 🧹 **Normalización a Dataschema (`schema.py`)**: Estandariza modalidad (por defecto remoto), unifica fechas ISO 8601, limpia elementos HTML incrustados en las descripciones y envuelve los sueldos en límites numéricos de arreglos.
- 📁 **Almacenamiento Consolidado (`storage/json_storage.py`)**: Merge local de metadatos de las 3 plataformas con deduplicación segura por su ID nativo originario. 

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

Ejecuta el orquestador principal indicando qué fuentes deseas extraer. El orden de completado será: `Get on Board` -> `Remotive` -> `RemoteOK`.

```bash
# 1. Pipeline Completo
python main.py --fuentes all

# 2. Especificando Fuentes puntuales
python main.py --fuentes getonboard remotive

# 3. Limitar Items (Excelente para generar una muestra representativa de 50 registros)
python main.py --fuentes all --max-items 50
```

### Dónde se guarda la data extraída

El progreso se escribe en el directorio `data/` separado por fecha:

```text
data/
 ├── getonboard/2026-X-X.json       # Datos en crudo y normalizado  
 ├── remotive/2026-X-X.json
 ├── remoteok/2026-X-X.json
 └── consolidated/2026-X-X.json     # Gran dataset de las 3 APIs fusionadas
```

---

## 🧪 Pruebas (Tests Unitarios)

Se provee una suite básica de `PyTest`. (Importante: Requieren ser refactorizados para asertar la lógica de las nuevas APIs si se utilizan en CI/CD).

```bash
# Correr assertions
pytest tests/ -v
```

### Personalizar / Ajustar Configuraciones

Edita el archivo **`config.py`** si deseas ajustar manualmente los retardos (delay), los endpoints oficiales o los user-agents solicitados en las documentaciones de las API para evitar baneos pasivos. Creado sin usar navegadores sin cabeza que lo ralentizan (como Playwright/Selenium).
