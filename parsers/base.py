from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import re
from bs4 import BeautifulSoup
from schema import JobOffer

class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_data: Dict[str, Any]) -> JobOffer:
        """Convierte datos crudos de la fuente al esquema JobOffer."""
        pass

    def clean_html(self, html_str: Optional[str]) -> Optional[str]:
        if not html_str:
            return None
        soup = BeautifulSoup(html_str, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        # Limpieza de exceso de saltos de línea
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    def extract_salary_from_text(self, text: str) -> Optional[int]:
        """Intenta extraer un salario numérico base mensual a partir del texto."""
        # TODO: Mejorar heurísticas según la fuente
        # Ejemplo: $750.000, 1.200.000, etc.
        if not text:
            return None
        matches = re.findall(r'\$?(\d{1,3}(?:\.\d{3})+)', text)
        if matches:
            # tomar el valor mayor de la ocurrencia (asumiendo que es el sueldo y no horas extra o bono min)
            salarios = []
            for match in matches:
                val = int(match.replace('.', ''))
                if val > 100000: # Heurística: sueldos chilenos son > 100k
                    salarios.append(val)
            if salarios:
                return max(salarios)
        return None

    def detect_modality(self, text: str) -> Optional[str]:
        """Detecta modalidad (remoto, presencial, híbrido)."""
        if not text:
            return None
        text_lower = text.lower()
        if 'hibrid' in text_lower or 'híbrid' in text_lower:
            return 'híbrido'
        if 'remot' in text_lower or 'teletrabajo' in text_lower or 'homeoffice' in text_lower:
            return 'remoto'
        if 'presencial' in text_lower:
            return 'presencial'
        return None

    def detect_jornada(self, text: str) -> Optional[str]:
        """Detecta la jornada laboral"""
        if not text:
            return None
        text_lower = text.lower()
        if 'full-time' in text_lower or 'jornada completa' in text_lower or 'fulltime' in text_lower:
            return 'full-time'
        if 'part-time' in text_lower or 'media jornada' in text_lower or 'partime' in text_lower:
            return 'part-time'
        return None
