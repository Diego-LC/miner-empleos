from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

@dataclass
class JobSalary:
    min: Optional[int] = None
    max: Optional[int] = None
    moneda: Optional[str] = None
    periodo: Optional[str] = None

@dataclass
class JobLocation:
    ciudad: Optional[str] = None
    region: Optional[str] = None
    pais: Optional[str] = "Chile"

@dataclass
class JobOffer:
    id: str  # id unívoco: fuente-original_id
    fuente: str
    titulo: str
    empresa: Optional[str] = None
    fecha_publicacion: Optional[str] = None  # ISO 8601
    ubicacion: JobLocation = field(default_factory=JobLocation)
    modalidad: Optional[str] = None
    jornada: Optional[str] = None
    salario: JobSalary = field(default_factory=JobSalary)
    seniority: Optional[str] = None
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    requisitos: Optional[str] = None
    beneficios: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    url: str = ""
    fecha_extraccion: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la oferta a diccionario y elimina nulos en listas."""
        return asdict(self)
    
    def validate(self) -> bool:
        """Verifica que los campos obligatorios estén."""
        return bool(self.id and self.fuente and self.titulo and self.url)
