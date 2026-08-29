from pathlib import Path
import os

from dotenv import load_dotenv


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# CENTRAL CONFIGURATION
# ============================================================

load_dotenv()


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

EMBEDDINGS_DIR = DATA_DIR / "embeddings"

VECTOR_STORE_DIR = DATA_DIR / "vector_store"


# ============================================================
# DATA FILES
# ============================================================

LANDMARKS_FILE = (
    DATA_DIR / "landmarks.csv"
)

SCRAPED_FILE = (
    DATA_DIR / "scraped_landmarks.csv"
)

TOURISM_FILE = (
    DATA_DIR / "tourism_data.csv"
)

LOCATION_FILE = (
    DATA_DIR / "enriched_tourism_data.csv"
)

TOURISM_ENRICHED_FILE = (
    DATA_DIR / "tourism_enriched.csv"
)

VIDEOS_FILE = (
    DATA_DIR / "videos.csv"
)

KNOWLEDGE_BASE_FILE = (
    DATA_DIR / "knowledge_base.csv"
)


# ============================================================
# VECTOR FILES
# ============================================================

EMBEDDINGS_FILE = (
    EMBEDDINGS_DIR / "embeddings.npy"
)

EMBEDDING_METADATA_FILE = (
    EMBEDDINGS_DIR / "metadata.json"
)

FAISS_INDEX_FILE = (
    VECTOR_STORE_DIR / "egypt_explorer.faiss"
)

VECTOR_METADATA_FILE = (
    VECTOR_STORE_DIR / "metadata.json"
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

EMBEDDING_BATCH_SIZE = int(
    os.getenv(
        "EMBEDDING_BATCH_SIZE",
        "32"
    )
)


# ============================================================
# RAG
# ============================================================

RAG_TOP_K = int(
    os.getenv(
        "RAG_TOP_K",
        "5"
    )
)

RAG_MIN_SCORE = float(
    os.getenv(
        "RAG_MIN_SCORE",
        "0.25"
    )
)


# ============================================================
# GROQ / LLM
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    ""
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)


# ============================================================
# SPEECH TO TEXT
# ============================================================

STT_MODEL = os.getenv(
    "STT_MODEL",
    "whisper-large-v3-turbo"
)


# ============================================================
# TEXT TO SPEECH
# ============================================================

TTS_MODEL = os.getenv(
    "TTS_MODEL",
    "playai-tts"
)

TTS_VOICE = os.getenv(
    "TTS_VOICE",
    "Fritz-PlayAI"
)


# ============================================================
# YOUTUBE
# ============================================================

YOUTUBE_API_KEY = os.getenv(
    "YOUTUBE_API_KEY",
    ""
)

YOUTUBE_RESULTS_PER_LANDMARK = int(
    os.getenv(
        "YOUTUBE_RESULTS_PER_LANDMARK",
        "3"
    )
)


# ============================================================
# APPLICATION
# ============================================================

APP_TITLE = os.getenv(
    "APP_TITLE",
    "🇪🇬 Egypt Explorer AI"
)

APP_SHARE = (
    os.getenv(
        "APP_SHARE",
        "true"
    ).lower()
    == "true"
)


# ============================================================
# NETWORK
# ============================================================

REQUEST_TIMEOUT = int(
    os.getenv(
        "REQUEST_TIMEOUT",
        "20"
    )
)

REQUEST_DELAY = float(
    os.getenv(
        "REQUEST_DELAY",
        "1.5"
    )
)


# ============================================================
# UTILITY
# ============================================================

def ensure_directories():

    directories = [
        DATA_DIR,
        RAW_DATA_DIR,
        EMBEDDINGS_DIR,
        VECTOR_STORE_DIR
    ]

    for directory in directories:

        directory.mkdir(
            parents=True,
            exist_ok=True
        )


# ============================================================
# CONFIG SUMMARY
# ============================================================

def print_config():

    print("=" * 70)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("⚙️ CONFIGURATION")
    print("=" * 70)

    print(
        f"\n📁 Base directory:"
        f"\n{BASE_DIR}"
    )

    print(
        f"\n📚 Knowledge base:"
        f"\n{KNOWLEDGE_BASE_FILE}"
    )

    print(
        f"\n🧠 Embedding model:"
        f"\n{EMBEDDING_MODEL}"
    )

    print(
        f"\n🔎 RAG Top-K:"
        f"\n{RAG_TOP_K}"
    )

    print(
        f"\n🤖 LLM:"
        f"\n{GROQ_MODEL}"
    )

    print(
        f"\n🎤 STT:"
        f"\n{STT_MODEL}"
    )

    print(
        f"\n🔊 TTS:"
        f"\n{TTS_MODEL}"
    )


if __name__ == "__main__":

    ensure_directories()

    print_config()
