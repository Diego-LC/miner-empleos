from typing import Dict, Any, Optional
from parsers.base import BaseParser
from schema import JobOffer, JobLocation, JobSalary
from dateutil import parser as date_parser

class RemoteOkParser(BaseParser):
    def parse(self, raw_data: Dict[str, Any]) -> JobOffer:
        # RemoteOK a veces tiene epoch o date
        fecha_pub = None
        raw_date = raw_data.get("date")
        if raw_date:
            try:
                # El ISO puede tener offsets, pasamos a string UTC para estandarizar
                fecha_pub = date_parser.parse(raw_date).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass

        location_req = raw_data.get("location")
        
        salary_obj = JobSalary(
            min=raw_data.get("salary_min"),
            max=raw_data.get("salary_max"),
            moneda="USD",
            periodo="anual"
        )
        
        # Tags a veces vienen como lista de strings
        tags = raw_data.get("tags")
        if isinstance(tags, str):
            tags = [tags]
        elif not tags:
            tags = []
            
        slug = raw_data.get("id") or raw_data.get("slug", "unknown")
            
        offer = JobOffer(
            id=f"remoteok-{slug}",
            fuente="remoteok",
            url=raw_data.get("url", raw_data.get("apply_url", "")),
            titulo=raw_data.get("position", "Desconocido"),
            empresa=raw_data.get("company"),
            fecha_publicacion=fecha_pub,
            ubicacion=JobLocation(pais=location_req, ciudad=None, region=None),
            modalidad="remoto",
            jornada="full-time", # RemoteOk asume remote full-time mayormente
            salario=salary_obj,
            categoria=None,  # Suele venir todo en tags
            descripcion=self.clean_html(raw_data.get("description")),
            tags=tags,
        )
        return offer
