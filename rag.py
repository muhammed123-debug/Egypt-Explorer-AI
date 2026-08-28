import json
import numpy as np

from sentence_transformers import SentenceTransformer

from vector_store import load_vector_store, search
from llm import create_llm


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# RAG ENGINE
# ============================================================

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

DEFAULT_TOP_K = 5


# ============================================================
# RAG ENGINE
# ============================================================

class EgyptExplorerRAG:

    def __init__(
        self,
        top_k=DEFAULT_TOP_K,
        llm=None
    ):

        self.top_k = top_k

        # ----------------------------------------------------
        # Embedding Model
        # ----------------------------------------------------

        print(
            "🧠 Loading embedding model..."
        )

        self.embedding_model = (
            SentenceTransformer(
                EMBEDDING_MODEL_NAME
            )
        )

        print(
            "✅ Embedding model loaded."
        )

        # ----------------------------------------------------
        # Vector Store
        # ----------------------------------------------------

        print(
            "📚 Loading FAISS vector store..."
        )

        (
            self.index,
            self.metadata
        ) = load_vector_store()

        print(
            f"✅ Vector store loaded: "
            f"{self.index.ntotal} vectors"
        )

        # ----------------------------------------------------
        # LLM
        # ----------------------------------------------------

        print(
            "🤖 Initializing LLM..."
        )

        self.llm = (
            llm
            if llm is not None
            else create_llm()
        )

        print(
            "✅ LLM ready."
        )


    # ========================================================
    # EMBED QUERY
    # ========================================================

    def embed_query(
        self,
        question
    ):

        embedding = (
            self.embedding_model.encode(
                [question],
                normalize_embeddings=True,
                convert_to_numpy=True
            )
        )

        return np.asarray(
            embedding,
            dtype=np.float32
        )


    # ========================================================
    # RETRIEVE
    # ========================================================

    def retrieve(
        self,
        question,
        top_k=None
    ):

        if top_k is None:

            top_k = self.top_k

        query_embedding = (
            self.embed_query(
                question
            )
        )

        results = search(
            query_embedding,
            self.index,
            self.metadata,
            top_k=top_k
        )

        return results


    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    def build_context(
        self,
        results
    ):

        context_parts = []

        for i, result in enumerate(
            results,
            start=1
        ):

            landmark_name = result.get(
                "landmark_name",
                ""
            )

            city = result.get(
                "city",
                ""
            )

            governorate = result.get(
                "governorate",
                ""
            )

            latitude = result.get(
                "latitude",
                ""
            )

            longitude = result.get(
                "longitude",
                ""
            )

            document = result.get(
                "document",
                ""
            )

            # ------------------------------------------------
            # Important:
            # Some versions of knowledge_base.py
            # may store the RAG text as rag_document.
            # ------------------------------------------------

            if not document:

                document = result.get(
                    "rag_document",
                    ""
                )

            source_url = result.get(
                "source_url",
                ""
            )

            tourism_url = result.get(
                "tourism_url",
                ""
            )

            score = result.get(
                "score",
                0
            )

            part = f"""
DOCUMENT {i}

Landmark:
{landmark_name}

Location:
{city}, {governorate}

Coordinates:
{latitude}, {longitude}

Information:
{document}

Source:
{source_url}

Tourism Source:
{tourism_url}

Similarity Score:
{score:.4f}
""".strip()

            context_parts.append(
                part
            )

        return "\n\n".join(
            context_parts
        )


    # ========================================================
    # EXTRACT MEDIA
    # ========================================================

    def extract_media(
        self,
        results
    ):

        youtube_videos = []

        tiktok_links = []

        sources = []

        # ----------------------------------------------------
        # Process retrieved landmarks
        # ----------------------------------------------------

        for result in results:

            # =================================================
            # YouTube
            # =================================================

            youtube_raw = result.get(
                "youtube_videos",
                "[]"
            )

            try:

                videos = json.loads(
                    youtube_raw
                )

                if isinstance(
                    videos,
                    list
                ):

                    youtube_videos.extend(
                        videos
                    )

            except Exception:

                pass

            # =================================================
            # TikTok
            # =================================================

            tiktok_url = result.get(
                "tiktok_search_url",
                ""
            )

            if tiktok_url:

                tiktok_links.append({

                    "landmark_name":
                        result.get(
                            "landmark_name",
                            ""
                        ),

                    "url":
                        tiktok_url
                })

            # =================================================
            # Sources
            # =================================================

            source_url = result.get(
                "source_url",
                ""
            )

            tourism_url = result.get(
                "tourism_url",
                ""
            )

            if source_url:

                sources.append(
                    source_url
                )

            if tourism_url:

                sources.append(
                    tourism_url
                )

        # ----------------------------------------------------
        # Remove duplicate sources
        # ----------------------------------------------------

        sources = list(
            dict.fromkeys(
                sources
            )
        )

        return {

            "youtube":
                youtube_videos,

            "tiktok":
                tiktok_links,

            "sources":
                sources
        }


    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    def generate_answer(
        self,
        question,
        context
    ):

        if not context:

            return (
                "مش لاقي معلومات كافية في "
                "قاعدة البيانات للإجابة على السؤال."
            )

        # ----------------------------------------------------
        # Send context to LLM
        # ----------------------------------------------------

        answer = self.llm.generate(
            question=question,
            context=context
        )

        return answer


    # ========================================================
    # ASK
    # ========================================================

    def ask(
        self,
        question,
        top_k=None
    ):

        question = str(
            question
        ).strip()

        if not question:

            return {

                "success":
                    False,

                "answer":
                    "من فضلك اكتب سؤالك.",

                "results":
                    [],

                "media":
                    {}
            }

        try:

            # ------------------------------------------------
            # Retrieval
            # ------------------------------------------------

            results = self.retrieve(
                question,
                top_k=top_k
            )

            if not results:

                return {

                    "success":
                        False,

                    "answer":
                        "مش لاقي معلومات مرتبطة "
                        "بسؤالك في قاعدة البيانات.",

                    "results":
                        [],

                    "media":
                        {}
                }

            # ------------------------------------------------
            # Context
            # ------------------------------------------------

            context = self.build_context(
                results
            )

            # ------------------------------------------------
            # LLM
            # ------------------------------------------------

            answer = self.generate_answer(
                question,
                context
            )

            # ------------------------------------------------
            # Media
            # ------------------------------------------------

            media = self.extract_media(
                results
            )

            return {

                "success":
                    True,

                "question":
                    question,

                "answer":
                    answer,

                "results":
                    results,

                "media":
                    media
            }

        except Exception as e:

            return {

                "success":
                    False,

                "answer":
                    f"حصل خطأ أثناء معالجة السؤال: {e}",

                "results":
                    [],

                "media":
                    {}
            }


# ============================================================
# FACTORY
# ============================================================

def create_rag(
    top_k=DEFAULT_TOP_K
):

    return EgyptExplorerRAG(
        top_k=top_k
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 75)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("🧠 RAG ENGINE")
    print("=" * 75)

    print(
        "\nRAG engine configuration:"
    )

    print(
        "1. Multilingual embeddings"
    )

    print(
        "2. FAISS vector search"
    )

    print(
        "3. Groq LLM"
    )

    print(
        "4. Tourism sources"
    )

    print(
        "5. YouTube + TikTok metadata"
    )

    print(
        "\n✅ RAG module ready."
    )


if __name__ == "__main__":

    main()