import asyncio
import random
from pathlib import Path
import os
from dotenv import load_dotenv
import pandas as pd
from telethon import TelegramClient, errors, events
from src.config.settings import settings


# =====================================================
# CONFIG
# =====================================================
load_dotenv()

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")

target_bot = os.getenv("TELEGRAM_TARGET_BOT")



download_folder = settings.raw_paper_dir
download_folder.mkdir(parents=True, exist_ok=True)

TRACKING_FILE = settings.tracking_dir / "paper_tracking.csv"


# =====================================================
# TELEGRAM CLIENT
# =====================================================

client = TelegramClient(
    "paper_session",
    api_id,
    api_hash
)


# =====================================================
# GLOBAL DOWNLOAD STATE
# =====================================================

current_download = {
    "doi": None,
    "future": None,
    "download_clicked": False
}


# =====================================================
# GLOBAL TELEGRAM HANDLER
# =====================================================

@client.on(events.NewMessage(from_users=target_bot))
async def telegram_handler(event):

    if not isinstance(event, events.NewMessage.Event):
        return


    print("\n--- BOT MESSAGE ---")

    if event.text:
        print(event.text)


    # No active DOI request
    if current_download["future"] is None:
        return



    # -------------------------------------------------
    # Handle buttons
    # -------------------------------------------------

    if event.buttons:

        for row in event.buttons:

            for button in row:

                print(
                    "Button:",
                    button.text,
                    "| Callback:",
                    button.data
                )


                # ---------------------------------
                # Download available
                # ---------------------------------

                if (
                    button.data
                    and button.data.startswith(b"/d_")
                    and not current_download["download_clicked"]
                ):

                    current_download["download_clicked"] = True

                    print(
                        "Clicking DOWNLOAD button..."
                    )

                    await asyncio.sleep(
                        random.uniform(1, 3)
                    )


                    try:

                        await event.click(
                            text=button.text
                        )

                    except Exception as e:

                        print(
                            "Download click failed:",
                            e
                        )

                    return



                # ---------------------------------
                # Requires request -> SKIP
                # ---------------------------------

                if (
                    button.data
                    and button.data.startswith(b"/req_")
                ):

                    print(
                        "Paper requires request. Skipping..."
                    )


                    if not current_download["future"].done():

                        current_download["future"].set_result(
                            "SKIP_REQUEST"
                        )

                    return



    # -------------------------------------------------
    # PDF received
    # -------------------------------------------------

    if event.document:

        filename = event.file.name or ""

        print(
            "Document received:",
            filename
        )


        if (
            event.document.mime_type == "application/pdf"
            or filename.lower().endswith(".pdf")
        ):

            print(
                "Downloading PDF..."
            )


            pdf_path = await event.download_media(
                file=str(download_folder)
            )


            print(
                "Saved:",
                pdf_path
            )


            if not current_download["future"].done():

                current_download["future"].set_result(
                    pdf_path
                )



# =====================================================
# REQUEST ONE PDF
# =====================================================

async def get_pdf(doi):

    future = asyncio.Future()


    current_download["doi"] = doi
    current_download["future"] = future
    current_download["download_clicked"] = False



    print(
        f"Sending DOI: {doi}"
    )


    await client.send_message(
        target_bot,
        f"https://doi.org/{doi}"
    )


    try:

        result = await asyncio.wait_for(
            future,
            timeout=120
        )


        return result



    except asyncio.TimeoutError:

        print(
            "Timed out waiting for response"
        )

        return None



    finally:

        current_download["doi"] = None
        current_download["future"] = None
        current_download["download_clicked"] = False




# =====================================================
# MAIN
# =====================================================

async def main():

    if not TRACKING_FILE.exists():

        print(
            "Tracking CSV missing"
        )

        return



    df = pd.read_csv(
        TRACKING_FILE,
        index_col="ccdc_id"
    )


    if "file_path" not in df.columns:

        df["file_path"] = None



    pending = df[
        df["status"] == "done"
    ]



    if pending.empty:

        print(
            "No papers to process"
        )

        return



    await client.start()

    print(
        "Telegram client logged in."
    )



    downloaded = set(
        df.loc[
            df["status"] == "downloaded",
            "publication_doi"
        ]
        .dropna()
        .astype(str)
        .str.strip()
    )



    for ccdc_id, row in pending.iterrows():


        doi = str(
            row["publication_doi"]
        ).strip()



        if (
            not doi
            or doi.lower() == "nan"
        ):

            continue



        if doi in downloaded:

            print(
                f"Skipping {doi} (already downloaded)"
            )

            continue



        print("\n" + "=" * 60)
        print(
            f"Processing {ccdc_id}"
        )
        print(
            doi
        )
        print("=" * 60)



        try:


            result = await get_pdf(
                doi
            )



            mask = (
                df["publication_doi"]
                .astype(str)
                .str.strip()
                == doi
            )



            # -----------------------------
            # Paper requires request
            # -----------------------------

            if result == "SKIP_REQUEST":

                print(
                    "Marked as requires_request"
                )


                df.loc[
                    mask,
                    "status"
                ] = "requires_request"



            # -----------------------------
            # Successful download
            # -----------------------------

            elif result:


                df.loc[
                    mask,
                    "file_path"
                ] = str(result)


                df.loc[
                    mask,
                    "status"
                ] = "downloaded"


                downloaded.add(
                    doi
                )


                print(
                    "Download complete"
                )



            else:

                print(
                    "Failed / timeout"
                )



            # Save after every DOI

            df.to_csv(
                TRACKING_FILE
            )



            delay = random.uniform(
                5,
                10
            )


            print(
                f"Sleeping {delay:.1f}s"
            )


            await asyncio.sleep(
                delay
            )



        except errors.FloodWaitError as e:

            print(
                f"Telegram FloodWait: {e.seconds}s"
            )

            await asyncio.sleep(
                e.seconds
            )



        except Exception as e:

            print(
                "Unexpected error:",
                e
            )



    print(
        "Batch finished"
    )


    await client.disconnect()



# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    asyncio.run(main())