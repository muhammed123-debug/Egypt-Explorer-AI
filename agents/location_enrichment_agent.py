# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# 📍 LOCATION ENRICHMENT AGENT
# ============================================================

from pathlib import Path
import sys
import time

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "tourism_enriched.csv"

OUTPUT_FILE = DATA_DIR / "tourism_enriched.csv"


# ============================================================
# IMPORT LOCATION AGENT
# ============================================================

sys.path.insert(
    0,
    str(BASE_DIR)
)

from agents.location_agent import LocationAgent


# ============================================================
# CONFIG
# ============================================================

MIN_CONFIDENCE = 0.60

ONLY_MISSING_LOCATION = True


# ============================================================
# HELPERS
# ============================================================

def is_missing(value):

    if pd.isna(value):
        return True

    value = str(value).strip()

    return value in [
        "",
        "nan",
        "None",
        "null"
    ]


# ============================================================
# LOCATION ENRICHER
# ============================================================

class LocationEnrichmentAgent:

    def __init__(self):

        self.agent = LocationAgent(
            min_confidence=MIN_CONFIDENCE
        )


    # ========================================================
    # PROCESS DATASET
    # ========================================================

    def run(self):

        print("=" * 70)

        print(
            "🇪🇬 EGYPT EXPLORER AI"
        )

        print(
            "📍 LOCATION ENRICHMENT AGENT"
        )

        print("=" * 70)


        # ----------------------------------------------------
        # Load dataset
        # ----------------------------------------------------

        if not INPUT_FILE.exists():

            raise FileNotFoundError(
                f"❌ Dataset not found:\n"
                f"{INPUT_FILE}"
            )


        df = pd.read_csv(
            INPUT_FILE
        )


        print(
            f"\n📊 Total landmarks:"
            f" {len(df)}"
        )


        # ----------------------------------------------------
        # Ensure columns exist
        # ----------------------------------------------------

        location_columns = [

            "latitude",
            "longitude",
            "display_name",
            "city",
            "governorate",
            "country",
            "osm_type",
            "location_status"
        ]


        for column in location_columns:

            if column not in df.columns:

                df[column] = ""


        # ----------------------------------------------------
        # Find landmarks requiring enrichment
        # ----------------------------------------------------

        missing_mask = (

            df["latitude"].apply(
                is_missing
            )

            |

            df["longitude"].apply(
                is_missing
            )

        )


        targets = df[
            missing_mask
        ]


        print(
            f"\n🎯 Landmarks requiring "
            f"location enrichment:"
            f" {len(targets)}"
        )


        if len(targets) == 0:

            print(
                "\n✅ All landmarks already "
                "have coordinates."
            )

            return


        # ====================================================
        # PROCESS
        # ====================================================

        successful = 0

        low_confidence = 0

        not_found = 0


        for index, row in targets.iterrows():

            landmark_name = str(
                row[
                    "landmark_name"
                ]
            ).strip()


            city = (
                ""
                if is_missing(
                    row.get(
                        "city",
                        ""
                    )
                )
                else str(
                    row.get(
                        "city",
                        ""
                    )
                ).strip()
            )


            governorate = (
                ""
                if is_missing(
                    row.get(
                        "governorate",
                        ""
                    )
                )
                else str(
                    row.get(
                        "governorate",
                        ""
                    )
                ).strip()
            )


            print(
                "\n"
                + "-" * 70
            )

            print(
                f"📍 [{index + 1}/"
                f"{len(df)}]"
            )

            print(
                f"🏛️ {landmark_name}"
            )


            # ------------------------------------------------
            # Agent
            # ------------------------------------------------

            result = (
                self.agent.find_location(
                    landmark_name,
                    city,
                    governorate
                )
            )


            # ------------------------------------------------
            # Success
            # ------------------------------------------------

            if result.status == "success":

                df.at[
                    index,
                    "latitude"
                ] = result.latitude

                df.at[
                    index,
                    "longitude"
                ] = result.longitude

                df.at[
                    index,
                    "display_name"
                ] = result.display_name

                df.at[
                    index,
                    "city"
                ] = result.city

                df.at[
                    index,
                    "governorate"
                ] = result.governorate

                df.at[
                    index,
                    "country"
                ] = result.country

                df.at[
                    index,
                    "osm_type"
                ] = result.osm_type

                df.at[
                    index,
                    "location_status"
                ] = (
                    "agent_success"
                )

                successful += 1


            # ------------------------------------------------
            # Low confidence
            # ------------------------------------------------

            elif (
                result.status
                == "low_confidence"
            ):

                df.at[
                    index,
                    "location_status"
                ] = (
                    "agent_low_confidence"
                )

                low_confidence += 1


            # ------------------------------------------------
            # Not found
            # ------------------------------------------------

            else:

                df.at[
                    index,
                    "location_status"
                ] = (
                    "agent_not_found"
                )

                not_found += 1


            # ------------------------------------------------
            # Save after every landmark
            # ------------------------------------------------

            df.to_csv(
                OUTPUT_FILE,
                index=False,
                encoding="utf-8-sig"
            )


            # Respect Nominatim usage
            time.sleep(
                1
            )


        # ====================================================
        # FINAL REPORT
        # ====================================================

        print(
            "\n"
            + "=" * 70
        )

        print(
            "📊 LOCATION AGENT REPORT"
        )

        print(
            "=" * 70
        )

        print(
            f"\n🎯 Processed:"
            f" {len(targets)}"
        )

        print(
            f"✅ Successful:"
            f" {successful}"
        )

        print(
            f"⚠️ Low confidence:"
            f" {low_confidence}"
        )

        print(
            f"❌ Not found:"
            f" {not_found}"
        )

        print(
            f"\n💾 Updated dataset:"
            f"\n{OUTPUT_FILE}"
        )

        print(
            "\n🎉 LOCATION ENRICHMENT COMPLETE"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    enricher = (
        LocationEnrichmentAgent()
    )

    enricher.run()