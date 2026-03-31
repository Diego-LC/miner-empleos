import json
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from parsers.base import BaseParser
from schema import JobOffer, JobLocation, JobSalary

class BNEParser(BaseParser):
    def parse(self, raw_data: Dict[str, Any]) -> JobOffer:
        url = raw_data.get('url', '')
        # Extraer un ID de la URL (ej: /oferta/12345)
        bne_id = url.split('/')[-1] if url else "unknown"
        job_id = f"bne-{bne_id}"
        
        html = raw_data.get("html", "")
        soup = BeautifulSoup(html, "html.parser")
        
        # Buscar el JSON-LD de JobPosting
        json_ld_data = {}
        for script in soup.find_all("script", type="application/ld+json"):
             try:
                 obj = json.loads(script.string)
                 if isinstance(obj, dict) and obj.get("@type") == "JobPosting":
                     json_ld_data = obj
                     break
             except Exception:
                 continue
                 
        # Parseo con JSON-LD como base primaria
        titulo = json_ld_data.get("title", "")
        
        # fallback titulo si jsonld falla
        if not titulo:
            h1 = soup.find("h1")
            titulo = h1.text.strip() if h1 else "Título no disponible"
            
        empresa_name = None
        org = json_ld_data.get("hiringOrganization", {})
        if org:
            empresa_name = org.get("name")
            
        fecha_pub = json_ld_data.get("datePosted")
        
        desc = json_ld_data.get("description", "")
        desc = self.clean_html(desc)
        
        # ubicacion
        ciudad = None
        region = None
        pais = "Chile"
        loc = json_ld_data.get("jobLocation", {}).get("address", {})
        if loc:
             ciudad = loc.get("addressLocality")
             region = loc.get("addressRegion")
             pais = loc.get("addressCountry", pais)
             
        ubicacion = JobLocation(ciudad=ciudad, region=region, pais=pais)
        
        # Opcional HTML info (fallback o complementario)
        # La jornada y modalidad no siempre vienen claras en el json_ld de BNE, buscar en texto
        mod_inf = self.detect_modality(desc)
        jor_inf = self.detect_jornada(desc)
        
        if not mod_inf:
             mod_inf = self.detect_modality(titulo)
        if not jor_inf:
             jor_inf = self.detect_jornada(titulo)
             
        # Salario
        # BNE usa baseSalary
        salario = JobSalary()
        base_sal = json_ld_data.get("baseSalary", {})
        if base_sal:
             val = base_sal.get("value", {})
             if isinstance(val, dict):
                 salario.min = val.get("minValue")
                 salario.max = val.get("maxValue")
                 salario.moneda = base_sal.get("currency")
             else:
                 # si value es numero directo
                 try:
                     salario.max = int(val)
                     salario.moneda = base_sal.get("currency")
                 except:
                     pass
                     
        if not salario.max and desc:
             salario_base = self.extract_salary_from_text(desc)
             if salario_base:
                 salario.max = salario_base
                 salario.moneda = "CLP"
                 
        offer = JobOffer(
            id=job_id,
            fuente="bne",
            titulo=titulo,
            empresa=empresa_name,
            fecha_publicacion=fecha_pub,
            ubicacion=ubicacion,
            modalidad=mod_inf,
            jornada=jor_inf,
            salario=salario,
            descripcion=desc,
            url=url
        )
        return offer
