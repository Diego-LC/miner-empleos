import requests
import time
import json
import os
from lxml import etree
from typing import List, Dict, Any, Optional
from extractors.base import BaseExtractor
from config import BNE_SITEMAP_URL, BASE_HEADERS, REQUEST_TIMEOUT, STATE_DIR, CHECKPOINT_EVERY, REQUEST_DELAY

class BNEExtractor(BaseExtractor):
    def get_name(self) -> str:
        return "bne"

    def __init__(self, logger=None):
        super().__init__(logger)
        self.state_file = os.path.join(STATE_DIR, "bne.cursor.json")
        self.checkpoint_state = {
            "sitemap_index": 0,
            "last_offer_url": None,
            "last_timestamp": None
        }
        self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                     self.checkpoint_state = json.load(f)
            except Exception:
                pass
                
    def save_state(self, sitemap_index: int, last_url: str):
        self.checkpoint_state = {
             "sitemap_index": sitemap_index,
             "last_offer_url": last_url,
             "last_timestamp": time.time()
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
             json.dump(self.checkpoint_state, f)

    def extract(self, max_items: Optional[int] = None, max_hours: Optional[float] = None, resume: bool = False) -> List[Dict[str, Any]]:
        self.start_time = time.time()
        self.extracted_count = 0
        all_jobs = []
        
        self.logger.info("Descargando sitemap de BNE Chile...")
        try:
             response = requests.get(BNE_SITEMAP_URL, headers=BASE_HEADERS, timeout=REQUEST_TIMEOUT)
             response.raise_for_status()
             
             # Parse XML using namespaces normally found in sitemaps
             root = etree.fromstring(response.content)
             # Sitemaps use default namespace mapping
             ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
             urls = root.xpath('//ns:loc/text()', namespaces=ns)
             
             # Filtrar solo ofertas
             ofertas_urls = [u for u in urls if "/oferta/" in u]
             self.logger.info(f"Encontradas {len(ofertas_urls)} rutas de ofertas en el sitemap.")
             
        except Exception as e:
             self.logger.error(f"Error descargando o parseando sitemap de BNE: {e}")
             return all_jobs
             
        start_index = 0
        if resume and self.checkpoint_state.get("sitemap_index", 0) > 0:
             start_index = self.checkpoint_state["sitemap_index"]
             self.logger.info(f"Reanudando desde índice {start_index}...")

        consecutive_errors = 0
             
        for idx in range(start_index, len(ofertas_urls)):
             # Checks de parada globales
             if getattr(self, "check_time_limit", lambda x: False)(max_hours):
                 self.logger.warning(f"Límite de tiempo alcanzado ({max_hours} horas). Deteniendo BNE.")
                 break
             if max_items and self.extracted_count >= max_items:
                 self.logger.info(f"Límite de items alcanzado ({max_items}). Deteniendo extractores de BNE.")
                 break
                 
             url = ofertas_urls[idx]
             
             try:
                 det_response = requests.get(url, headers=BASE_HEADERS, timeout=REQUEST_TIMEOUT)
                 det_response.raise_for_status()
                 
                 raw_job = {
                      "url": url,
                      "html": det_response.text
                 }
                 
                 all_jobs.append(raw_job)
                 self.extracted_count += 1
                 consecutive_errors = 0
                 
                 if self.extracted_count % CHECKPOINT_EVERY == 0:
                      self.save_state(idx + 1, url)
                      self.logger.info(f"Progreso BNE: {self.extracted_count} ofertas procesadas y guardadas en checkpoint...")
                      
                 self._safe_request_delay(REQUEST_DELAY)

             except requests.exceptions.HTTPError as he:
                 if he.response.status_code == 404:
                     self.logger.warning(f"Oferta 404, omitiendo: {url}")
                 else:
                     self.logger.error(f"Error HTTP {he.response.status_code} extrañendo {url}")
                     consecutive_errors += 1
             except Exception as e:
                 self.logger.error(f"Error extrayendo {url}: {e}")
                 consecutive_errors += 1
                 
             if consecutive_errors >= 3:
                 self.logger.error("Demasiados errores consecutivos. Abortando extracción para evitar bloqueo de BNE.")
                 break
                 
        self.save_state(start_index + self.extracted_count, None)
        return all_jobs
