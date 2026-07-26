from pathlib import Path
import shutil
import pandas as pd

from src.config.settings import settings


# =====================================================
# PATHS
# =====================================================

TRACKING_CSV = settings.ccdc_tracking_csv

RAW_CIF_DIR = settings.raw_cif_dir
RAW_PAPER_DIR = settings.raw_paper_dir

READY_CIF_DIR = settings.ready_cif_dir
READY_PAPER_DIR = settings.ready_paper_dir

NO_PAPER_CIF_DIR = settings.no_paper_cif_dir


# =====================================================
# CREATE DIRECTORIES
# =====================================================

for directory in [
    READY_CIF_DIR,
    READY_PAPER_DIR,
    NO_PAPER_CIF_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True
    )


# =====================================================
# LOAD TRACKING CSV
# =====================================================

print("=" * 60)
print("Loading tracking file:")
print(TRACKING_CSV)
print("=" * 60)


df = pd.read_csv(TRACKING_CSV)


print("\nColumns:")
print(df.columns.tolist())

print("\nDetected statuses:")
print(df["status"].value_counts())

print("=" * 60)


# =====================================================
# COUNTERS
# =====================================================

ready_cifs = 0
ready_pdfs = 0
no_paper_cifs = 0

missing_cifs = []
missing_pdfs = []

unknown_status = []


# =====================================================
# PROCESS EACH ENTRY
# =====================================================

for _, row in df.iterrows():

    refcode = str(row["ccdc_id"]).strip()

    status = (
        str(row["status"])
        .strip()
        .lower()
        .replace(" ", "_")
    )


    # CIF naming convention
    cif_file = RAW_CIF_DIR / f"{refcode}_stripped.cif"


    # =================================================
    # PAPER AVAILABLE
    # =================================================

    if status in [
        "downloaded",
        "done"
    ]:


        # -------------------------
        # Move CIF
        # -------------------------

        if cif_file.exists():

            destination = READY_CIF_DIR / cif_file.name


            if not destination.exists():

                shutil.move(
                    str(cif_file),
                    str(destination)
                )

                ready_cifs += 1


        else:

            missing_cifs.append(refcode)



        # -------------------------
        # Move PDF
        # -------------------------

        pdf_path = row.get("file_path")


        if isinstance(pdf_path, str) and pdf_path.strip():

            # only use filename
            pdf_name = Path(pdf_path).name

            pdf_file = RAW_PAPER_DIR / pdf_name


            if pdf_file.exists():

                destination = READY_PAPER_DIR / pdf_file.name


                if not destination.exists():

                    shutil.move(
                        str(pdf_file),
                        str(destination)
                    )

                    ready_pdfs += 1


            else:

                missing_pdfs.append(pdf_name)



    # =================================================
    # NO PAPER AVAILABLE
    # =================================================

    elif status in [
        "not_found",
        "failed"
    ]:


        if cif_file.exists():

            destination = NO_PAPER_CIF_DIR / cif_file.name


            if not destination.exists():

                shutil.move(
                    str(cif_file),
                    str(destination)
                )

                no_paper_cifs += 1


        else:

            missing_cifs.append(refcode)



    # =================================================
    # WAITING / NOT QUERIED
    # =================================================

    elif status in [
        "pending",
        "requires_request"
    ]:

        # Leave untouched
        continue



    # =================================================
    # UNKNOWN
    # =================================================

    else:

        unknown_status.append(
            {
                "ccdc_id": refcode,
                "status": status
            }
        )



# =====================================================
# SUMMARY
# =====================================================

print("\n")
print("=" * 60)
print("COMPLETE")
print("=" * 60)

print(f"Ready CIFs moved     : {ready_cifs}")
print(f"Ready PDFs moved     : {ready_pdfs}")
print(f"No-paper CIFs moved  : {no_paper_cifs}")

print()

print(f"Missing CIFs         : {len(missing_cifs)}")
print(f"Missing PDFs         : {len(missing_pdfs)}")
print(f"Unknown statuses     : {len(unknown_status)}")


if missing_cifs:

    print("\nMissing CIF examples:")
    print(
        missing_cifs[:20]
    )


if missing_pdfs:

    print("\nMissing PDF examples:")
    print(
        missing_pdfs[:20]
    )


if unknown_status:

    print("\nUnknown status examples:")
    for item in unknown_status[:20]:
        print(item)


print("=" * 60)