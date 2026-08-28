import os
import tempfile

import gradio as gr

from rag import create_rag
from voice import create_voice_engine


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# APPLICATION
# ============================================================

APP_TITLE = "🇪🇬 Egypt Explorer AI"

APP_DESCRIPTION = """
### Explore Egypt with AI 🏛️

Ask about Egyptian landmarks, locations, history,
activities, and related videos.

You can type your question or use your voice. 🎤
"""


# ============================================================
# GLOBAL ENGINES
# ============================================================

rag_engine = None
voice_engine = None


# ============================================================
# INITIALIZATION
# ============================================================

def initialize():

    global rag_engine
    global voice_engine

    print("=" * 70)
    print("🚀 INITIALIZING EGYPT EXPLORER AI")
    print("=" * 70)

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    print("\n🧠 Initializing RAG...")

    rag_engine = create_rag()

    # --------------------------------------------------------
    # Voice
    # --------------------------------------------------------

    print("\n🎤 Initializing Voice...")

    voice_engine = create_voice_engine()

    print("\n" + "=" * 70)
    print("✅ EGYPT EXPLORER AI READY")
    print("=" * 70)


# ============================================================
# SOURCES
# ============================================================

def format_sources(results):

    if not results:

        return "No sources found."

    output = []

    for i, result in enumerate(
        results,
        start=1
    ):

        name = result.get(
            "landmark_name",
            "Unknown"
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

        score = result.get(
            "score",
            0
        )

        source = result.get(
            "source_url",
            ""
        )

        location = ", ".join(
            x for x in [
                city,
                governorate
            ]
            if str(x).strip()
        )

        output.append(
            f"""
### {i}. {name}

📍 **Location:** {location or "Not available"}

🌐 **Coordinates:** {latitude}, {longitude}

🔎 **Relevance:** {score:.3f}

🔗 **Source:** {source or "Not available"}
""".strip()
        )

    return "\n\n---\n\n".join(
        output
    )


# ============================================================
# YOUTUBE
# ============================================================

def format_youtube(videos):

    if not videos:

        return (
            "No YouTube videos available."
        )

    output = []

    seen = set()

    for i, video in enumerate(
        videos,
        start=1
    ):

        url = video.get(
            "url",
            ""
        )

        if not url or url in seen:

            continue

        seen.add(url)

        title = video.get(
            "title",
            "YouTube Video"
        )

        channel = video.get(
            "channel",
            ""
        )

        thumbnail = video.get(
            "thumbnail",
            ""
        )

        block = (
            f"### 🎥 {i}. {title}\n\n"
            f"**Channel:** {channel}\n\n"
            f"[▶️ Watch on YouTube]({url})"
        )

        if thumbnail:

            block += (
                f"\n\n![Thumbnail]({thumbnail})"
            )

        output.append(
            block
        )

    if not output:

        return (
            "No YouTube videos available."
        )

    return "\n\n".join(
        output[:10]
    )


# ============================================================
# TIKTOK
# ============================================================

def format_tiktok(links):

    if not links:

        return (
            "No TikTok results available."
        )

    output = []

    seen = set()

    for item in links:

        url = item.get(
            "url",
            ""
        )

        name = item.get(
            "landmark_name",
            "TikTok"
        )

        if not url or url in seen:

            continue

        seen.add(url)

        output.append(
            f"""
### 📱 {name}

[🎵 Search TikTok videos]({url})
""".strip()
        )

    if not output:

        return (
            "No TikTok results available."
        )

    return "\n\n".join(
        output
    )


# ============================================================
# BUILD DETAILS
# ============================================================

def build_details(
    results,
    media
):

    sources = format_sources(
        results
    )

    youtube = format_youtube(
        media.get(
            "youtube",
            []
        )
    )

    tiktok = format_tiktok(
        media.get(
            "tiktok",
            []
        )
    )

    return f"""
## 📚 Sources

{sources}

---

## 🎥 YouTube

{youtube}

---

## 📱 TikTok

{tiktok}
""".strip()


# ============================================================
# TEXT CHAT
# ============================================================

def chat(
    question,
    history
):

    if not question:

        return (
            history or [],
            "",
            "⚠️ Please enter a question."
        )

    question = question.strip()

    if not question:

        return (
            history or [],
            "",
            "⚠️ Please enter a question."
        )

    try:

        result = rag_engine.ask(
            question
        )

        if not result.get(
            "success",
            False
        ):

            answer = result.get(
                "answer",
                "Unable to answer."
            )

            return (
                history or [],
                "",
                answer
            )

        answer = result.get(
            "answer",
            ""
        )

        results = result.get(
            "results",
            []
        )

        media = result.get(
            "media",
            {}
        )

        history = history or []

        history.append({

            "role":
                "user",

            "content":
                question
        })

        history.append({

            "role":
                "assistant",

            "content":
                answer
        })

        details = build_details(
            results,
            media
        )

        return (
            history,
            "",
            details
        )

    except Exception as e:

        return (
            history or [],
            "",
            f"❌ Error: {e}"
        )


# ============================================================
# VOICE CHAT
# ============================================================

def voice_chat(
    audio
):

    if audio is None:

        return (
            None,
            "",
            "🎤 Please record your question."
        )

    try:

        # ----------------------------------------------------
        # Speech → Text
        # ----------------------------------------------------

        print(
            "\n🎤 Transcribing audio..."
        )

        question = (
            voice_engine
            .speech_to_text(
                audio
            )
        )

        if not question:

            return (
                None,
                "",
                "❌ Could not understand the audio."
            )

        print(
            f"📝 Question: {question}"
        )

        # ----------------------------------------------------
        # RAG
        # ----------------------------------------------------

        print(
            "🧠 Running RAG..."
        )

        result = rag_engine.ask(
            question
        )

        answer = result.get(
            "answer",
            ""
        )

        results = result.get(
            "results",
            []
        )

        media = result.get(
            "media",
            {}
        )

        # ----------------------------------------------------
        # Text → Speech
        # ----------------------------------------------------

        print(
            "🔊 Generating voice..."
        )

        audio_bytes = (
            voice_engine
            .text_to_speech(
                answer
            )
        )

        # ----------------------------------------------------
        # Temporary audio file
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as temp:

            temp.write(
                audio_bytes
            )

            audio_path = temp.name

        # ----------------------------------------------------
        # Details
        # ----------------------------------------------------

        details = f"""
## 📝 Your Question

{question}

---

## 📚 Sources

{format_sources(results)}

---

## 🎥 YouTube

{format_youtube(
    media.get(
        "youtube",
        []
    )
)}

---

## 📱 TikTok

{format_tiktok(
    media.get(
        "tiktok",
        []
    )
)}
""".strip()

        return (
            audio_path,
            answer,
            details
        )

    except Exception as e:

        return (
            None,
            "",
            f"❌ Voice error: {e}"
        )


# ============================================================
# CLEAR
# ============================================================

def clear_chat():

    return (
        [],
        "",
        ""
    )


# ============================================================
# UI
# ============================================================

def build_ui():

    with gr.Blocks(
        title=APP_TITLE
    ) as demo:

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        gr.Markdown(
            f"""
# {APP_TITLE}

{APP_DESCRIPTION}
"""
        )

        # ====================================================
        # TABS
        # ====================================================

        with gr.Tabs():

            # =================================================
            # CHAT
            # =================================================

            with gr.Tab(
                "💬 Text Chat"
            ):

                chatbot = gr.Chatbot(
                    label="Egypt Explorer AI",
                    type="messages",
                    height=500
                )

                question = gr.Textbox(
                    label="Your Question",
                    placeholder=(
                        "مثال: احكيلي عن قلعة قايتباي "
                        "وموجودة فين؟"
                    ),
                    lines=3
                )

                with gr.Row():

                    ask_button = gr.Button(
                        "🚀 Ask",
                        variant="primary"
                    )

                    clear_button = gr.Button(
                        "🧹 Clear"
                    )

                details = gr.Markdown()

                # --------------------------------------------
                # Button
                # --------------------------------------------

                ask_button.click(
                    fn=chat,
                    inputs=[
                        question,
                        chatbot
                    ],
                    outputs=[
                        chatbot,
                        question,
                        details
                    ]
                )

                # --------------------------------------------
                # Enter
                # --------------------------------------------

                question.submit(
                    fn=chat,
                    inputs=[
                        question,
                        chatbot
                    ],
                    outputs=[
                        chatbot,
                        question,
                        details
                    ]
                )

                # --------------------------------------------
                # Clear
                # --------------------------------------------

                clear_button.click(
                    fn=clear_chat,
                    outputs=[
                        chatbot,
                        question,
                        details
                    ]
                )

            # =================================================
            # VOICE
            # =================================================

            with gr.Tab(
                "🎤 Voice Chat"
            ):

                gr.Markdown(
                    """
### 🎤 Talk to Egypt Explorer AI

Record your question and the system will:

**Speech → Text → RAG → AI Answer → Voice**
"""
                )

                audio_input = gr.Audio(
                    sources=[
                        "microphone",
                        "upload"
                    ],
                    type="filepath",
                    label="🎤 Record your question"
                )

                voice_button = gr.Button(
                    "🎙️ Ask by Voice",
                    variant="primary"
                )

                voice_answer = gr.Textbox(
                    label="🤖 AI Answer",
                    lines=7
                )

                voice_output = gr.Audio(
                    label="🔊 Voice Answer",
                    type="filepath",
                    autoplay=True
                )

                voice_details = gr.Markdown()

                voice_button.click(
                    fn=voice_chat,
                    inputs=[
                        audio_input
                    ],
                    outputs=[
                        voice_output,
                        voice_answer,
                        voice_details
                    ]
                )

        # ----------------------------------------------------
        # Footer
        # ----------------------------------------------------

        gr.Markdown(
            """
---

### 🇪🇬 Egypt Explorer AI

**AI-powered RAG Tourism Assistant for Egypt**

🏛️ Landmarks • 📍 Locations • 🎥 Videos • 🎤 Voice
"""
        )

    return demo


# ============================================================
# LAUNCH
# ============================================================

def launch():

    initialize()

    demo = build_ui()

    print(
        "\n🚀 Launching Gradio..."
    )

    demo.launch(
        share=True
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    launch()