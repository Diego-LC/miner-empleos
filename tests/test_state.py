import os
import json
import pytest
from extractors.chiletrabajos import ChiletrabajosExtractor

def test_chiletrabajos_state_loading(tmpdir):
    # Setup un state falso en tmpdir
    state_file = os.path.join(tmpdir, "chiletrabajos.cursor.json")
    with open(state_file, "w") as f:
         json.dump({"rss_index": 50, "last_guid": "abc"}, f)
         
    # Mocking config para que apunte ahí
    import config
    original_state_dir = config.STATE_DIR
    config.STATE_DIR = str(tmpdir)
    
    try:
         ext = ChiletrabajosExtractor()
         ext.state_file = state_file
         ext.load_state()
         assert ext.checkpoint_state["rss_index"] == 50
         assert ext.checkpoint_state["last_guid"] == "abc"
         
         # Modificar y guardar
         ext.save_state(100, "def")
         
         with open(state_file, "r") as f:
              data = json.load(f)
              assert data["rss_index"] == 100
              assert data["last_guid"] == "def"
              assert "last_timestamp" in data
    finally:
         config.STATE_DIR = original_state_dir
