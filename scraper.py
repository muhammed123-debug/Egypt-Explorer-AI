from pathlib import Path
import time
import random
import re
import requests
import pandas as pd

from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from urllib.parse import quote


# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# SMART + SAFE WIKIPEDIA SCRAPER
# ============================================================

INPUT_FILE = Path("data/landmarks.csv")
OUTPUT_FILE = Path("data/scraped_landmarks.csv")

WIKI_BASE = "https://en.wikipedia.org"

HEADERS = {
    "User-Agent": (
        "EgyptExplorerAI/1.0 "
        "(Educational Tourism RAG Project)"
    )
}

TIMEOUT = 20

MIN_DELAY = 2
MAX_DELAY = 4

# ============================================================
# MATCHING THRESHOLDS
# ============================================================

# Direct page must have a strong title match.
DIRECT_MATCH_THRESHOLD = 0.75

# Search result must have a strong match.
SEARCH_MATCH_THRESHOLD = 0.70

# Exact / near-exact matches are preferred.
STRONG_MATCH_THRESHOLD = 0.90


# ============================================================
# SESSION
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text):

    if text is None:
        return ""

    text = str(text).lower()

    text = (
        text
        .replace("_", " ")
        .replace("-", " ")
    )

    # Remove punctuation.
    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    # Normalize spaces.
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TOKENIZATION
# ============================================================

def tokens(text):

    normalized = normalize(text)

    if not normalized:
        return set()

    return set(
        normalized.split()
    )


# ============================================================
# SIMILARITY
# ============================================================

def similarity(a, b):

    a_norm = normalize(a)
    b_norm = normalize(b)

    if not a_norm or not b_norm:
        return 0.0

    # Exact match.
    if a_norm == b_norm:
        return 1.0

    sequence_score = SequenceMatcher(
        None,
        a_norm,
        b_norm
    ).ratio()

    a_tokens = tokens(a)
    b_tokens = tokens(b)

    if a_tokens and b_tokens:

        intersection = (
            a_tokens & b_tokens
        )

        union = (
            a_tokens | b_tokens
        )

        jaccard_score = (
            len(intersection)
            / len(union)
        )

    else:

        jaccard_score = 0.0

    # Weighted score.
    score = (
        0.65 * sequence_score
        + 0.35 * jaccard_score
    )

    return round(
        score,
        4
    )


# ============================================================
# LANDMARK-SPECIFIC KEYWORDS
# ============================================================

GENERIC_WORDS = {
    "the",
    "of",
    "in",
    "and",
    "el",
    "al",
    "a",
    "an",
}


def meaningful_tokens(text):

    return {
        token
        for token in tokens(text)
        if token not in GENERIC_WORDS
        and len(token) > 2
    }


# ============================================================
# TITLE VALIDATION
# ============================================================

def title_is_relevant(
    landmark_name,
    wiki_title,
    score
):

    landmark_tokens = (
        meaningful_tokens(
            landmark_name
        )
    )

    wiki_tokens = (
        meaningful_tokens(
            wiki_title
        )
    )

    if not landmark_tokens:
        return score >= DIRECT_MATCH_THRESHOLD

    # --------------------------------------------------------
    # Exact normalized match
    # --------------------------------------------------------

    if normalize(
        landmark_name
    ) == normalize(
        wiki_title
    ):

        return True

    # --------------------------------------------------------
    # Strong similarity
    # --------------------------------------------------------

    if score >= STRONG_MATCH_THRESHOLD:

        return True

    # --------------------------------------------------------
    # Token overlap
    # --------------------------------------------------------

    common = (
        landmark_tokens
        & wiki_tokens
    )

    overlap = (
        len(common)
        / max(
            len(landmark_tokens),
            1
        )
    )

    # At least half of meaningful landmark
    # tokens should appear in the title.
    if overlap >= 0.50 and score >= 0.65:

        return True

    return False


# ============================================================
# DIRECT WIKIPEDIA PAGE
# ============================================================

