import requests
import time
import json
import os
from typing import List, Dict, Any, Optional
from lxml import etree
from bs4 import BeautifulSoup
from extractors.base import BaseExtractor
from config import CHILETRABAJOS_RSS_URL, BASE_HEADERS, REQUEST_TIMEOUT, STATE_DIR, CHECKPOINT_EVERY, REQUEST_DELAY

class ChiletrabajosExtractor(BaseExtractor):
    def get_name(self) -> str:
        return "chiletrabajos"
        
    def __init__(self, logger=None):
        super().__init__(logger)
        self.state_file = os.path.join(STATE_DIR, "chiletrabajos.cursor.json")
        self.checkpoint_state = {
            "rss_index": 0,
            "last_guid": None,
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
                
    def save_state(self, rss_index: int, last_guid: str):
        self.checkpoint_state = {
             "rss_index": rss_index,
             "last_guid": last_guid,
             "last_timestamp": time.time()
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
             json.dump(self.checkpoint_state, f)

    def extract(self, max_items: Optional[int] = None, max_hours: Optional[float] = None, resume: bool = False) -> List[Dict[str, Any]]:
        self.start_time = time.time()
        self.extracted_count = 0
        all_jobs = []
        
        self.logger.info("Descargando RSS de Chiletrabajos...")
        try:
             response = requests.get(CHILETRABAJOS_RSS_URL, headers=BASE_HEADERS, timeout=REQUEST_TIMEOUT)
             response.raise_for_status()
             
             # Parsear XML
             root = etree.fromstring(response.content)
             items = root.xpath('//item')
             self.logger.info(f"Encontrados {len(items)} items en el RSS.")
             
        except Exception as e:
             self.logger.error(f"Error descargando o parseando RSS: {e}")
             return all_jobs
             
        # Orden original es como venga en RSS (teóricamente los más nuevos primero)
        start_index = 0
        if resume and self.checkpoint_state.get("rss_index", 0) > 0:
             start_index = self.checkpoint_state["rss_index"]
             self.logger.info(f"Reanudando desde índice {start_index}...")

        consecutive_errors = 0
             
        for idx in range(start_index, len(items)):
             # Checks de parada globales
             if getattr(self, "check_time_limit", lambda x: False)(max_hours):
                 self.logger.warning(f"Límite de tiempo alcanzado ({max_hours} horas). Deteniendo.")
                 break
             if max_items and self.extracted_count >= max_items:
                 self.logger.info(f"Límite de items alcanzado ({max_items}). Deteniendo extractores del RSS.")
                 break
                 
             item = items[idx]
             
             guid_node = item.xpath('guid/text()')
             guid = guid_node[0] if guid_node else str(idx)
             
             link_node = item.xpath('link/text()')
             if not link_node:
                 continue
             url = link_node[0]
             
             # Obtener el HTML de detalle
             try:
                 det_response = requests.get(url, headers=BASE_HEADERS, timeout=REQUEST_TIMEOUT)
                 det_response.raise_for_status()
                 html_content = det_response.text
                 
                 # Extraer metadata básica del RSS
                 title = item.xpath('title/text()')[0] if item.xpath('title/text()') else ""
                 description = item.xpath('description/text()')[0] if item.xpath('description/text()') else ""
                 category = item.xpath('category/text()')[0] if item.xpath('category/text()') else ""
                 pub_date = item.xpath('pubDate/text()')[0] if item.xpath('pubDate/text()') else ""

                 raw_job = {
                      "source_guid": guid,
                      "url": url,
                      "title": title,
                      "description": description,
                      "category": category,
                      "pubDate": pub_date,
                      "html": html_content
                 }
                 
                 all_jobs.append(raw_job)
                 self.extracted_count += 1
                 consecutive_errors = 0
                 
                 if self.extracted_count % CHECKPOINT_EVERY == 0:
                      self.save_state(idx + 1, guid)
                      self.logger.info(f"Progreso Chiletrabajos: {self.extracted_count} ofertas procesadas y guardadas en checkpoint...")
                      
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
                 self.logger.error("Demasiados errores consecutivos. Abortando extracción para evitar bloqueo.")
                 break
                 
        self.save_state(start_index + self.extracted_count, None)
        return all_jobs
