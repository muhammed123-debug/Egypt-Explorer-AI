from pathlib import Path
import time
import random
import requests
import pandas as pd

# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# LOCATION ENRICHMENT
# ============================================================

INPUT_FILE = Path("data/tourism_data.csv")
OUTPUT_FILE = Path("data/enriched_tourism_data.csv")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": (
        "EgyptExplorerAI/1.0 "
        "(Educational Tourism RAG Project)"
    )
}

TIMEOUT = 20

# Nominatim requires polite request spacing
MIN_DELAY = 2
MAX_DELAY = 3


# ============================================================
# SEARCH LOCATION
# ============================================================

def search_location(landmark_name):

    params = {
        "q": f"{landmark_name}, Egypt",
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    result = results[0]

    address = result.get("address", {})

    return {
        "latitude": result.get("lat", ""),
        "longitude": result.get("lon", ""),
        "display_name": result.get("display_name", ""),
        "city": (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or ""
        ),
        "governorate": (
            address.get("state")
            or ""
        ),
        "country": (
            address.get("country")
            or ""
        ),
        "osm_type": result.get("type", ""),
        "osm_class": result.get("class", ""),
    }


# ============================================================
# LOAD PREVIOUS RESULTS
# ============================================================

def load_existing():

    if not OUTPUT_FILE.exists():
        return {}

    try:

        df = pd.read_csv(
            OUTPUT_FILE
        ).fillna("")

        results = {}

        for _, row in df.iterrows():

            results[
                row["landmark_name"]
            ] = row.to_dict()

        return results

    except Exception:

        return {}


# ============================================================
# SAVE
# ============================================================

def save_results(results):

    df = pd.DataFrame(
        list(results.values())
    )

    if not df.empty:

        df = df.sort_values(
            "landmark_id"
        )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("📍 LOCATION ENRICHMENT")
    print("=" * 70)

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        print(
            "\n❌ tourism_data.csv not found!"
        )

        return

    # --------------------------------------------------------
    # Load tourism data
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_FILE
    ).fillna("")

    print(
        f"\n📊 Total landmarks: {len(df)}"
    )

    # --------------------------------------------------------
    # Previous progress
    # --------------------------------------------------------

    results = load_existing()

    print(
        f"♻️ Existing location records: "
        f"{len(results)}"
    )

    # --------------------------------------------------------
    # Process landmarks
    # --------------------------------------------------------

    for index, row in df.iterrows():

        landmark_name = row[
            "landmark_name"
        ]

        print("\n" + "-" * 70)

        print(
            f"📍 [{index + 1}/{len(df)}] "
            f"{landmark_name}"
        )

        # ----------------------------------------------------
        # Skip if already enriched successfully
        # ----------------------------------------------------

        if landmark_name in results:

            existing = results[
                landmark_name
            ]

            if (
                str(existing.get("latitude", "")).strip()
                and
                str(existing.get("longitude", "")).strip()
            ):

                print(
                    "   ⏭️ Location already exists."
                )

                continue

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        try:

            print(
                "   🔎 Searching OpenStreetMap..."
            )

            location = search_location(
                landmark_name
            )

            # ------------------------------------------------
            # Found
            # ------------------------------------------------

            if location:

                print(
                    f"   ✅ Found:"
                )

                print(
                    f"   🌐 "
                    f"{location['latitude']}, "
                    f"{location['longitude']}"
                )

                print(
                    f"   🏙️ "
                    f"{location['city']}"
                )

                # Merge original data
                record = row.to_dict()

                record.update(location)

                record["location_status"] = (
                    "success"
                )

                results[
                    landmark_name
                ] = record

            # ------------------------------------------------
            # Not found
            # ------------------------------------------------

            else:

                print(
                    "   ⚠️ Location not found."
                )

                record = row.to_dict()

                record.update({

                    "latitude": "",

                    "longitude": "",

                    "display_name": "",

                    "city": "",

                    "governorate": "",

                    "country": "",

                    "osm_type": "",

                    "osm_class": "",

                    "location_status":
                        "not_found"
                })

                results[
                    landmark_name
                ] = record

        # ----------------------------------------------------
        # Error
        # ----------------------------------------------------

        except Exception as e:

            print(
                f"   ❌ Error: {e}"
            )

            record = row.to_dict()

            record.update({

                "latitude": "",

                "longitude": "",

                "display_name": "",

                "city": "",

                "governorate": "",

                "country": "",

                "osm_type": "",

                "osm_class": "",

                "location_status":
                    f"error: {e}"
            })

            results[
                landmark_name
            ] = record

        # ----------------------------------------------------
        # Save after every landmark
        # ----------------------------------------------------

        save_results(results)

        print(
            "   💾 Progress saved."
        )

        # ----------------------------------------------------
        # Polite delay
        # ----------------------------------------------------

        time.sleep(
            random.uniform(
                MIN_DELAY,
                MAX_DELAY
            )
        )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    save_results(results)

    final_df = pd.DataFrame(
        list(results.values())
    )

    print("\n" + "=" * 70)
    print("🎉 LOCATION ENRICHMENT FINISHED")
    print("=" * 70)

    print(
        f"\n📄 Output:"
    )

    print(
        OUTPUT_FILE.resolve()
    )

    print("\n📊 Location status:")

    print(
        final_df[
            "location_status"
        ]
        .value_counts()
        .to_string()
    )

    print(
        f"\n🏛️ Total records: "
        f"{len(final_df)}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
    