import io
import os
from typing import Optional

from dotenv import load_dotenv


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# VOICE ENGINE
# Speech-to-Text + Text-to-Speech
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

STT_MODEL = os.getenv(
    "STT_MODEL",
    "whisper-large-v3-turbo"
)

TTS_MODEL = os.getenv(
    "TTS_MODEL",
    "playai-tts"
)

TTS_VOICE = os.getenv(
    "TTS_VOICE",
    "Fritz-PlayAI"
)


# ============================================================
# SPEECH TO TEXT
# ============================================================

class SpeechToText:

    def __init__(
        self,
        api_key: Optional[str] = None
    ):

        self.api_key = (
            api_key
            or os.getenv("GROQ_API_KEY", "")
        )

        if not self.api_key:

            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        from groq import Groq

        self.client = Groq(
            api_key=self.api_key
        )

        print(
            f"🎤 STT initialized: "
            f"{STT_MODEL}"
        )


    def transcribe(
        self,
        audio_file,
        language=None
    ):

        """
        Convert an audio file into text.

        audio_file can be:
        - file path
        - file-like object
        - bytes
        """

        if isinstance(
            audio_file,
            str
        ):

            with open(
                audio_file,
                "rb"
            ) as file:

                audio_data = file.read()

            filename = os.path.basename(
                audio_file
            )

        elif isinstance(
            audio_file,
            bytes
        ):

            audio_data = audio_file
            filename = "audio.wav"

        else:

            audio_data = audio_file.read()

            filename = getattr(
                audio_file,
                "name",
                "audio.wav"
            )

            filename = os.path.basename(
                filename
            )

        audio_buffer = io.BytesIO(
            audio_data
        )

        audio_buffer.name = filename

        request = {
            "file": audio_buffer,
            "model": STT_MODEL
        }

        if language:

            request["language"] = language

        try:

            transcription = (
                self.client.audio.transcriptions.create(
                    **request
                )
            )

            return (
                transcription.text
                .strip()
            )

        except Exception as e:

            raise RuntimeError(
                f"Speech-to-text failed: {e}"
            )


# ============================================================
# TEXT TO SPEECH
# ============================================================

class TextToSpeech:

    def __init__(
        self,
        api_key: Optional[str] = None
    ):

        self.api_key = (
            api_key
            or os.getenv("GROQ_API_KEY", "")
        )

        if not self.api_key:

            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        from groq import Groq

        self.client = Groq(
            api_key=self.api_key
        )

        print(
            f"🔊 TTS initialized: "
            f"{TTS_MODEL}"
        )


    def synthesize(
        self,
        text,
        output_file=None
    ):

        """
        Convert text to speech.

        Returns audio bytes.

        If output_file is provided,
        the audio is also saved to disk.
        """

        text = str(
            text
        ).strip()

        if not text:

            raise ValueError(
                "Text cannot be empty."
            )

        try:

            response = (
                self.client.audio.speech.create(
                    model=TTS_MODEL,
                    voice=TTS_VOICE,
                    input=text,
                    response_format="wav"
                )
            )

            audio_bytes = (
                response.read()
            )

            if output_file:

                with open(
                    output_file,
                    "wb"
                ) as file:

                    file.write(
                        audio_bytes
                    )

            return audio_bytes

        except Exception as e:

            raise RuntimeError(
                f"Text-to-speech failed: {e}"
            )


# ============================================================
# VOICE ENGINE
# ============================================================

class VoiceEngine:

    def __init__(
        self,
        api_key=None
    ):

        print(
            "\n🎙️ Initializing voice engine..."
        )

        self.stt = SpeechToText(
            api_key=api_key
        )

        self.tts = TextToSpeech(
            api_key=api_key
        )

        print(
            "✅ Voice engine ready."
        )


    # ========================================================
    # AUDIO → TEXT
    # ========================================================

    def speech_to_text(
        self,
        audio_file,
        language=None
    ):

        return self.stt.transcribe(
            audio_file,
            language=language
        )


    # ========================================================
    # TEXT → AUDIO
    # ========================================================

    def text_to_speech(
        self,
        text,
        output_file=None
    ):

        return self.tts.synthesize(
            text,
            output_file=output_file
        )


# ============================================================
# FACTORY
# ============================================================

def create_voice_engine(
    api_key=None
):

    return VoiceEngine(
        api_key=api_key
    )