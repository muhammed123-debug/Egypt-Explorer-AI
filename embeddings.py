from pathlib import Path
import json
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# EMBEDDING GENERATION
# ============================================================

INPUT_FILE = Path("data/knowledge_base.csv")

OUTPUT_DIR = Path("data/embeddings")

EMBEDDINGS_FILE = OUTPUT_DIR / "embeddings.npy"

METADATA_FILE = OUTPUT_DIR / "metadata.json"

MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

BATCH_SIZE = 32


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    print("\n🧠 Loading embedding model...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    print(
        "✅ Embedding model loaded."
    )

    return model


# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Knowledge base not found: "
            f"{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    ).fillna("")

    print(
        f"\n📚 Knowledge base records: "
        f"{len(df)}"
    )

    return df


# ============================================================
# PREPARE DOCUMENTS
# ============================================================

def prepare_documents(df):

    documents = []

    valid_indexes = []

    for index, row in df.iterrows():

        document = str(
            row.get(
                "rag_document",
                ""
            )
        ).strip()

        # Skip empty documents
        if not document:

            continue

        documents.append(
            document
        )

        valid_indexes.append(
            index
        )

    print(
        f"📄 Valid documents: "
        f"{len(documents)}"
    )

    print(
        f"⚠️ Empty documents skipped: "
        f"{len(df) - len(documents)}"
    )

    return documents, valid_indexes


# ============================================================
# CREATE METADATA
# ============================================================

def create_metadata(
    df,
    valid_indexes
):

    metadata = []

    for index in valid_indexes:

        row = df.loc[index]

        metadata.append({

            "index":
                len(metadata),

            "landmark_id":
                str(
                    row.get(
                        "landmark_id",
                        ""
                    )
                ),

            "landmark_name":
                str(
                    row.get(
                        "landmark_name",
                        ""
                    )
                ),

            "city":
                str(
                    row.get(
                        "city",
                        ""
                    )
                ),

            "governorate":
                str(
                    row.get(
                        "governorate",
                        ""
                    )
                ),

            "country":
                str(
                    row.get(
                        "country",
                        "Egypt"
                    )
                ),

            "latitude":
                str(
                    row.get(
                        "latitude",
                        ""
                    )
                ),

            "longitude":
                str(
                    row.get(
                        "longitude",
                        ""
                    )
                ),

            "source_url":
                str(
                    row.get(
                        "source_url",
                        ""
                    )
                ),

            "tourism_url":
                str(
                    row.get(
                        "tourism_url",
                        ""
                    )
                ),

            "youtube_videos":
                str(
                    row.get(
                        "youtube_videos",
                        "[]"
                    )
                ),

            "tiktok_search_url":
                str(
                    row.get(
                        "tiktok_search_url",
                        ""
                    )
                )
        })

    return metadata


# ============================================================
# GENERATE EMBEDDINGS
# ============================================================

def generate_embeddings(
    model,
    documents
):

    print(
        "\n🔄 Generating embeddings..."
    )

    embeddings = model.encode(
        documents,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    print(
        "\n✅ Embeddings generated."
    )

    print(
        f"📐 Shape: {embeddings.shape}"
    )

    return embeddings


# ============================================================
# SAVE
# ============================================================

def save_embeddings(
    embeddings,
    metadata
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save vectors
    # --------------------------------------------------------

    np.save(
        EMBEDDINGS_FILE,
        embeddings
    )

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        "\n💾 Embeddings saved:"
    )

    print(
        EMBEDDINGS_FILE.resolve()
    )

    print(
        "\n💾 Metadata saved:"
    )

    print(
        METADATA_FILE.resolve()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("🧠 EMBEDDING GENERATION")
    print("=" * 75)

    # --------------------------------------------------------
    # Load knowledge base
    # --------------------------------------------------------

    df = load_knowledge_base()

    # --------------------------------------------------------
    # Prepare documents
    # --------------------------------------------------------

    documents, valid_indexes = (
        prepare_documents(df)
    )

    if not documents:

        print(
            "\n❌ No valid documents found."
        )

        return

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = load_model()

    # --------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------

    embeddings = generate_embeddings(
        model,
        documents
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata = create_metadata(
        df,
        valid_indexes
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if len(embeddings) != len(metadata):

        raise ValueError(
            "Embeddings and metadata "
            "have different lengths."
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_embeddings(
        embeddings,
        metadata
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("\n" + "=" * 75)
    print("🎉 EMBEDDING PIPELINE READY")
    print("=" * 75)

    print(
        f"\n📚 Documents: "
        f"{len(documents)}"
    )

    print(
        f"📐 Vector dimensions: "
        f"{embeddings.shape[1]}"
    )

    print(
        "\n📁 Output directory:"
    )

    print(
        OUTPUT_DIR.resolve()
    )


if __name__ == "__main__":
    main()