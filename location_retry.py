from pathlib import Path
import time
import random
import requests
import pandas as pd

# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# SMART LOCATION RETRY
# ============================================================

INPUT_FILE = Path("data/enriched_tourism_data.csv")
OUTPUT_FILE = Path("data/enriched_tourism_data.csv")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": (
        "EgyptExplorerAI/1.0 "
        "(Educational Tourism RAG Project)"
    )
}

TIMEOUT = 20

MIN_DELAY = 2
MAX_DELAY = 3


# ============================================================
# SEARCH
# ============================================================

def search_location(query):

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 3,
        "addressdetails": 1
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# GENERATE SEARCH QUERIES
# ============================================================

def generate_queries(row):

    name = str(
        row["landmark_name"]
    ).strip()

    wiki_title = str(
        row.get("wiki_title", "")
    ).strip()

    queries = []

    # Original
    queries.append(
        f"{name}, Egypt"
    )

    # Wikipedia title
    if wiki_title and wiki_title.lower() != "nan":

        queries.append(
            f"{wiki_title}, Egypt"
        )

    # Remove common words that can confuse search
    simplified = name

    replacements = [
        "Temple of ",
        "Mosque of ",
        "Church of ",
        "Monastery of ",
        "Pyramid of ",
        "Tomb of ",
        "Museum of ",
        "Palace of ",
    ]

    for prefix in replacements:

        if simplified.lower().startswith(
            prefix.lower()
        ):

            simplified = simplified[
                len(prefix):
            ]

            queries.append(
                f"{simplified}, Egypt"
            )

    # Specific location hints
    location_hints = [
        "Cairo, Egypt",
        "Giza, Egypt",
        "Alexandria, Egypt",
        "Luxor, Egypt",
        "Aswan, Egypt",
        "Sinai, Egypt",
        "Fayoum, Egypt",
        "Siwa, Egypt",
        "Dahshur, Egypt",
        "Saqqara, Egypt",
        "Abydos, Egypt",
    ]

    for hint in location_hints:

        queries.append(
            f"{name}, {hint.split(',')[0]}"
        )

    # Remove duplicates
    unique = []

    for q in queries:

        if q not in unique:

            unique.append(q)

    return unique


# ============================================================
# CHOOSE BEST RESULT
# ============================================================

def choose_result(results, landmark_name):

    if not results:
        return None

    name = landmark_name.lower()

    # First try exact-ish name matching
    for result in results:

        display = result.get(
            "display_name",
            ""
        ).lower()

        if name in display:

            return result

    # Otherwise use first result
    return results[0]


# ============================================================
# EXTRACT LOCATION
# ============================================================

def extract_location(result):

    address = result.get(
        "address",
        {}
    )

    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
        or ""
    )

    governorate = (
        address.get("state")
        or ""
    )

    country = (
        address.get("country")
        or ""
    )

    return {

        "latitude":
            result.get("lat", ""),

        "longitude":
            result.get("lon", ""),

        "display_name":
            result.get(
                "display_name",
                ""
            ),

        "city":
            city,

        "governorate":
            governorate,

        "country":
            country,

        "osm_type":
            result.get(
                "type",
                ""
            ),

        "osm_class":
            result.get(
                "class",
                ""
            )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("🔄 SMART LOCATION RETRY")
    print("=" * 70)

    if not INPUT_FILE.exists():

        print(
            "\n❌ enriched_tourism_data.csv not found!"
        )

        return

    df = pd.read_csv(
        INPUT_FILE
    ).fillna("")

    print(
        f"\n📊 Total landmarks: {len(df)}"
    )

    # Only retry locations that failed
    failed_mask = (
        df["location_status"]
        != "success"
    )

    failed_indexes = df[
        failed_mask
    ].index.tolist()

    print(
        f"⚠️ Locations to retry: "
        f"{len(failed_indexes)}"
    )

    successful = 0

    # ========================================================
    # PROCESS FAILED LOCATIONS
    # ========================================================

    for counter, index in enumerate(
        failed_indexes,
        start=1
    ):

        row = df.loc[index]

        landmark_name = row[
            "landmark_name"
        ]

        print("\n" + "-" * 70)

        print(
            f"🔄 [{counter}/{len(failed_indexes)}] "
            f"{landmark_name}"
        )

        queries = generate_queries(
            row
        )

        found = None

        for query_number, query in enumerate(
            queries,
            start=1
        ):

            print(
                f"   🔎 Query {query_number}: "
                f"{query}"
            )

            try:

                results = search_location(
                    query
                )

                candidate = choose_result(
                    results,
                    landmark_name
                )

                if candidate:

                    found = candidate

                    print(
                        "   ✅ Candidate found:"
                    )

                    print(
                        "   📍 "
                        + candidate.get(
                            "display_name",
                            ""
                        )
                    )

                    break

            except Exception as e:

                print(
                    f"   ⚠️ Query failed: {e}"
                )

            time.sleep(
                random.uniform(
                    1.5,
                    2.5
                )
            )

        # ====================================================
        # UPDATE
        # ====================================================

        if found:

            location = extract_location(
                found
            )

            for key, value in location.items():

                df.loc[index, key] = value

            df.loc[
                index,
                "location_status"
            ] = "retry_success"

            successful += 1

            print(
                "   💾 Location updated."
            )

        else:

            df.loc[
                index,
                "location_status"
            ] = "not_found"

            print(
                "   ❌ Still not found."
            )

        # Save after every landmark
        df.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            "   💾 Progress saved."
        )

        time.sleep(
            random.uniform(
                MIN_DELAY,
                MAX_DELAY
            )
        )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 70)
    print("🎉 LOCATION RETRY FINISHED")
    print("=" * 70)

    print(
        f"\n✅ Newly resolved: {successful}"
    )

    print(
        f"📊 Total landmarks: {len(df)}"
    )

    print("\n📍 Location status:")

    print(
        df["location_status"]
        .value_counts()
        .to_string()
    )

    print("\n📄 Output:")

    print(
        OUTPUT_FILE.resolve()
    )


if __name__ == "__main__":
    main()