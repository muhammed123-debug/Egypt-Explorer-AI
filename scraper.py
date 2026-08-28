from pathlib import Path
import time
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from urllib.parse import quote

# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# SMART WIKIPEDIA SCRAPER
# ============================================================

INPUT_FILE = Path("data/landmarks.csv")
OUTPUT_FILE = Path("data/scraped_landmarks.csv")

WIKI_BASE = "https://en.wikipedia.org"

HEADERS = {
    "User-Agent": (
        "EgyptExplorerAI/1.0 "
        "(Educational Tourism RAG Project; contact: local-project)"
    )
}

TIMEOUT = 20

# Don't hammer Wikipedia
MIN_DELAY = 2
MAX_DELAY = 4


# ============================================================
# SESSION
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# HELPERS
# ============================================================

def normalize(text):
    """Normalize text for comparison."""

    if not text:
        return ""

    return (
        text.lower()
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )


def similarity(a, b):
    """Calculate similarity between two names."""

    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b)
    ).ratio()


# ============================================================
# DIRECT WIKIPEDIA PAGE
# ============================================================

def get_direct_page(landmark_name):
    """
    Try the obvious Wikipedia URL first.

    This avoids the Search API for most landmarks.
    """

    title = landmark_name.replace(" ", "_")

    url = (
        WIKI_BASE
        + "/wiki/"
        + quote(title, safe="()_,.'-")
    )

    try:

        response = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        if response.status_code == 200:

            final_url = response.url

            # Extract final title from URL
            final_title = (
                final_url
                .split("/wiki/")[-1]
                .replace("_", " ")
            )

            # Remove URL encoding
            final_title = final_title.strip()

            score = similarity(
                landmark_name,
                final_title
            )

            # Accept if reasonably similar
            if score >= 0.45:

                return {
                    "url": final_url,
                    "title": final_title,
                    "score": score
                }

    except Exception:
        pass

    return None


# ============================================================
# WIKIPEDIA SEARCH WITH RETRY
# ============================================================

def search_wikipedia(landmark_name, retries=4):
    """
    Search Wikipedia only when direct page lookup fails.

    Uses exponential backoff for 429 responses.
    """

    api_url = f"{WIKI_BASE}/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": landmark_name,
        "format": "json",
        "utf8": 1,
        "srlimit": 3
    }

    for attempt in range(retries):

        try:

            response = session.get(
                api_url,
                params=params,
                timeout=TIMEOUT
            )

            # Rate limited
            if response.status_code == 429:

                wait = 10 * (2 ** attempt)

                print(
                    f"   ⏳ Wikipedia rate limit. "
                    f"Waiting {wait}s..."
                )

                time.sleep(wait)

                continue

            response.raise_for_status()

            data = response.json()

            results = (
                data
                .get("query", {})
                .get("search", [])
            )

            if not results:
                return None

            # Find best matching result
            best_result = None
            best_score = 0

            for result in results:

                title = result.get(
                    "title",
                    ""
                )

                score = similarity(
                    landmark_name,
                    title
                )

                if score > best_score:

                    best_score = score
                    best_result = result

            if not best_result:
                return None

            # Don't accept completely unrelated pages
            if best_score < 0.40:

                print(
                    f"   ⚠️ Weak match rejected: "
                    f"{best_result.get('title')}"
                )

                return None

            title = best_result["title"]

            url = (
                WIKI_BASE
                + "/wiki/"
                + quote(
                    title.replace(" ", "_"),
                    safe="()_,.'-"
                )
            )

            return {
                "url": url,
                "title": title,
                "score": best_score
            }

        except requests.exceptions.RequestException as e:

            if attempt == retries - 1:

                print(
                    f"   ❌ Search failed: {e}"
                )

                return None

            wait = 5 * (2 ** attempt)

            print(
                f"   🔄 Retry in {wait}s..."
            )

            time.sleep(wait)

        except Exception as e:

            print(
                f"   ❌ Unexpected search error: {e}"
            )

            return None

    return None


# ============================================================
# SCRAPE WIKIPEDIA PAGE
# ============================================================

