from pathlib import Path
import re
import pandas as pd

# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# DATA CLEANING & RAG PREPARATION
# ============================================================

INPUT_FILE = Path("data/scraped_landmarks.csv")
OUTPUT_FILE = Path("data/tourism_data.csv")


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    """
    Clean scraped text without changing its meaning.
    """

    if pd.isna(text):
        return ""

    text = str(text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove spaces around punctuation
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    return text.strip()


def normalize_name(name):
    """
    Normalize landmark name.
    """

    if pd.isna(name):
        return ""

    name = str(name)

    name = re.sub(r"\s+", " ", name)

    return name.strip()


# ============================================================
# CREATE RAG DOCUMENT
# ============================================================

def create_document(row):
    """
    Create a clean document that will later be embedded.
    """

    landmark = row["landmark_name"]
    text = row["clean_text"]

    document = f"""
Tourist Landmark in Egypt

Name: {landmark}

Information:
{text}

Source: {row["source_url"]}
""".strip()

    return document


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("🧹 DATA CLEANING")
    print("=" * 70)

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        print(
            "\n❌ scraped_landmarks.csv not found!"
        )

        return

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_FILE
    ).fillna("")

    print(
        f"\n📊 Original records: {len(df)}"
    )

    # --------------------------------------------------------
    # Normalize names
    # --------------------------------------------------------

    df["landmark_name"] = (
        df["landmark_name"]
        .apply(normalize_name)
    )

    # --------------------------------------------------------
    # Clean scraped text
    # --------------------------------------------------------

    df["clean_text"] = (
        df["scraped_text"]
        .apply(clean_text)
    )

    # --------------------------------------------------------
    # Calculate quality
    # --------------------------------------------------------

    df["text_length"] = (
        df["clean_text"]
        .str.len()
    )

    def quality(length):

        if length >= 1000:
            return "high"

        elif length >= 500:
            return "medium"

        elif length >= 100:
            return "low"

        else:
            return "insufficient"

    df["data_quality"] = (
        df["text_length"]
        .apply(quality)
    )

    # --------------------------------------------------------
    # Create RAG document
    # --------------------------------------------------------

    df["document"] = df.apply(
        create_document,
        axis=1
    )

    # --------------------------------------------------------
    # Remove duplicate landmarks
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates(
        subset=["landmark_name"],
        keep="first"
    )

    duplicates_removed = (
        before - len(df)
    )

    # --------------------------------------------------------
    # Select useful columns
    # --------------------------------------------------------

    final_columns = [
        "landmark_id",
        "landmark_name",
        "folder_name",
        "image_count",
        "source_url",
        "wiki_title",
        "match_score",
        "text_length",
        "data_quality",
        "status",
        "clean_text",
        "document"
    ]

    df = df[
        final_columns
    ]

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # REPORT
    # ========================================================

    print("\n" + "=" * 70)
    print("🎉 CLEANING FINISHED")
    print("=" * 70)

    print(
        f"\n📊 Original records: "
        f"{before}"
    )

    print(
        f"🗑️ Duplicates removed: "
        f"{duplicates_removed}"
    )

    print(
        f"📚 Final records: "
        f"{len(df)}"
    )

    print("\n📈 Data quality:")

    print(
        df["data_quality"]
        .value_counts()
        .to_string()
    )

    print("\n📊 Status:")

    print(
        df["status"]
        .value_counts()
        .to_string()
    )

    print("\n📄 Output:")

    print(
        OUTPUT_FILE.resolve()
    )

    print("\n🏛️ Sample landmarks:")

    print(
        df[
            [
                "landmark_name",
                "text_length",
                "data_quality"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()