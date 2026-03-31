import argparse
import logging
import sys
import time
from typing import List
from config import MAX_HOURS_PER_SOURCE, MAX_HOURS_TOTAL

from storage.json_storage import JSONStorage
from extractors.getonboard import GetOnBoardExtractor
from parsers.getonboard_parser import GetOnBoardParser

from extractors.remotive import RemotiveExtractor
from parsers.remotive_parser import RemotiveParser

from extractors.remoteok import RemoteOkExtractor
from parsers.remoteok_parser import RemoteOkParser

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Handler de consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Podría sumarse un FileHandler aquí a choice

def main():
    parser = argparse.ArgumentParser(description="Job Extractor Pipeline Global Tech")
    parser.add_argument("--fuentes", nargs="+", choices=["getonboard", "remotive", "remoteok", "all"], default=["all"], help="Fuentes a extraer")
    parser.add_argument("--max-hours", type=float, default=MAX_HOURS_PER_SOURCE, help="Tiempo máximo por fuente en horas")
    parser.add_argument("--max-total-hours", type=float, default=MAX_HOURS_TOTAL, help="Tiempo máximo global en horas")
    parser.add_argument("--max-items", type=int, default=None, help="Límite máximo de ofertas por fuente (útil para pruebas)")
    parser.add_argument("--resume", action="store_true", help="Reanudar extracciones usando descargas previas (si la fuente lo soporta)")
    
    args = parser.parse_args()
    setup_logger()
    logger = logging.getLogger("main")
    
    pipeline_start = time.time()
    
    sources_to_run = args.fuentes
    if "all" in sources_to_run:
        sources_to_run = ["getonboard", "remotive", "remoteok"]
        
    logger.info(f"Iniciando pipeline para: {', '.join(sources_to_run)}")
    logger.info(f"Opciones: max_hours={args.max_hours}, max_items={args.max_items}, resume={args.resume}")
    
    storage = JSONStorage()
    
    pipeline_config = {
        "getonboard": (GetOnBoardExtractor, GetOnBoardParser),
        "remotive": (RemotiveExtractor, RemotiveParser),
        "remoteok": (RemoteOkExtractor, RemoteOkParser)
    }

    results_summary = {}
    ordered_sources = []
    
    # Priority enforcement: GetOnBoard -> Remotive -> RemoteOK
    ordered_preferences = ["getonboard", "remotive", "remoteok"]
    for src in ordered_preferences:
        if src in sources_to_run:
             ordered_sources.append(src)

    for source_name in ordered_sources:
        # Check global time
        global_elapsed = (time.time() - pipeline_start) / 3600.0
        if global_elapsed >= args.max_total_hours:
             logger.warning(f"Se alcanzó el presupuesto global de {args.max_total_hours} horas. Saltando fuentes pendientes.")
             break
             
        logger.info(f"--- Iniciando extracción de {source_name} ---")
        ExtractorClass, ParserClass = pipeline_config[source_name]
        
        extractor = ExtractorClass()
        parser_inst = ParserClass()
        
        # Ejecutar Extracción
        raw_items = extractor.extract(
            max_items=args.max_items, 
            max_hours=args.max_hours, 
            resume=args.resume
        )
        
        logger.info(f"Extracción finalizada para {source_name}. Total crudos: {len(raw_items)}")
        
        if not raw_items:
             logger.info(f"Sin datos nuevos de {source_name}.")
             results_summary[source_name] = {"extracted": 0, "parsed": 0}
             continue
             
        # Ejecutar Normalización
        normalized_offers = []
        for raw in raw_items:
             try:
                 offer = parser_inst.parse(raw)
                 if offer.validate():
                     normalized_offers.append(offer)
             except Exception as e:
                 logger.error(f"Error normalizando oferta desde {source_name}: {e}")
                 
        logger.info(f"Normalización completa para {source_name}. Total válidos listos para guardado: {len(normalized_offers)}")
        
        # Storage
        storage.save(normalized_offers, source_name)
        
        results_summary[source_name] = {
             "extracted": len(raw_items),
             "parsed": len(normalized_offers)
        }

    # Consolidar todo si se corrió más de 1
    storage.consolidate()
    
    total_time = (time.time() - pipeline_start) / 60.0
    logger.info(f"Pipeline finalizado en {total_time:.2f} minutos.")
    logger.info(f"Resumen de operación: {results_summary}")

if __name__ == "__main__":
    main()
