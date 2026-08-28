from pathlib import Path
import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# VIDEO DISCOVERY
# YouTube + TikTok
# ============================================================

load_dotenv()

INPUT_FILE = Path("data/tourism_enriched.csv")
OUTPUT_FILE = Path("data/videos.csv")

YOUTUBE_API_KEY = os.getenv(
    "YOUTUBE_API_KEY",
    ""
)

YOUTUBE_SEARCH_URL = (
    "https://www.googleapis.com/youtube/v3/search"
)

YOUTUBE_RESULTS_PER_LANDMARK = 3


# ============================================================
# YOUTUBE
# ============================================================

def search_youtube(landmark_name):

    if not YOUTUBE_API_KEY:

        print(
            "   ⚠️ YOUTUBE_API_KEY not configured."
        )

        return []

    params = {
        "part": "snippet",
        "q": f"{landmark_name} Egypt",
        "type": "video",
        "maxResults": YOUTUBE_RESULTS_PER_LANDMARK,
        "order": "relevance",
        "safeSearch": "moderate",
        "key": YOUTUBE_API_KEY
    }

    try:

        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        videos = []

        for item in data.get(
            "items",
            []
        ):

            video_id = (
                item
                .get("id", {})
                .get("videoId")
            )

            snippet = item.get(
                "snippet",
                {}
            )

            if not video_id:
                continue

            videos.append({

                "title":
                    snippet.get(
                        "title",
                        ""
                    ),

                "url":
                    f"https://www.youtube.com/watch?v={video_id}",

                "channel":
                    snippet.get(
                        "channelTitle",
                        ""
                    ),

                "published_at":
                    snippet.get(
                        "publishedAt",
                        ""
                    ),

                "thumbnail":
                    snippet.get(
                        "thumbnails",
                        {}
                    )
                    .get(
                        "high",
                        {}
                    )
                    .get(
                        "url",
                        ""
                    )
            })

        return videos

    except Exception as e:

        print(
            f"   ❌ YouTube error: {e}"
        )

        return []


# ============================================================
# TIKTOK
# ============================================================

def build_tiktok_search(landmark_name):

    """
    We don't scrape TikTok directly.

    Instead, create a TikTok search URL
    that the application can open later.
    """

    query = (
        landmark_name
        .replace(" ", "%20")
    )

    return (
        f"https://www.tiktok.com/search?q={query}"
    )


# ============================================================
# PROCESS ONE LANDMARK
# ============================================================

def process_landmark(landmark_name):

    print(
        f"\n🎥 Searching videos for: "
        f"{landmark_name}"
    )

    # --------------------------------------------------------
    # YouTube
    # --------------------------------------------------------

    print(
        "   ▶️ Searching YouTube..."
    )

    youtube_videos = search_youtube(
        landmark_name
    )

    print(
        f"   ✅ YouTube results: "
        f"{len(youtube_videos)}"
    )

    # --------------------------------------------------------
    # TikTok
    # --------------------------------------------------------

    print(
        "   🎵 Creating TikTok search..."
    )

    tiktok_search_url = (
        build_tiktok_search(
            landmark_name
        )
    )

    return {

        "landmark_name":
            landmark_name,

        "youtube_videos":
            json.dumps(
                youtube_videos,
                ensure_ascii=False
            ),

        "youtube_count":
            len(youtube_videos),

        "tiktok_search_url":
            tiktok_search_url,

        "tiktok_status":
            "search_url"
    }


# ============================================================
# LOAD EXISTING
# ============================================================

def load_existing():

    if not OUTPUT_FILE.exists():

        return {}

    try:

        df = pd.read_csv(
            OUTPUT_FILE
        ).fillna("")

        results = {}

        for _, row in df.iterrows():

            results[
                row["landmark_name"]
            ] = row.to_dict()

        return results

    except Exception:

        return {}


# ============================================================
# SAVE
# ============================================================

def save_results(results):

    df = pd.DataFrame(
        list(results.values())
    )

    if not df.empty:

        df = df.sort_values(
            "landmark_name"
        )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("🇪🇬 EGYPT EXPLORER AI")
    print("🎥 VIDEO DISCOVERY")
    print("=" * 70)

    # --------------------------------------------------------
    # Input
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        print(
            "\n❌ tourism_enriched.csv not found!"
        )

        return

    df = pd.read_csv(
        INPUT_FILE
    ).fillna("")

    print(
        f"\n📊 Total landmarks: "
        f"{len(df)}"
    )

    # --------------------------------------------------------
    # API status
    # --------------------------------------------------------

    if YOUTUBE_API_KEY:

        print(
            "🔑 YouTube API key: configured"
        )

    else:

        print(
            "⚠️ YouTube API key: NOT configured"
        )

        print(
            "   YouTube results will be empty."
        )

    # --------------------------------------------------------
    # Existing
    # --------------------------------------------------------

    results = load_existing()

    print(
        f"♻️ Existing video records: "
        f"{len(results)}"
    )

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    for index, row in df.iterrows():

        landmark_name = row[
            "landmark_name"
        ]

        print("\n" + "-" * 70)

        print(
            f"🏛️ [{index + 1}/{len(df)}] "
            f"{landmark_name}"
        )

        # Skip completed
        if landmark_name in results:

            existing = results[
                landmark_name
            ]

            if (
                existing.get(
                    "tiktok_search_url",
                    ""
                )
                and
                (
                    existing.get(
                        "youtube_count",
                        ""
                    )
                    != ""
                )
            ):

                print(
                    "   ⏭️ Already processed."
                )

                continue

        result = process_landmark(
            landmark_name
        )

        # Add original information
        result.update({
            "landmark_id":
                row.get(
                    "landmark_id",
                    ""
                ),

            "city":
                row.get(
                    "city",
                    ""
                ),

            "latitude":
                row.get(
                    "latitude",
                    ""
                ),

            "longitude":
                row.get(
                    "longitude",
                    ""
                )
        })

        results[
            landmark_name
        ] = result

        # Save immediately
        save_results(
            results
        )

        print(
            "   💾 Progress saved."
        )

        time.sleep(1)

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    save_results(
        results
    )

    final_df = pd.DataFrame(
        list(results.values())
    )

    print("\n" + "=" * 70)
    print("🎉 VIDEO DISCOVERY FINISHED")
    print("=" * 70)

    print(
        f"\n📊 Total records: "
        f"{len(final_df)}"
    )

    if "youtube_count" in final_df:

        print(
            f"▶️ Total YouTube videos: "
            f"{final_df['youtube_count'].sum()}"
        )

    print(
        "\n📄 Output:"
    )

    print(
        OUTPUT_FILE.resolve()
    )


if __name__ == "__main__":
    main()