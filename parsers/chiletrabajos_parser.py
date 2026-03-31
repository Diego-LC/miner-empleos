from typing import Dict, Any, Optional
import re
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from parsers.base import BaseParser
from schema import JobOffer, JobLocation, JobSalary

class ChiletrabajosParser(BaseParser):
    def parse(self, raw_data: Dict[str, Any]) -> JobOffer:
        job_id = f"chiletrabajos-{raw_data.get('source_guid', '')}"
        url = raw_data.get('url', '')
        
        # Básicos del RSS
        titulo = raw_data.get("title", "").strip()
        categoria = raw_data.get("category", "")
        
        pub_str = raw_data.get("pubDate", "")
        fecha_pub = None
        if pub_str:
             try:
                 fecha_pub = date_parser.parse(pub_str).strftime("%Y-%m-%dT%H:%M:%SZ")
             except Exception:
                 pass
                 
        html = raw_data.get("html", "")
        soup = BeautifulSoup(html, "html.parser")
        
        empresa_name = None
        ciudad = None
        
        # Extracción específica desde el HTML de Chiletrabajos
        # La empresa suele venir en un span con class="text-primary" o dentro de un tag-label
        # (requeriría ajuste si el markup cambió, usamos fallback)
        company_tag = soup.find("a", href=lambda h: h and "/empresa/" in h)
        if company_tag:
             empresa_name = company_tag.text.strip()
             
        # Ubicación suele estar en un enlace de ciudad
        city_tag = soup.find("a", href=lambda h: h and "/ciudad/" in h)
        if city_tag:
             ciudad = city_tag.text.strip()
             
        # Descripción: asumiendo que el texto principal está en block
        desc_div = soup.find("div", class_="box-body") or soup.find("div", class_="description")
        desc_text = self.clean_html(str(desc_div)) if desc_div else self.clean_html(raw_data.get("description", ""))
        
        # Inferir salario (en Chiletrabajos no suele estar el campo estructurado)
        salario_val = self.extract_salary_from_text(desc_text)
        salario = JobSalary(max=salario_val, moneda="CLP" if salario_val else None, periodo="mensual" if salario_val else None)
        
        # Modalidad y Jornada
        mod_inf = self.detect_modality(desc_text)
        jor_inf = self.detect_jornada(desc_text)
        
        # Algunas veces en el título lo dice (ej: "Desarrollador - Remoto")
        if not mod_inf:
            mod_inf = self.detect_modality(titulo)
        if not jor_inf:
            jor_inf = self.detect_jornada(titulo)
            
        ubicacion = JobLocation(ciudad=ciudad, pais="Chile")
        
        offer = JobOffer(
            id=job_id,
            fuente="chiletrabajos",
            titulo=titulo,
            empresa=empresa_name,
            fecha_publicacion=fecha_pub,
            ubicacion=ubicacion,
            modalidad=mod_inf,
            jornada=jor_inf,
            salario=salario,
            categoria=categoria,
            descripcion=desc_text,
            url=url
        )
        return offer
