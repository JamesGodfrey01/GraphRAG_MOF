from pathlib import Path
import shutil
import pandas as pd

from src.config.settings import settings

# Paths & Directories
READY_CIF_DIR = Path(settings.ready_cif_dir)
NO_PAPER_CIF_DIR = Path(settings.no_paper_cif_dir)
RAW_CIF_DIR = Path(settings.raw_cif_dir)

READY_CIF_DIR.mkdir(parents=True, exist_ok=True)
NO_PAPER_CIF_DIR.mkdir(parents=True, exist_ok=True)

# Load CSV and keep only required columns
df = pd.read_csv(settings.paper_tracking_csv)[["ccdc_id", "status"]]

# Clean values
df["status"] = df["status"].astype(str).str.strip().str.lower()
df["ccdc_id"] = (
    df["ccdc_id"]
    .astype(str)
    .str.strip()
    .str.upper()    
    .str.replace(r"^PENDING", "", regex=True)
)

# Process rows
for _, row in df.iterrows():
    cif_file = RAW_CIF_DIR / f"{row['ccdc_id']}_stripped.cif"

    if row["status"] == "downloaded":
        target = READY_CIF_DIR / cif_file.name
    elif row["status"] == "not_found":
        target = NO_PAPER_CIF_DIR / cif_file.name
    else:
        continue

    # Move file if it exists and hasn't already been moved
    if cif_file.exists() and not target.exists():
        shutil.move(cif_file, target)

print("Finished processing CIFs!")