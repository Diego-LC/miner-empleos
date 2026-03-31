import os

# Rutas principales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATE_DIR = os.path.join(BASE_DIR, "state")

# Configuraciones de requests
REQUEST_DELAY = 1.0  # Delay base entre peticiones HTTP (segundos)
REQUEST_TIMEOUT = 20  # Timeout por request en segundos
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 JobMiner/1.0"

# Rutas y Endpoints
GETONBOARD_BASE_URL = "https://www.getonbrd.com/api/v0"
GETONBOARD_PER_PAGE = 120

CHILETRABAJOS_RSS_URL = "https://www.chiletrabajos.cl/rss.xml"
CHILETRABAJOS_BASE_URL = "https://www.chiletrabajos.cl"

BNE_BASE_URL = "https://www.bne.gob.cl"
BNE_SITEMAP_URL = "https://www.bne.gob.cl/sitemap.xml"

# Opciones de control del orquestador
CHECKPOINT_EVERY = 100               # Cada cuántas ofertas guardar checkpoint
MAX_HOURS_PER_SOURCE = 2.0           # Presupuesto de tiempo max por fuente
MAX_HOURS_TOTAL = 0.1                # Presupuesto de tiempo total
MAX_ITEMS_OVERRIDE = None            # Override dinámico vía CLI

# Headers HTTP base
BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7",
}
