import json
import os
import logging
from datetime import datetime, timezone
from typing import List
from schema import JobOffer
from config import DATA_DIR

logger = logging.getLogger(__name__)

class JSONStorage:
    def __init__(self):
        self._ensure_dirs()
        self.version = "1.0"

    def _ensure_dirs(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, "consolidated"), exist_ok=True)
        # Rutas de las fuentes se crearán on-demand o en config

    def save(self, offers: List[JobOffer], source: str) -> None:
        """Guarda ofertas deduplicadas por fuente."""
        if not offers:
            logger.info(f"0 ofertas recibidas de {source}, nada que guardar.")
            return

        os.makedirs(os.path.join(DATA_DIR, source), exist_ok=True)
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filepath = os.path.join(DATA_DIR, source, f"{today_str}.json")

        existing_offers = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("ofertas", []):
                        if "id" in item:
                            existing_offers[item["id"]] = item
            except Exception as e:
                logger.error(f"Error leyendo archivo JSON actual ({filepath}): {e}")

        new_count = 0
        updated_count = 0

        for offer in offers:
            # offer viene tipado como JobOffer
            if not offer.validate():
                continue
            dict_out = offer.to_dict()
            if dict_out["id"] in existing_offers:
                updated_count += 1
            else:
                new_count += 1
            existing_offers[dict_out["id"]] = dict_out

        total = len(existing_offers)

        # Reconstruir listado
        final_list = list(existing_offers.values())
        
        output_data = {
            "_meta": {
                "fecha_extraccion": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fuente": source,
                "total_ofertas": total,
                "version_schema": self.version
            },
            "ofertas": final_list
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Guardado exitoso para {source}: {new_count} nuevas, {updated_count} actualizadas. Total actual: {total}")

    def consolidate(self) -> None:
        """Merge de todas las fuentes del día."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        consolidated_path = os.path.join(DATA_DIR, "consolidated", f"{today_str}.json")

        consolidated_offers = {}
        for source in ["getonboard", "chiletrabajos", "bne"]:
            filepath = os.path.join(DATA_DIR, source, f"{today_str}.json")
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data.get("ofertas", []):
                            consolidated_offers[item["id"]] = item
                except Exception as e:
                     logger.error(f"Error al consolidar origen {source}: {e}")

        total = len(consolidated_offers)
        if total == 0:
            logger.info("No hay datos para consolidar hoy.")
            return

        final_list = list(consolidated_offers.values())
        output_data = {
            "_meta": {
                "fecha_extraccion": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fuente": "consolidated",
                "total_ofertas": total,
                "version_schema": self.version
            },
            "ofertas": final_list
        }

        with open(consolidated_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Consolidación exitosa. Total final: {total} ofertas.")
