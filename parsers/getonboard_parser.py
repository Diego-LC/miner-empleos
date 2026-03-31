from typing import Dict, Any, Optional
from datetime import datetime
from parsers.base import BaseParser
from schema import JobOffer, JobLocation, JobSalary

class GetOnBoardParser(BaseParser):
    def parse(self, raw_data: Dict[str, Any]) -> JobOffer:
        attributes = raw_data.get("attributes", {})
        rels = raw_data.get("relationships", {})
        links = raw_data.get("links", {})
        
        # ID and URL
        job_id = f"getonboard-{raw_data.get('id', '')}"
        url = links.get("public_url", "")
        
        # Title
        titulo = attributes.get("title", "Título no disponible")

        # Company
        empresa_name = None
        company_rel = rels.get("company", {}).get("data", {})
        if company_rel:
            empresa_name = company_rel.get("attributes", {}).get("name")
            
        # Description, requisites, and benefits
        desc = self.clean_html(attributes.get("description", ""))
        reqs = self.clean_html(attributes.get("functions", ""))
        desirable = self.clean_html(attributes.get("desirable", ""))
        if reqs and desirable:
            reqs += "\n\nOpcionales/Deseables:\n" + desirable
        elif desirable:
            reqs = desirable
            
        benefits = self.clean_html(attributes.get("benefits", ""))
        
        # Dates
        pub_epoch_str = attributes.get("published_at")
        fecha_pub = None
        if pub_epoch_str:
            try:
                from datetime import timezone
                fecha_pub = datetime.fromtimestamp(int(pub_epoch_str), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except (ValueError, TypeError):
                pass
                
        # Category
        categoria = attributes.get("category_name", None)
        
        # Salary
        min_salary = attributes.get("min_salary")
        max_salary = attributes.get("max_salary")
        salario = JobSalary(
            min=min_salary if min_salary else None,
            max=max_salary if max_salary else None
        )
        
        # Modality
        modality = None
        remote_status = attributes.get("remote_modality")
        if remote_status == "fully_remote":
            modality = "remoto"
        elif remote_status == "hybrid":
            modality = "híbrido"
        elif remote_status == "no_remote":
             modality = "presencial"
        else:
            mod_rel = rels.get("modality", {}).get("data", {})
            if mod_rel:
                modality = mod_rel.get("attributes", {}).get("name")
                
        # Seniority
        seniority = None
        sen_rel = rels.get("seniority", {}).get("data", {})
        if sen_rel:
             seniority = sen_rel.get("attributes", {}).get("name")
             
        # Location
        ciudad = None
        pais = "Chile" # fallback de la constante, pero intentamos sacar el real
        
        countries = attributes.get("countries", [])
        if countries:
            pais = ", ".join(countries)
            
        loc_rel = rels.get("location_cities", {}).get("data", [])
        if loc_rel and isinstance(loc_rel, list) and len(loc_rel) > 0:
            ciudades = []
            for loc in loc_rel:
                cname = loc.get("attributes", {}).get("name")
                if cname: ciudades.append(cname)
            if ciudades:
                ciudad = ", ".join(ciudades)
        
        ubicacion = JobLocation(ciudad=ciudad, pais=pais)
        
        # Tags
        tags = []
        tags_rel = rels.get("tags", {}).get("data", [])
        if tags_rel and isinstance(tags_rel, list):
             for tag in tags_rel:
                  tname = tag.get("attributes", {}).get("name")
                  if tname: tags.append(tname)

        offer = JobOffer(
            id=job_id,
            fuente="getonboard",
            titulo=titulo,
            empresa=empresa_name,
            fecha_publicacion=fecha_pub,
            ubicacion=ubicacion,
            modalidad=modality,
            salario=salario,
            seniority=seniority,
            categoria=categoria,
            descripcion=desc,
            requisitos=reqs,
            beneficios=benefits,
            tags=tags,
            url=url
        )
        
        return offer
