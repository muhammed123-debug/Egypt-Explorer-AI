from pathlib import Path
import json
import pandas as pd


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# KNOWLEDGE BASE BUILDER
# ============================================================

DATA_DIR = Path("data")

TOURISM_FILE = DATA_DIR / "tourism_enriched.csv"
LOCATION_FILE = DATA_DIR / "enriched_tourism_data.csv"
VIDEO_FILE = DATA_DIR / "videos.csv"

OUTPUT_FILE = DATA_DIR / "knowledge_base.csv"


# ============================================================
# HELPERS
# ============================================================

def safe_text(value):
    """
    Convert a value into clean text.
    """

    if pd.isna(value):
        return ""

    return str(value).strip()


def safe_json(value):
    """
    Make sure JSON fields are valid.
    """

    if pd.isna(value):
        return "[]"

    value = str(value).strip()

    if not value:
        return "[]"

    try:
        json.loads(value)
        return value

    except Exception:
        return "[]"


def first_existing_column(df, columns):
    """
    Return the first column that exists.
    """

    for column in columns:

        if column in df.columns:
            return column

    return None


# ============================================================
# LOAD FILE
# ============================================================

def load_csv(path):

    if not path.exists():

        print(
            f"⚠️ File not found: {path}"
        )

        return pd.DataFrame()

    print(
        f"📂 Loading: {path}"
    )

    return pd.read_csv(
        path
    ).fillna("")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("🧠 KNOWLEDGE BASE BUILDER")
    print("=" * 75)

    # ========================================================
    # LOAD DATASETS
    # ========================================================

    tourism_df = load_csv(
        TOURISM_FILE
    )

    location_df = load_csv(
        LOCATION_FILE
    )

    video_df = load_csv(
        VIDEO_FILE
    )

    # --------------------------------------------------------
    # Main dataset check
    # --------------------------------------------------------

    if tourism_df.empty:

        print(
            "\n❌ tourism_enriched.csv is required."
        )

        return

    print(
        f"\n🏛️ Tourism records: "
        f"{len(tourism_df)}"
    )

    print(
        f"📍 Location records: "
        f"{len(location_df)}"
    )

    print(
        f"🎥 Video records: "
        f"{len(video_df)}"
    )

    # ========================================================
    # BASE DATASET
    # ========================================================

    kb = tourism_df.copy()

    # ========================================================
    # LOCATION DATA
    # ========================================================

    if not location_df.empty:

        location_columns = [
            "landmark_name",
            "latitude",
            "longitude",
            "display_name",
            "city",
            "governorate",
            "country",
            "osm_type",
            "osm_class",
            "location_status"
        ]

        available = [
            column
            for column in location_columns
            if column in location_df.columns
        ]

        location_data = location_df[
            available
        ].copy()

        # Avoid duplicate columns
        location_data = (
            location_data
            .drop_duplicates(
                subset=["landmark_name"]
            )
        )

        kb = kb.merge(
            location_data,
            on="landmark_name",
            how="left",
            suffixes=("", "_location")
        )

    # ========================================================
    # VIDEO DATA
    # ========================================================

    if not video_df.empty:

        video_columns = [
            "landmark_name",
            "youtube_videos",
            "youtube_count",
            "tiktok_search_url",
            "tiktok_status"
        ]

        available = [
            column
            for column in video_columns
            if column in video_df.columns
        ]

        video_data = video_df[
            available
        ].copy()

        video_data = (
            video_data
            .drop_duplicates(
                subset=["landmark_name"]
            )
        )

        kb = kb.merge(
            video_data,
            on="landmark_name",
            how="left",
            suffixes=("", "_video")
        )

    # ========================================================
    # CLEAN DUPLICATE COLUMNS
    # ========================================================

    # If location information existed in tourism data,
    # prefer the enriched location value.

    for field in [
        "latitude",
        "longitude",
        "city",
        "governorate",
        "country"
    ]:

        location_field = f"{field}_location"

        if location_field in kb.columns:

            if field not in kb.columns:

                kb[field] = kb[
                    location_field
                ]

            else:

                kb[field] = (
                    kb[field]
                    .replace("", pd.NA)
                    .fillna(
                        kb[location_field]
                    )
                    .fillna("")
                )

            kb.drop(
                columns=[
                    location_field
                ],
                inplace=True
            )

    # ========================================================
    # CLEAN TEXT FIELDS
    # ========================================================

    text_columns = [
        "landmark_name",
        "city",
        "governorate",
        "country",
        "tourism_description",
        "tourism_history",
        "tourism_attractions",
        "tourism_activities",
        "clean_text",
        "source_url",
        "tourism_url"
    ]

    for column in text_columns:

        if column in kb.columns:

            kb[column] = (
                kb[column]
                .apply(safe_text)
            )

    # ========================================================
    # CLEAN VIDEO FIELDS
    # ========================================================

    if "youtube_videos" in kb.columns:

        kb["youtube_videos"] = (
            kb["youtube_videos"]
            .apply(safe_json)
        )

    else:

        kb["youtube_videos"] = "[]"

    if "youtube_count" not in kb.columns:

        kb["youtube_count"] = 0

    if "tiktok_search_url" not in kb.columns:

        kb["tiktok_search_url"] = ""

    if "tiktok_status" not in kb.columns:

        kb["tiktok_status"] = ""

    # ========================================================
    # CREATE RAG DOCUMENT
    # ========================================================

    def build_document(row):

        parts = []

        name = safe_text(
            row.get(
                "landmark_name",
                ""
            )
        )

        city = safe_text(
            row.get(
                "city",
                ""
            )
        )

        governorate = safe_text(
            row.get(
                "governorate",
                ""
            )
        )

        country = safe_text(
            row.get(
                "country",
                ""
            )
        )

        description = safe_text(
            row.get(
                "tourism_description",
                ""
            )
        )

        history = safe_text(
            row.get(
                "tourism_history",
                ""
            )
        )

        attractions = safe_text(
            row.get(
                "tourism_attractions",
                ""
            )
        )

        activities = safe_text(
            row.get(
                "tourism_activities",
                ""
            )
        )

        # ----------------------------------------------------
        # Name
        # ----------------------------------------------------

        if name:

            parts.append(
                f"Tourist Landmark: {name}"
            )

        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        location_parts = []

        if city:
            location_parts.append(city)

        if governorate:
            location_parts.append(
                governorate
            )

        if country:
            location_parts.append(country)

        if location_parts:

            parts.append(
                "Location: "
                + ", ".join(
                    location_parts
                )
            )

        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        if description:

            parts.append(
                "Description: "
                + description
            )

        # ----------------------------------------------------
        # History
        # ----------------------------------------------------

        if history:

            parts.append(
                "History: "
                + history
            )

        # ----------------------------------------------------
        # Attractions
        # ----------------------------------------------------

        if attractions:

            parts.append(
                "Architecture and Features: "
                + attractions
            )

        # ----------------------------------------------------
        # Activities
        # ----------------------------------------------------

        if activities:

            parts.append(
                "Activities and Visitor Information: "
                + activities
            )

        return "\n\n".join(
            parts
        ).strip()

    kb["rag_document"] = kb.apply(
        build_document,
        axis=1
    )

    # ========================================================
    # DOCUMENT QUALITY
    # ========================================================

    kb["document_length"] = (
        kb["rag_document"]
        .str.len()
    )

    def document_quality(length):

        if length >= 3000:
            return "high"

        elif length >= 1000:
            return "medium"

        elif length >= 300:
            return "low"

        return "insufficient"

    kb["document_quality"] = (
        kb["document_length"]
        .apply(document_quality)
    )

    # ========================================================
    # HAS LOCATION
    # ========================================================

    kb["has_location"] = (
        kb["latitude"]
        .astype(str)
        .str.strip()
        .ne("")
        &
        kb["longitude"]
        .astype(str)
        .str.strip()
        .ne("")
    )

    # ========================================================
    # HAS VIDEOS
    # ========================================================

    kb["has_youtube"] = (
        pd.to_numeric(
            kb["youtube_count"],
            errors="coerce"
        )
        .fillna(0)
        .gt(0)
    )

    kb["has_tiktok"] = (
        kb["tiktok_search_url"]
        .astype(str)
        .str.strip()
        .ne("")
    )

    # ========================================================
    # FINAL COLUMN ORDER
    # ========================================================

    preferred_columns = [
        "landmark_id",
        "landmark_name",
        "folder_name",
        "image_count",

        "city",
        "governorate",
        "country",
        "latitude",
        "longitude",
        "display_name",

        "tourism_description",
        "tourism_history",
        "tourism_attractions",
        "tourism_activities",

        "clean_text",

        "source_url",
        "tourism_url",

        "youtube_videos",
        "youtube_count",

        "tiktok_search_url",
        "tiktok_status",

        "rag_document",
        "document_length",
        "document_quality",

        "has_location",
        "has_youtube",
        "has_tiktok",

        "status",
        "tourism_status",
        "location_status"
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in kb.columns
    ]

    kb = kb[
        final_columns
    ]

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    before = len(kb)

    kb = (
        kb
        .drop_duplicates(
            subset=["landmark_name"]
        )
        .reset_index(drop=True)
    )

    duplicates = (
        before - len(kb)
    )

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    kb.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # REPORT
    # ========================================================

    print("\n" + "=" * 75)
    print("🎉 KNOWLEDGE BASE CREATED")
    print("=" * 75)

    print(
        f"\n🏛️ Total landmarks: "
        f"{len(kb)}"
    )

    print(
        f"🗑️ Duplicates removed: "
        f"{duplicates}"
    )

    print(
        f"📍 With location: "
        f"{kb['has_location'].sum()}"
    )

    print(
        f"▶️ With YouTube: "
        f"{kb['has_youtube'].sum()}"
    )

    print(
        f"🎵 With TikTok search: "
        f"{kb['has_tiktok'].sum()}"
    )

    print("\n🧠 Document quality:")

    print(
        kb[
            "document_quality"
        ]
        .value_counts()
        .to_string()
    )

    print("\n📄 Output:")

    print(
        OUTPUT_FILE.resolve()
    )


if __name__ == "__main__":
    main()