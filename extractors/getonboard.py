import requests
import time
from typing import List, Dict, Any, Optional
from extractors.base import BaseExtractor
from config import GETONBOARD_BASE_URL, GETONBOARD_PER_PAGE, BASE_HEADERS, REQUEST_TIMEOUT

class GetOnBoardExtractor(BaseExtractor):
    def get_name(self) -> str:
        return "getonboard"

    def extract(self, max_items: Optional[int] = None, max_hours: Optional[float] = None, resume: bool = False) -> List[Dict[str, Any]]:
        self.start_time = time.time()
        self.extracted_count = 0
        all_jobs = []
        
        try:
            # Obtener todas las categorías para iterar
            cat_response = requests.get(f"{GETONBOARD_BASE_URL}/categories", headers=BASE_HEADERS, timeout=REQUEST_TIMEOUT)
            cat_response.raise_for_status()
            categories = [c["id"] for c in cat_response.json().get("data", [])]
        except Exception as e:
            self.logger.error(f"No se pudieron obtener las categorías: {e}")
            return all_jobs
            
        self.logger.info(f"Se iterará sobre {len(categories)} categorías para una extracción exhaustiva.")

        for category in categories:
            page = 1
            while True:
                # Check Limits
                if getattr(self, "check_time_limit", lambda x: False)(max_hours):
                    self.logger.warning(f"Límite de tiempo alcanzado ({max_hours} horas). Deteniendo extracción en categoría {category}, página {page}.")
                    return all_jobs
                
                if max_items and self.extracted_count >= max_items:
                    self.logger.info(f"Límite de items alcanzado ({max_items}). Deteniendo extracción completa.")
                    return all_jobs
                    
                self.logger.info(f"[{category}] Buscando ofertas, página {page}...")
                
                try:
                    params = {
                        "per_page": GETONBOARD_PER_PAGE,
                        "page": page,
                        "expand[]": ["company", "seniority", "modality", "location_cities", "tags"]
                    }
                    
                    url = f"{GETONBOARD_BASE_URL}/categories/{category}/jobs"
                    response = requests.get(url, headers=BASE_HEADERS, params=params, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    
                    data = response.json()
                    jobs = data.get("data", [])
                    
                    if not jobs:
                        self.logger.info(f"[{category}] Sin más ofertas.")
                        break
                        
                    for job in jobs:
                        all_jobs.append(job)
                        self.extracted_count += 1
                        if max_items and self.extracted_count >= max_items:
                            break

                    meta = data.get("meta", {})
                    current_page = meta.get("page", page)
                    total_pages = meta.get("total_pages", page)
                    
                    if current_page >= total_pages or len(jobs) == 0:
                        break
                    
                    page += 1
                    self._safe_request_delay(0.5)
                    
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Error HTTP consumiendo API de GetOnBoard para categoría {category}: {e}")
                    self.logger.warning("Pasando a la siguiente categoría...")
                    break
                except Exception as e:
                     self.logger.error(f"Error parseando JSON en GetOnBoard: {e}")
                     break
                     
        return all_jobs
