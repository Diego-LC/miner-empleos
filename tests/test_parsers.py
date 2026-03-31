import pytest
from schema import JobOffer
from parsers.base import BaseParser
from parsers.getonboard_parser import GetOnBoardParser
from parsers.chiletrabajos_parser import ChiletrabajosParser
from parsers.bne_parser import BNEParser

class DummyParser(BaseParser):
    def parse(self, raw):
        return None

def test_base_parser_utilities():
    parser = DummyParser()
    
    # Text cleaning
    html_str = "<p>Hola<br>Mundo</p>"
    assert parser.clean_html(html_str) == "Hola\nMundo"
    
    # Salary
    text = "Sueldo ofrecido: $1.200.000 líquidos a honorarios"
    assert parser.extract_salary_from_text(text) == 1200000
    
    text2 = "Entre 800.000 y 900.000"
    assert parser.extract_salary_from_text(text2) == 900000 # Toma el max
    
    # Modality
    assert parser.detect_modality("Trabajo 100% remoto") == "remoto"
    assert parser.detect_modality("Disponibilidad para trabajar híbrido") == "híbrido"
    assert parser.detect_modality("Trabajo presencial en Las Condes") == "presencial"
    
def test_getonboard_parser():
    parser = GetOnBoardParser()
    raw = {
        "id": "123",
        "attributes": {
            "title": "Data Scientist",
            "remote_modality": "fully_remote",
            "min_salary": 1000,
            "max_salary": 2000
        },
        "links": {"public_url": "http://ejemplo.com/1"}
    }
    
    offer = parser.parse(raw)
    assert offer.id == "getonboard-123"
    assert offer.titulo == "Data Scientist"
    assert offer.modalidad == "remoto"
    assert offer.salario.min == 1000
    assert offer.salario.max == 2000
    assert offer.validate() is True

def test_chiletrabajos_parser_regex():
    parser = ChiletrabajosParser()
    raw = {
        "source_guid": "999",
        "title": "Desarrollador Python Remoto",
        "html": "<div class='box-body'>Sueldo $1.500.000 jornada completa</div>",
        "url": "http://ejemplo2.com/1"
    }
    
    offer = parser.parse(raw)
    assert offer.id == "chiletrabajos-999"
    assert offer.modalidad == "remoto" # detected from title
    assert offer.salario.max == 1500000 # detected from html desc
    assert offer.jornada == "full-time"

def test_bne_parser_json_ld():
    parser = BNEParser()
    jsonld_html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org/",
          "@type": "JobPosting",
          "title": "Ingeniero Civil",
          "description": "Buscamos Ingeniero Presencial",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Constructora XYZ"
          },
          "baseSalary": {
             "@type": "MonetaryAmount",
             "currency": "CLP",
             "value": {
                "@type": "QuantitativeValue",
                "minValue": 1000000,
                "maxValue": 2000000
             }
          }
        }
        </script>
      </head>
    </html>
    """
    raw = {
        "url": "/oferta/111",
        "html": jsonld_html
    }
    
    offer = parser.parse(raw)
    assert offer.id == "bne-111"
    assert offer.titulo == "Ingeniero Civil"
    assert offer.empresa == "Constructora XYZ"
    assert offer.salario.max == 2000000
    assert offer.salario.min == 1000000
    assert offer.salario.moneda == "CLP"
    assert offer.modalidad == "presencial" # from description text fallback
