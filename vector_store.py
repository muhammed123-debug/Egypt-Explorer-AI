from pathlib import Path
import json

import faiss
import numpy as np


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# FAISS VECTOR STORE
# ============================================================

EMBEDDINGS_FILE = Path(
    "data/embeddings/embeddings.npy"
)

METADATA_FILE = Path(
    "data/embeddings/metadata.json"
)

VECTOR_STORE_DIR = Path(
    "data/vector_store"
)

INDEX_FILE = (
    VECTOR_STORE_DIR / "egypt_explorer.faiss"
)

STORE_METADATA_FILE = (
    VECTOR_STORE_DIR / "metadata.json"
)


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

def load_embeddings():

    if not EMBEDDINGS_FILE.exists():

        raise FileNotFoundError(
            f"Embeddings file not found:\n"
            f"{EMBEDDINGS_FILE}"
        )

    embeddings = np.load(
        EMBEDDINGS_FILE
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    if len(embeddings) == 0:

        raise ValueError(
            "Embeddings file is empty."
        )

    return embeddings


# ============================================================
# LOAD METADATA
# ============================================================

def load_metadata():

    if not METADATA_FILE.exists():

        raise FileNotFoundError(
            f"Metadata file not found:\n"
            f"{METADATA_FILE}"
        )

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(
            file
        )

    if not metadata:

        raise ValueError(
            "Metadata file is empty."
        )

    return metadata


# ============================================================
# BUILD INDEX
# ============================================================

def build_index(embeddings):

    dimension = embeddings.shape[1]

    print(
        f"\n📐 Vector dimension: "
        f"{dimension}"
    )

    print(
        f"📚 Number of vectors: "
        f"{len(embeddings)}"
    )

    # --------------------------------------------------------
    # Inner Product
    #
    # embeddings are normalized in embeddings.py.
    #
    # Therefore:
    #
    # Inner Product ≈ Cosine Similarity
    # --------------------------------------------------------

    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(
        embeddings
    )

    print(
        "\n✅ FAISS index built."
    )

    print(
        f"📊 FAISS total vectors: "
        f"{index.ntotal}"
    )

    return index


# ============================================================
# SAVE VECTOR STORE
# ============================================================

def save_vector_store(
    index,
    metadata
):

    VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save FAISS index
    # --------------------------------------------------------

    faiss.write_index(
        index,
        str(INDEX_FILE)
    )

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    with open(
        STORE_METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        "\n💾 FAISS index saved:"
    )

    print(
        INDEX_FILE.resolve()
    )

    print(
        "\n💾 Metadata saved:"
    )

    print(
        STORE_METADATA_FILE.resolve()
    )


# ============================================================
# LOAD VECTOR STORE
# ============================================================

def load_vector_store():

    if not INDEX_FILE.exists():

        raise FileNotFoundError(
            f"FAISS index not found:\n"
            f"{INDEX_FILE}"
        )

    if not STORE_METADATA_FILE.exists():

        raise FileNotFoundError(
            f"Vector metadata not found:\n"
            f"{STORE_METADATA_FILE}"
        )

    index = faiss.read_index(
        str(INDEX_FILE)
    )

    with open(
        STORE_METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(
            file
        )

    return index, metadata


# ============================================================
# SEARCH
# ============================================================

def search(
    query_embedding,
    index,
    metadata,
    top_k=5
):

    query_embedding = np.asarray(
        query_embedding,
        dtype=np.float32
    )

    # Make sure shape is:
    # (1, embedding_dimension)

    if query_embedding.ndim == 1:

        query_embedding = (
            query_embedding.reshape(
                1,
                -1
            )
        )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    scores, indexes = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indexes[0]
    ):

        # FAISS can return -1
        if idx < 0:
            continue

        if idx >= len(metadata):
            continue

        result = dict(
            metadata[idx]
        )

        result["score"] = float(
            score
        )

        results.append(
            result
        )

    return results


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("🧠 FAISS VECTOR STORE")
    print("=" * 75)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print(
        "\n📂 Loading embeddings..."
    )

    embeddings = load_embeddings()

    print(
        f"✅ Shape: "
        f"{embeddings.shape}"
    )

    print(
        "\n📂 Loading metadata..."
    )

    metadata = load_metadata()

    print(
        f"✅ Metadata records: "
        f"{len(metadata)}"
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if len(embeddings) != len(metadata):

        raise ValueError(
            "Number of embeddings does not "
            "match number of metadata records."
        )

    # --------------------------------------------------------
    # Build
    # --------------------------------------------------------

    index = build_index(
        embeddings
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_vector_store(
        index,
        metadata
    )

    # ========================================================
    # FINAL
    # ========================================================

    print("\n" + "=" * 75)
    print("🎉 VECTOR DATABASE READY")
    print("=" * 75)

    print(
        f"\n📚 Vectors: "
        f"{index.ntotal}"
    )

    print(
        f"📐 Dimension: "
        f"{index.d}"
    )

    print(
        "\n📁 Directory:"
    )

    print(
        VECTOR_STORE_DIR.resolve()
    )


if __name__ == "__main__":
    main()