def scrape_page(url):
    """
    Extract useful readable text from Wikipedia.
    """

    response = session.get(
        url,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Remove unnecessary elements
    for tag in soup([
        "script",
        "style",
        "noscript",
        "table",
        "sup",
        "nav",
        "footer",
        "header"
    ]):

        tag.decompose()

    paragraphs = soup.find_all("p")

    texts = []

    for p in paragraphs:

        text = p.get_text(
            " ",
            strip=True
        )

        if text:

            texts.append(text)

    return " ".join(texts).strip()


# ============================================================
# LOAD PREVIOUS RESULTS
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

    except Exception as e:

        print(
            f"⚠️ Could not load previous results: {e}"
        )

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
            "landmark_id"
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
    print("🧠 SMART WIKIPEDIA SCRAPER")
    print("=" * 70)

    # --------------------------------------------------------
    # Load landmarks
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        print(
            "\n❌ data/landmarks.csv not found!"
        )

        return

    landmarks = pd.read_csv(
        INPUT_FILE
    ).fillna("")

    print(
        f"\n📊 Total landmarks: {len(landmarks)}"
    )

    # --------------------------------------------------------
    # Load previous progress
    # --------------------------------------------------------

    results = load_existing()

    print(
        f"♻️ Existing records: {len(results)}"
    )

    # --------------------------------------------------------
    # Process landmarks
    # --------------------------------------------------------

    for index, row in landmarks.iterrows():

        landmark_name = row[
            "landmark_name"
        ]

        print("\n" + "-" * 70)

        print(
            f"🔎 [{index + 1}/{len(landmarks)}] "
            f"{landmark_name}"
        )

        # ----------------------------------------------------
        # Existing successful result
        # ----------------------------------------------------

        if landmark_name in results:

            old = results[
                landmark_name
            ]

            old_text = str(
                old.get(
                    "scraped_text",
                    ""
                )
            )

            old_status = str(
                old.get(
                    "status",
                    ""
                )
            )

            # Keep good existing data
            if (
                old_status == "success"
                and len(old_text) >= 500
            ):

                print(
                    "   ⏭️ Good data already exists."
                )

                continue

            print(
                "   🔄 Existing result is weak. "
                "Trying again..."
            )

        # ----------------------------------------------------
        # Step 1: Direct page
        # ----------------------------------------------------

        page = get_direct_page(
            landmark_name
        )

        if page:

            print(
                f"   🎯 Direct page found:"
            )

            print(
                f"   🔗 {page['url']}"
            )

            print(
                f"   📌 Title: {page['title']}"
            )

            print(
                f"   🎯 Similarity: "
                f"{page['score']:.2f}"
            )

        else:

            # ------------------------------------------------
            # Step 2: Search API fallback
            # ------------------------------------------------

            print(
                "   🔍 Direct page not found."
            )

            print(
                "   🔎 Trying Wikipedia search..."
            )

            page = search_wikipedia(
                landmark_name
            )

        # ----------------------------------------------------
        # No page
        # ----------------------------------------------------

        if not page:

            print(
                "   ⚠️ No reliable Wikipedia page found."
            )

            results[landmark_name] = {

                "landmark_id":
                    row["landmark_id"],

                "landmark_name":
                    landmark_name,

                "folder_name":
                    row["folder_name"],

                "image_count":
                    row["image_count"],

                "source_url":
                    "",

                "wiki_title":
                    "",

                "match_score":
                    0,

                "scraped_text":
                    "",

                "text_length":
                    0,

                "status":
                    "not_found"
            }

            save_results(results)

            time.sleep(
                random.uniform(
                    MIN_DELAY,
                    MAX_DELAY
                )
            )

            continue

        # ----------------------------------------------------
        # Step 3: Scrape
        # ----------------------------------------------------

        try:

            print(
                "   📝 Extracting page text..."
            )

            text = scrape_page(
                page["url"]
            )

            text_length = len(text)

            print(
                f"   📄 Characters: "
                f"{text_length}"
            )

            # ------------------------------------------------
            # Quality check
            # ------------------------------------------------

            if text_length >= 500:

                status = "success"

            elif text_length > 100:

                status = "short_text"

            else:

                status = "invalid"

            results[landmark_name] = {

                "landmark_id":
                    row["landmark_id"],

                "landmark_name":
                    landmark_name,

                "folder_name":
                    row["folder_name"],

                "image_count":
                    row["image_count"],

                "source_url":
                    page["url"],

                "wiki_title":
                    page["title"],

                "match_score":
                    round(
                        page["score"],
                        3
                    ),

                "scraped_text":
                    text,

                "text_length":
                    text_length,

                "status":
                    status
            }

            print(
                f"   ✅ Status: {status}"
            )

        except Exception as e:

            print(
                f"   ❌ Scraping error: {e}"
            )

            results[landmark_name] = {

                "landmark_id":
                    row["landmark_id"],

                "landmark_name":
                    landmark_name,

                "folder_name":
                    row["folder_name"],

                "image_count":
                    row["image_count"],

                "source_url":
                    page["url"],

                "wiki_title":
                    page["title"],

                "match_score":
                    round(
                        page["score"],
                        3
                    ),

                "scraped_text":
                    "",

                "text_length":
                    0,

                "status":
                    "error"
            }

        # ----------------------------------------------------
        # Save after every landmark
        # ----------------------------------------------------

        save_results(results)

        print(
            "   💾 Progress saved."
        )

        # ----------------------------------------------------
        # Random delay
        # ----------------------------------------------------

        delay = random.uniform(
            MIN_DELAY,
            MAX_DELAY
        )

        time.sleep(delay)

    # ========================================================
    # FINAL REPORT
    # ========================================================

    save_results(results)

    df = pd.DataFrame(
        list(results.values())
    )

    print("\n" + "=" * 70)
    print("🎉 SCRAPING FINISHED")
    print("=" * 70)

    print(
        f"\n📄 Output:"
    )

    print(
        OUTPUT_FILE.resolve()
    )

    print(
        "\n📊 Status:"
    )

    print(
        df["status"]
        .value_counts()
        .to_string()
    )

    print(
        f"\n🏛️ Total records: {len(df)}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()