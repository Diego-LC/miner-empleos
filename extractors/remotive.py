from typing import List, Dict, Any, Optional
import time
import requests
import json
from extractors.base import BaseExtractor
from config import REMOTIVE_API_URL, REQUEST_TIMEOUT, BASE_HEADERS

class RemotiveExtractor(BaseExtractor):
    def get_name(self) -> str:
        return "remotive"

    def extract(self, max_items: Optional[int] = None, max_hours: Optional[float] = None, resume: bool = False) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando extracción de Remotive...")
        self.start_time = time.time()
        
        try:
            # Remotive permite extraer todo en una sola petición sin paginar
            endpoint = REMOTIVE_API_URL
            if max_items:
                endpoint += f"?limit={max_items}"
                
            self.logger.info(f"Llamando a {endpoint}")
            resp = requests.get(endpoint, headers=BASE_HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            
            jobs = data.get("jobs", [])
            self.logger.info(f"Se obtuvieron {len(jobs)} ofertas crudas desde Remotive.")
            
            if max_items and len(jobs) > max_items:
                jobs = jobs[:max_items]

            return jobs

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error HTTP extrayendo de Remotive: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parseando JSON de Remotive: {e}")
            return []