def get_direct_page(
    landmark_name
):

    """
    Try the obvious Wikipedia URL first.

    IMPORTANT:
    A successful HTTP request is NOT enough.
    The final Wikipedia title must match the landmark.
    """

    title = landmark_name.replace(
        " ",
        "_"
    )

    url = (
        WIKI_BASE
        + "/wiki/"
        + quote(
            title,
            safe="()_,.'-"
        )
    )

    try:

        response = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        if response.status_code != 200:

            return None

        final_url = response.url

        if "/wiki/" not in final_url:

            return None

        final_title = (
            final_url
            .split("/wiki/")[-1]
            .replace("_", " ")
        )

        final_title = final_title.strip()

        score = similarity(
            landmark_name,
            final_title
        )

        # ----------------------------------------------------
        # Validate redirected title.
        # ----------------------------------------------------

        if not title_is_relevant(
            landmark_name,
            final_title,
            score
        ):

            print(
                f"   ⚠️ Direct page rejected:"
            )

            print(
                f"      Requested: {landmark_name}"
            )

            print(
                f"      Got: {final_title}"
            )

            print(
                f"      Score: {score:.3f}"
            )

            return None

        return {

            "url":
                final_url,

            "title":
                final_title,

            "score":
                score
        }

    except Exception as e:

        print(
            f"   ⚠️ Direct lookup error: {e}"
        )

        return None


# ============================================================
# WIKIPEDIA SEARCH
# ============================================================

def search_wikipedia(
    landmark_name,
    retries=4
):

    """
    Search Wikipedia when direct lookup fails.

    Returns only strongly relevant pages.
    """

    api_url = (
        f"{WIKI_BASE}/w/api.php"
    )

    params = {

        "action":
            "query",

        "list":
            "search",

        "srsearch":
            landmark_name,

        "format":
            "json",

        "utf8":
            1,

        "srlimit":
            5
    }

    for attempt in range(
        retries
    ):

        try:

            response = session.get(
                api_url,
                params=params,
                timeout=TIMEOUT
            )

            # ------------------------------------------------
            # Rate limit
            # ------------------------------------------------

            if response.status_code == 429:

                wait = (
                    10
                    * (2 ** attempt)
                )

                print(
                    f"   ⏳ Wikipedia rate limit."
                    f" Waiting {wait}s..."
                )

                time.sleep(
                    wait
                )

                continue

            response.raise_for_status()

            data = response.json()

            results = (
                data
                .get(
                    "query",
                    {}
                )
                .get(
                    "search",
                    []
                )
            )

            if not results:

                return None

            # ------------------------------------------------
            # Rank candidates
            # ------------------------------------------------

            candidates = []

            for result in results:

                title = result.get(
                    "title",
                    ""
                )

                score = similarity(
                    landmark_name,
                    title
                )

                candidates.append(
                    {
                        "title":
                            title,

                        "score":
                            score
                    }
                )

            candidates.sort(
                key=lambda x: x["score"],
                reverse=True
            )

            # ------------------------------------------------
            # Try candidates
            # ------------------------------------------------

            for candidate in candidates:

                title = candidate[
                    "title"
                ]

                score = candidate[
                    "score"
                ]

                print(
                    f"   🔎 Candidate:"
                    f" {title}"
                    f" ({score:.3f})"
                )

                if not title_is_relevant(
                    landmark_name,
                    title,
                    score
                ):

                    continue

                url = (
                    WIKI_BASE
                    + "/wiki/"
                    + quote(
                        title.replace(
                            " ",
                            "_"
                        ),
                        safe="()_,.'-"
                    )
                )

                return {

                    "url":
                        url,

                    "title":
                        title,

                    "score":
                        score
                }

            # ------------------------------------------------
            # Nothing reliable
            # ------------------------------------------------

            print(
                "   ⚠️ No reliable Wikipedia "
                "match found."
            )

            return None

        except requests.exceptions.RequestException as e:

            if attempt == retries - 1:

                print(
                    f"   ❌ Search failed: {e}"
                )

                return None

            wait = (
                5
                * (2 ** attempt)
            )

            print(
                f"   🔄 Retry in {wait}s..."
            )

            time.sleep(
                wait
            )

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
    Extract readable paragraph text.
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

    # --------------------------------------------------------
    # Remove unnecessary elements
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Extract paragraphs
    # --------------------------------------------------------

    paragraphs = (
        soup.find_all("p")
    )

    texts = []

    for p in paragraphs:

        text = p.get_text(
            " ",
            strip=True
        )

        if text:

            texts.append(
                text
            )

    return " ".join(
        texts
    ).strip()


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
            f"⚠️ Could not load previous "
            f"results: {e}"
        )

        return {}


# ============================================================
# SAVE
# ============================================================

