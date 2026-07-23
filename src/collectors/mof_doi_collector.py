from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.config.settings import settings
import pandas as pd
from pathlib import Path
import re
import time
import random


# ==========================
# CONFIG
# ==========================

TRACKING_FILE = settings.tracking_dir / "ccdc_tracking.csv"

RUNS = 2000


# ==========================
# LOAD CSV
# ==========================

df = pd.read_csv(
    TRACKING_FILE,
    dtype=str
)

df["publication_doi"] = df["publication_doi"].fillna("")
df["status"] = df["status"].fillna("pending")


# ==========================
# START BROWSER ONCE
# ==========================

options = Options()

driver = webdriver.Chrome(options=options)


try:

    for run in range(RUNS):

        pending = df[df["status"] == "pending"]


        if len(pending) == 0:
            print("No pending CCDC IDs left")
            break


        CCDC_ID = pending.iloc[0]["ccdc_id"]

        print(
            f"\n[{run+1}/{RUNS}] Processing {CCDC_ID}"
        )


        try:

            url = (
                "https://www.ccdc.cam.ac.uk/structures/"
                f"Search?Ccdcid={CCDC_ID}&DatabaseToSearch=Published"
            )


            driver.get(url)


            # wait for page
            time.sleep(random.uniform(3, 8))


            text = driver.find_element(
                By.TAG_NAME,
                "body"
            ).text


            # CAPTCHA detection
            if "captcha" in text.lower():
                raise Exception(
                    "CAPTCHA detected"
                )


            if "Associated publications" in text:

                publication_text = text.split(
                    "Associated publications",
                    1
                )[1]

            else:

                publication_text = ""


            dois = list(set(
                re.findall(
                    r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+',
                    publication_text
                )
            ))


            if dois:

                df.loc[
                    df["ccdc_id"] == CCDC_ID,
                    "publication_doi"
                ] = ";".join(dois)


                df.loc[
                    df["ccdc_id"] == CCDC_ID,
                    "status"
                ] = "done"


                print(
                    "DOI:",
                    dois
                )


            else:

                df.loc[
                    df["ccdc_id"] == CCDC_ID,
                    "publication_doi"
                ] = ""


                df.loc[
                    df["ccdc_id"] == CCDC_ID,
                    "status"
                ] = "not_found"


                print(
                    "No DOI"
                )


        except Exception as e:

            print(
                "Failed:",
                CCDC_ID,
                e
            )


            df.loc[
                df["ccdc_id"] == CCDC_ID,
                "status"
            ] = "failed"


        # save every structure
        df.to_csv(
            TRACKING_FILE,
            index=False
        )


        # delay before next request
        time.sleep(
            random.uniform(4, 10)
        )


finally:

    driver.quit()


print("Finished batch")