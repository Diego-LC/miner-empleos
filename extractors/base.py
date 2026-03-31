from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import logging

class BaseExtractor(ABC):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.extracted_count = 0
        self.start_time = 0.0

    @abstractmethod
    def get_name(self) -> str:
        """Nombre de la fuente."""
        pass

    @abstractmethod
    def extract(self, max_items: Optional[int] = None, max_hours: Optional[float] = None, resume: bool = False) -> List[Dict[str, Any]]:
        """
        Extrae los datos crudos desde la fuente.
        Debe manejar sus propios checkpoints si corresponde y ceder resultados.
        """
        pass

    def check_time_limit(self, max_hours: Optional[float]) -> bool:
        """Verifica si se sobrepasó el tiempo máximo asignado."""
        if not max_hours:
            return False
        elapsed = (time.time() - self.start_time) / 3600.0
        return elapsed >= max_hours

    def _safe_request_delay(self, seconds: float):
        """Bloquea la ejecución el tiempo indicado para no sobrecargar el servidor."""
        time.sleep(seconds)