def save_results(
    results
):

    df = pd.DataFrame(
        list(
            results.values()
        )
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
# VALIDATE EXISTING RESULT
# ============================================================

def existing_result_is_good(
    row
):

    status = str(
        row.get(
            "status",
            ""
        )
    )

    text = str(
        row.get(
            "scraped_text",
            ""
        )
    )

    title = str(
        row.get(
            "wiki_title",
            ""
        )
    )

    landmark = str(
        row.get(
            "landmark_name",
            ""
        )
    )

    try:

        score = float(
            row.get(
                "match_score",
                0
            )
        )

    except Exception:

        score = 0.0

    # --------------------------------------------------------
    # Must have useful text.
    # --------------------------------------------------------

    if status not in [
        "success",
        "short_text"
    ]:

        return False

    if len(text.strip()) < 500:

        return False

    # --------------------------------------------------------
    # Must have a title.
    # --------------------------------------------------------

    if not title:

        return False

    # --------------------------------------------------------
    # Revalidate old title.
    # --------------------------------------------------------

    if not title_is_relevant(
        landmark,
        title,
        score
    ):

        print(
            "   ⚠️ Existing result "
            "failed title validation."
        )

        print(
            f"      Landmark: {landmark}"
        )

        print(
            f"      Wiki title: {title}"
        )

        print(
            f"      Score: {score:.3f}"
        )

        return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "🇪🇬 EGYPT EXPLORER AI"
    )

    print(
        "🧠 SMART + SAFE WIKIPEDIA SCRAPER"
    )

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
        f"\n📊 Total landmarks:"
        f" {len(landmarks)}"
    )

    # --------------------------------------------------------
    # Existing progress
    # --------------------------------------------------------

    results = load_existing()

    print(
        f"♻️ Existing records:"
        f" {len(results)}"
    )

    # --------------------------------------------------------
    # Process landmarks
    # --------------------------------------------------------

    for index, row in landmarks.iterrows():

        landmark_name = row[
            "landmark_name"
        ]

        print(
            "\n"
            + "-" * 70
        )

        print(
            f"🔎 [{index + 1}/"
            f"{len(landmarks)}]"
            f" {landmark_name}"
        )

        # ====================================================
        # Existing result validation
        # ====================================================

        if landmark_name in results:

            old = results[
                landmark_name
            ]

            if existing_result_is_good(
                old
            ):

                print(
                    "   ⏭️ Existing data "
                    "passed validation."
                )

                continue

            print(
                "   🔄 Existing result "
                "needs re-scraping."
            )

        # ====================================================
        # Direct page
        # ====================================================

        page = get_direct_page(
            landmark_name
        )

        if page:

            print(
                "   🎯 Reliable direct page:"
            )

            print(
                f"   🔗 {page['url']}"
            )

            print(
                f"   📌 Title:"
                f" {page['title']}"
            )

            print(
                f"   🎯 Similarity:"
                f" {page['score']:.3f}"
            )

        else:

            # =================================================
            # Search API fallback
            # =================================================

            print(
                "   🔍 Direct page rejected/not found."
            )

            print(
                "   🔎 Searching Wikipedia..."
            )

            page = search_wikipedia(
                landmark_name
            )

        # ====================================================
        # No reliable page
        # ====================================================

        if not page:

            print(
                "   ⚠️ No reliable Wikipedia "
                "page found."
            )

            results[
                landmark_name
            ] = {

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

            save_results(
                results
            )

            time.sleep(
                random.uniform(
                    MIN_DELAY,
                    MAX_DELAY
                )
            )

            continue

        # ====================================================
        # Scrape page
        # ====================================================

        try:

            print(
                "   📝 Extracting page text..."
            )

            text = scrape_page(
                page["url"]
            )

            text_length = len(
                text
            )

            print(
                f"   📄 Characters:"
                f" {text_length}"
            )

            # ------------------------------------------------
            # Quality
            # ------------------------------------------------

            if text_length >= 500:

                status = "success"

            elif text_length > 100:

                status = "short_text"

            else:

                status = "invalid"

            # ------------------------------------------------
            # Save
            # ------------------------------------------------

            results[
                landmark_name
            ] = {

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
                f"   ✅ Status:"
                f" {status}"
            )

        except Exception as e:

            print(
                f"   ❌ Scraping error:"
                f" {e}"
            )

            results[
                landmark_name
            ] = {

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

        # ====================================================
        # Save progress
        # ====================================================

        save_results(
            results
        )

        print(
            "   💾 Progress saved."
        )

        # ====================================================
        # Delay
        # ====================================================

        delay = random.uniform(
            MIN_DELAY,
            MAX_DELAY
        )

        time.sleep(
            delay
        )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    save_results(
        results
    )

    df = pd.DataFrame(
        list(
            results.values()
        )
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "🎉 SCRAPING + VALIDATION FINISHED"
    )

    print(
        "=" * 70
    )

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
        f"\n🏛️ Total records:"
        f" {len(df)}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()