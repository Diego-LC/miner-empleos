from typing import Dict, Any, Optional
from parsers.base import BaseParser
from schema import JobOffer, JobLocation, JobSalary
from dateutil import parser as date_parser

class RemotiveParser(BaseParser):
    def parse(self, raw_data: Dict[str, Any]) -> JobOffer:
        # Extraer salario base si viene como string libre ("$90k - $120k / year")
        raw_salary = raw_data.get("salary")
        salary_obj = JobSalary()
        
        if raw_salary:
            salary_obj.periodo = raw_salary
            # La 2da transformación en el futuro extraerá min/max numerico

        fecha_pub = None
        raw_date = raw_data.get("publication_date")
        if raw_date:
            try:
                # ISO offset
                fecha_pub = date_parser.parse(raw_date).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass

        location_req = raw_data.get("candidate_required_location")
        
        offer = JobOffer(
            id=f"remotive-{raw_data.get('id', '')}",
            fuente="remotive",
            url=raw_data.get("url", ""),
            titulo=raw_data.get("title", "Desconocido"),
            empresa=raw_data.get("company_name"),
            fecha_publicacion=fecha_pub,
            ubicacion=JobLocation(pais=location_req, ciudad=None, region=None),
            modalidad="remoto",
            jornada=raw_data.get("job_type", "").lower(),
            salario=salary_obj,
            categoria=raw_data.get("category"),
            descripcion=self.clean_html(raw_data.get("description")),
            tags=raw_data.get("tags", []),
        )
        return offer
