from typing import List, Dict, Any, Optional
import time
import requests
import json
from extractors.base import BaseExtractor
from config import REMOTEOK_API_URL, REQUEST_TIMEOUT, BASE_HEADERS

class RemoteOkExtractor(BaseExtractor):
    def get_name(self) -> str:
        return "remoteok"

    def extract(self, max_items: Optional[int] = None, max_hours: Optional[float] = None, resume: bool = False) -> List[Dict[str, Any]]:
        self.logger.info("Iniciando extracción de RemoteOK...")
        self.start_time = time.time()
        
        try:
            # RemoteOK entrega todo en una sola petición
            self.logger.info(f"Llamando a {REMOTEOK_API_URL}")
            resp = requests.get(REMOTEOK_API_URL, headers=BASE_HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            
            # El primer registro de RemoteOK es un "legal notice", no un Job.
            if len(data) > 0 and "legal" in data[0]:
                jobs = data[1:]
            else:
                jobs = data

            self.logger.info(f"Se obtuvieron {len(jobs)} ofertas crudas desde RemoteOK.")
            
            if max_items and len(jobs) > max_items:
                jobs = jobs[:max_items]

            return jobs

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error HTTP extrayendo de RemoteOK: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parseando JSON de RemoteOK: {e}")
            return []
