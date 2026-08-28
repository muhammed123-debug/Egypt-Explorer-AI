from pathlib import Path
import time
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# TOURISM INFORMATION ENRICHMENT
# ============================================================

INPUT_FILE = Path("data/enriched_tourism_data.csv")
OUTPUT_FILE = Path("data/tourism_enriched.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}

TIMEOUT = 20


# ============================================================
# REQUEST
# ============================================================

def fetch_page(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    return response.text


# ============================================================
# EXTRACT TEXT
# ============================================================

def extract_text(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Remove unnecessary elements
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "footer",
            "header"
        ]
    ):
        tag.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True
    )

    return text


# ============================================================
# WIKIPEDIA URL
# ============================================================

def build_wikipedia_url(wiki_title):

    if not wiki_title:
        return ""

    title = str(
        wiki_title
    ).strip()

    if not title:
        return ""

    title = title.replace(
        " ",
        "_"
    )

    return (
        "https://en.wikipedia.org/wiki/"
        + title
    )


# ============================================================
# EXTRACT USEFUL SECTIONS
# ============================================================

def extract_sections(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    sections = {}

    current_heading = "Introduction"

    current_text = []

    for element in soup.find_all(
        ["h2", "h3", "p"]
    ):

        if element.name in ["h2", "h3"]:

            # Save previous section
            if current_text:

                sections[
                    current_heading
                ] = " ".join(
                    current_text
                )

            current_heading = (
                element.get_text(
                    " ",
                    strip=True
                )
            )

            current_text = []

        elif element.name == "p":

            text = element.get_text(
                " ",
                strip=True
            )

            if text:

                current_text.append(
                    text
                )

    # Save final section
    if current_text:

        sections[
            current_heading
        ] = " ".join(
            current_text
        )

    return sections


# ============================================================
# FIND BEST SECTION
# ============================================================

def find_section(
    sections,
    keywords
):

    for title, text in sections.items():

        title_lower = title.lower()

        for keyword in keywords:

            if keyword in title_lower:

                return text

    return ""


# ============================================================
# ENRICH ONE LANDMARK
# ============================================================

def enrich_landmark(row):

    landmark_name = str(
        row["landmark_name"]
    ).strip()

    wiki_title = str(
        row.get("wiki_title", "")
    ).strip()

    # --------------------------------------------------------
    # If no Wikipedia title
    # --------------------------------------------------------

    if not wiki_title:

        return {
            "tourism_status": "no_wiki_title",
            "tourism_description": "",
            "tourism_history": "",
            "tourism_attractions": "",
            "tourism_activities": "",
            "tourism_url": ""
        }

    url = build_wikipedia_url(
        wiki_title
    )

    print(
        f"   🌐 {url}"
    )

    try:

        html = fetch_page(
            url
        )

        sections = extract_sections(
            html
        )

        # ----------------------------------------------------
        # Introduction
        # ----------------------------------------------------

        description = sections.get(
            "Introduction",
            ""
        )

        # ----------------------------------------------------
        # History
        # ----------------------------------------------------

        history = find_section(
            sections,
            [
                "history",
                "historical"
            ]
        )

        # ----------------------------------------------------
        # Attractions / Architecture
        # ----------------------------------------------------

        attractions = find_section(
            sections,
            [
                "architecture",
                "features",
                "description",
                "structure"
            ]
        )

        # ----------------------------------------------------
        # Activities
        # ----------------------------------------------------

        activities = find_section(
            sections,
            [
                "activities",
                "tourism",
                "visitors"
            ]
        )

        return {

            "tourism_status":
                "success",

            "tourism_description":
                description,

            "tourism_history":
                history,

            "tourism_attractions":
                attractions,

            "tourism_activities":
                activities,

            "tourism_url":
                url
        }

    except Exception as e:

        print(
            f"   ❌ Error: {e}"
        )

        return {

            "tourism_status":
                "error",

            "tourism_description":
                "",

            "tourism_history":
                "",

            "tourism_attractions":
                "",

            "tourism_activities":
                "",

            "tourism_url":
                url
        }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("🏛️ TOURISM INFORMATION ENRICHMENT")
    print("=" * 70)

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        print(
            "\n❌ Input file not found:"
        )

        print(
            INPUT_FILE.resolve()
        )

        return

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_FILE
    ).fillna("")

    print(
        f"\n📊 Total landmarks: {len(df)}"
    )

    # --------------------------------------------------------
    # Existing output / resume
    # --------------------------------------------------------

    if OUTPUT_FILE.exists():

        print(
            "\n♻️ Existing enrichment file found."
        )

        old_df = pd.read_csv(
            OUTPUT_FILE
        ).fillna("")

        # Merge previously processed values
        enrichment_columns = [
            "tourism_status",
            "tourism_description",
            "tourism_history",
            "tourism_attractions",
            "tourism_activities",
            "tourism_url"
        ]

        for column in enrichment_columns:

            if column in old_df.columns:

                mapping = dict(
                    zip(
                        old_df["landmark_name"],
                        old_df[column]
                    )
                )

                df[column] = (
                    df["landmark_name"]
                    .map(mapping)
                    .fillna("")
                )

    else:

        for column in [
            "tourism_status",
            "tourism_description",
            "tourism_history",
            "tourism_attractions",
            "tourism_activities",
            "tourism_url"
        ]:

            df[column] = ""

    # ========================================================
    # PROCESS
    # ========================================================

    for index, row in df.iterrows():

        name = row[
            "landmark_name"
        ]

        print("\n" + "-" * 70)

        print(
            f"🏛️ [{index + 1}/{len(df)}] "
            f"{name}"
        )

        # ----------------------------------------------------
        # Skip successful records
        # ----------------------------------------------------

        if (
            str(
                row["tourism_status"]
            ).strip()
            == "success"
        ):

            print(
                "   ⏭️ Already enriched."
            )

            continue

        # ----------------------------------------------------
        # Enrich
        # ----------------------------------------------------

        result = enrich_landmark(
            row
        )

        # ----------------------------------------------------
        # Update
        # ----------------------------------------------------

        for key, value in result.items():

            df.loc[
                index,
                key
            ] = value

        # ----------------------------------------------------
        # Save progress
        # ----------------------------------------------------

        df.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            "   💾 Progress saved."
        )

        # ----------------------------------------------------
        # Polite delay
        # ----------------------------------------------------

        time.sleep(
            random.uniform(
                1.0,
                2.0
            )
        )

    # ========================================================
    # FINAL
    # ========================================================

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 70)
    print("🎉 TOURISM ENRICHMENT FINISHED")
    print("=" * 70)

    print(
        f"\n📊 Total landmarks: {len(df)}"
    )

    print("\n📈 Status:")

    print(
        df[
            "tourism_status"
        ]
        .value_counts()
        .to_string()
    )

    print("\n📄 Output:")

    print(
        OUTPUT_FILE.resolve()
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()