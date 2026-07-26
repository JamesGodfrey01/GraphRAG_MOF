from pathlib import Path
import gemmi
from src.config.settings import settings

cif_file = Path(settings.cif_dir) / "ABACUF_stripped.cif"

doc = gemmi.cif.read_file(str(cif_file))

block = doc.sole_block()

print(block.find_value("_cell_length_a"))
