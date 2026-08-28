import re
from pathlib import Path

import pandas as pd


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# KNOWLEDGE BASE BUILDER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

INPUT_FILE = (
    DATA_DIR / "tourism_enriched.csv"
)

OUTPUT_FILE = (
    DATA_DIR / "knowledge_base.csv"
)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_value(value):

    if pd.isna(value):

        return ""

    value = str(value).strip()

    if value.lower() in [
        "nan",
        "none",
        "null",
        "n/a",
        "na"
    ]:

        return ""

    return value


def normalize_text(text):

    text = clean_value(text)

    if not text:

        return ""

    # Remove excessive whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# BUILD LOCATION TEXT
# ============================================================

def build_location(row):

    parts = []

    city = normalize_text(
        row.get("city", "")
    )

    governorate = normalize_text(
        row.get("governorate", "")
    )

    country = normalize_text(
        row.get("country", "")
    )

    display_name = normalize_text(
        row.get("display_name", "")
    )

    latitude = clean_value(
        row.get("latitude", "")
    )

    longitude = clean_value(
        row.get("longitude", "")
    )

    if display_name:

        parts.append(
            f"Address: {display_name}"
        )

    elif city or governorate:

        location_parts = [
            x for x in [
                city,
                governorate,
                country
            ]
            if x
        ]

        parts.append(
            "Location: "
            + ", ".join(
                location_parts
            )
        )

    if latitude and longitude:

        parts.append(
            f"Coordinates: "
            f"{latitude}, {longitude}"
        )

    return "\n".join(parts)


# ============================================================
# BUILD DOCUMENT
# ============================================================

def build_document(row):

    landmark_name = normalize_text(
        row.get(
            "landmark_name",
            ""
        )
    )

    clean_text = normalize_text(
        row.get(
            "clean_text",
            ""
        )
    )

    original_document = normalize_text(
        row.get(
            "document",
            ""
        )
    )

    tourism_history = normalize_text(
        row.get(
            "tourism_history",
            ""
        )
    )

    tourism_attractions = normalize_text(
        row.get(
            "tourism_attractions",
            ""
        )
    )

    tourism_activities = normalize_text(
        row.get(
            "tourism_activities",
            ""
        )
    )

    location_text = build_location(
        row
    )

    source_url = normalize_text(
        row.get(
            "source_url",
            ""
        )
    )

    tourism_url = normalize_text(
        row.get(
            "tourism_url",
            ""
        )
    )


    # ========================================================
    # CHOOSE MAIN INFORMATION
    # ========================================================

    main_text = (
        clean_text
        if clean_text
        else original_document
    )


    sections = []

    # --------------------------------------------------------
    # Landmark
    # --------------------------------------------------------

    if landmark_name:

        sections.append(
            f"Landmark: {landmark_name}"
        )


    # --------------------------------------------------------
    # Main information
    # --------------------------------------------------------

    if main_text:

        sections.append(
            "General Information:\n"
            + main_text
        )


    # --------------------------------------------------------
    # History
    # --------------------------------------------------------

    if tourism_history:

        sections.append(
            "History:\n"
            + tourism_history
        )


    # --------------------------------------------------------
    # Attractions
    # --------------------------------------------------------

    if tourism_attractions:

        sections.append(
            "Attractions:\n"
            + tourism_attractions
        )


    # --------------------------------------------------------
    # Activities
    # --------------------------------------------------------

    if tourism_activities:

        sections.append(
            "Activities:\n"
            + tourism_activities
        )


    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    if location_text:

        sections.append(
            "Location:\n"
            + location_text
        )


    # --------------------------------------------------------
    # Sources
    # --------------------------------------------------------

    if source_url:

        sections.append(
            f"Source: {source_url}"
        )

    if tourism_url:

        sections.append(
            f"Tourism Source: {tourism_url}"
        )


    return "\n\n".join(
        sections
    )


# ============================================================
# BUILD KNOWLEDGE BASE
# ============================================================

def build_knowledge_base():

    print("=" * 70)

    print(
        "🇪🇬 EGYPT EXPLORER AI"
    )

    print(
        "📚 KNOWLEDGE BASE BUILDER"
    )

    print("=" * 70)


    # ========================================================
    # CHECK INPUT
    # ========================================================

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"❌ Input file not found:\n"
            f"{INPUT_FILE}"
        )


    print(
        f"\n📥 Input:"
    )

    print(
        INPUT_FILE
    )


    # ========================================================
    # LOAD
    # ========================================================

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"\n📊 Input records: "
        f"{len(df)}"
    )


    # ========================================================
    # BUILD DOCUMENTS
    # ========================================================

    print(
        "\n🧠 Building RAG documents..."
    )


    df["rag_document"] = df.apply(
        build_document,
        axis=1
    )


    # ========================================================
    # DOCUMENT QUALITY
    # ========================================================

    df["rag_document"] = (
        df["rag_document"]
        .fillna("")
        .astype(str)
        .str.strip()
    )


    df["rag_text_length"] = (
        df["rag_document"]
        .str.len()
    )


    # ========================================================
    # STATUS
    # ========================================================

    df["rag_ready"] = (
        df["rag_text_length"] > 0
    )


    # ========================================================
    # SELECT COLUMNS
    # ========================================================

    columns = [
        "landmark_id",
        "landmark_name",
        "folder_name",
        "image_count",

        "latitude",
        "longitude",
        "display_name",
        "city",
        "governorate",
        "country",

        "source_url",
        "tourism_url",

        "rag_document",
        "rag_text_length",
        "rag_ready"
    ]


    available_columns = [
        column
        for column in columns
        if column in df.columns
    ]


    output_df = df[
        available_columns
    ].copy()


    # ========================================================
    # SAVE
    # ========================================================

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # ========================================================
    # REPORT
    # ========================================================

    total = len(
        output_df
    )

    ready = int(
        output_df[
            "rag_ready"
        ].sum()
    )

    missing = (
        total - ready
    )


    print(
        "\n" + "=" * 70
    )

    print(
        "📚 KNOWLEDGE BASE REPORT"
    )

    print(
        "=" * 70
    )

    print(
        f"\n🏛️ Total landmarks:"
        f" {total}"
    )

    print(
        f"✅ RAG ready:"
        f" {ready}"
    )

    print(
        f"⚠️ Empty documents:"
        f" {missing}"
    )

    print(
        f"\n📏 Average document length:"
        f" {output_df['rag_text_length'].mean():,.0f}"
    )

    print(
        f"📏 Maximum document length:"
        f" {output_df['rag_text_length'].max():,}"
    )

    print(
        f"\n💾 Saved to:"
        f"\n{OUTPUT_FILE}"
    )


    # ========================================================
    # SAMPLE
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "📝 SAMPLE RAG DOCUMENT"
    )

    print(
        "=" * 70
    )

    sample = output_df[
        output_df["rag_ready"]
    ].head(1)


    if len(sample) > 0:

        print(
            "\n"
            + sample.iloc[0][
                "rag_document"
            ][:5000]
        )


    print(
        "\n" + "=" * 70
    )

    print(
        "🎉 KNOWLEDGE BASE CREATED"
    )

    print(
        "=" * 70
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    build_knowledge_base()