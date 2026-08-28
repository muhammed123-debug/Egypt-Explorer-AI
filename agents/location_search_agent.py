# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# 🌍 MULTI-SOURCE LOCATION SEARCH AGENT
# ============================================================

from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIG
# ============================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

WIKIPEDIA_API = (
    "https://en.wikipedia.org/w/api.php"
)

HEADERS = {
    "User-Agent": (
        "EgyptExplorerAI/1.0 "
        "(Educational Tourism RAG Project)"
    )
}

TIMEOUT = 20

MIN_CONFIDENCE = 0.70


# ============================================================
# RESULT
# ============================================================

@dataclass
class LocationSearchResult:

    landmark_name: str

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    display_name: str = ""

    city: str = ""

    governorate: str = ""

    country: str = ""

    source: str = ""

    source_url: str = ""

    confidence: float = 0.0

    status: str = "not_found"

    query_used: str = ""


# ============================================================
# AGENT
# ============================================================

class LocationSearchAgent:

    def __init__(
        self,
        min_confidence: float = MIN_CONFIDENCE
    ):

        self.min_confidence = (
            min_confidence
        )

        self.session = requests.Session()

        self.session.headers.update(
            HEADERS
        )


    # ========================================================
    # NORMALIZE
    # ========================================================

    @staticmethod
    def normalize(
        text: str
    ) -> str:

        if not text:
            return ""

        text = str(text).lower()

        text = (
            text
            .replace("_", " ")
            .replace("-", " ")
        )

        text = re.sub(
            r"[^\w\s]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    # ========================================================
    # TOKENS
    # ========================================================

    @classmethod
    def tokens(
        cls,
        text: str
    ):

        normalized = cls.normalize(
            text
        )

        return set(
            normalized.split()
        )


    # ========================================================
    # NAME SIMILARITY
    # ========================================================

    @classmethod
    def similarity(
        cls,
        landmark_name: str,
        candidate_name: str
    ) -> float:

        target = cls.tokens(
            landmark_name
        )

        candidate = cls.tokens(
            candidate_name
        )

        if not target or not candidate:

            return 0.0

        common = (
            target & candidate
        )

        overlap = (
            len(common)
            / len(target)
        )

        # Full containment.
        target_text = cls.normalize(
            landmark_name
        )

        candidate_text = cls.normalize(
            candidate_name
        )

        if (
            target_text in candidate_text
            or candidate_text in target_text
        ):

            overlap = max(
                overlap,
                0.85
            )

        return round(
            min(overlap, 1.0),
            3
        )


    # ========================================================
    # QUERY GENERATION
    # ========================================================

    @staticmethod
    def build_queries(
        landmark_name: str,
        city: str = "",
        governorate: str = ""
    ):

        queries = []

        name = landmark_name.strip()

        if city:

            queries.append(
                f"{name} {city} Egypt"
            )

        if governorate:

            queries.append(
                f"{name} {governorate} Egypt"
            )

        queries.extend(
            [
                f"{name} Egypt",
                f"{name} coordinates Egypt",
                f"{name} location Egypt",
                f"{name} map Egypt",
            ]
        )

        unique = []

        for query in queries:

            if query not in unique:

                unique.append(
                    query
                )

        return unique


    # ========================================================
    # NOMINATIM SEARCH
    # ========================================================

    def search_nominatim(
        self,
        query: str,
        limit: int = 5
    ):

        params = {

            "q":
                query,

            "format":
                "jsonv2",

            "addressdetails":
                1,

            "limit":
                limit,

            "countrycodes":
                "eg",

            "accept-language":
                "en"
        }

        try:

            response = self.session.get(
                NOMINATIM_URL,
                params=params,
                timeout=TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except Exception as exc:

            print(
                f"   ⚠️ Nominatim error:"
                f" {exc}"
            )

            return []


    # ========================================================
    # WIKIPEDIA SEARCH
    # ========================================================

    def search_wikipedia(
        self,
        landmark_name: str
    ):

        params = {

            "action":
                "query",

            "list":
                "search",

            "srsearch":
                f"{landmark_name} Egypt",

            "format":
                "json",

            "utf8":
                1,

            "srlimit":
                5
        }

        try:

            response = self.session.get(
                WIKIPEDIA_API,
                params=params,
                timeout=TIMEOUT
            )

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

            return results

        except Exception as exc:

            print(
                f"   ⚠️ Wikipedia error:"
                f" {exc}"
            )

            return []


    # ========================================================
    # WIKIPEDIA PAGE COORDINATES
    # ========================================================

    def get_wikipedia_coordinates(
        self,
        title: str
    ):

        params = {

            "action":
                "query",

            "prop":
                "coordinates",

            "titles":
                title,

            "format":
                "json",

            "coprimary":
                1
        }

        try:

            response = self.session.get(
                WIKIPEDIA_API,
                params=params,
                timeout=TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            pages = (
                data
                .get(
                    "query",
                    {}
                )
                .get(
                    "pages",
                    {}
                )
            )

            for page in pages.values():

                coordinates = page.get(
                    "coordinates"
                )

                if coordinates:

                    coordinate = (
                        coordinates[0]
                    )

                    return {
                        "lat":
                            coordinate.get(
                                "lat"
                            ),

                        "lon":
                            coordinate.get(
                                "lon"
                            )
                    }

        except Exception as exc:

            print(
                f"   ⚠️ Wikipedia "
                f"coordinates error:"
                f" {exc}"
            )

        return None


    # ========================================================
    # SCORE NOMINATIM RESULT
    # ========================================================

    def score_nominatim(
        self,
        landmark_name: str,
        candidate: dict,
        city: str = "",
        governorate: str = ""
    ):

        candidate_name = candidate.get(
            "name",
            ""
        )

        display_name = candidate.get(
            "display_name",
            ""
        )

        address = candidate.get(
            "address",
            {}
        )

        name_score = max(

            self.similarity(
                landmark_name,
                candidate_name
            ),

            self.similarity(
                landmark_name,
                display_name
            )
        )

        score = (
            0.80 * name_score
        )


        candidate_city = (
            address.get(
                "city"
            )
            or address.get(
                "town"
            )
            or address.get(
                "village"
            )
            or address.get(
                "municipality"
            )
            or ""
        )

        candidate_state = (
            address.get(
                "state"
            )
            or address.get(
                "state_district"
            )
            or ""
        )


        if city and (
            self.normalize(city)
            in self.normalize(
                display_name
            )
        ):

            score += 0.10


        if governorate and (
            self.normalize(
                governorate
            )
            in self.normalize(
                candidate_state
            )
        ):

            score += 0.10


        return round(
            min(score, 1.0),
            3
        )


    # ========================================================
    # SEARCH WEB-LIKE SOURCES
    # ========================================================

    def search_web_sources(
        self,
        landmark_name: str
    ):

        """
        Search Wikipedia and use its article
        coordinates when available.

        This gives us a second independent
        source when Nominatim fails.
        """

        results = self.search_wikipedia(
            landmark_name
        )

        candidates = []

        for result in results:

            title = result.get(
                "title",
                ""
            )

            if not title:
                continue

            score = self.similarity(
                landmark_name,
                title
            )

            if score < 0.50:
                continue

            coordinates = (
                self.get_wikipedia_coordinates(
                    title
                )
            )

            if not coordinates:
                continue

            candidates.append(
                {
                    "title":
                        title,

                    "score":
                        score,

                    "coordinates":
                        coordinates
                }
            )

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return candidates


    # ========================================================
    # MAIN FIND LOCATION
    # ========================================================

    def find_location(
        self,
        landmark_name: str,
        city: str = "",
        governorate: str = ""
    ) -> LocationSearchResult:

        print(
            f"\n🌍 Location Search Agent:"
            f" {landmark_name}"
        )


        queries = self.build_queries(
            landmark_name,
            city,
            governorate
        )


        candidates = []


        # ====================================================
        # SOURCE 1 — NOMINATIM
        # ====================================================

        for query in queries:

            print(
                f"   🔎 OSM:"
                f" {query}"
            )

            results = (
                self.search_nominatim(
                    query
                )
            )

            for candidate in results:

                score = (
                    self.score_nominatim(
                        landmark_name,
                        candidate,
                        city,
                        governorate
                    )
                )

                candidates.append(
                    {
                        "source":
                            "OpenStreetMap",

                        "score":
                            score,

                        "candidate":
                            candidate,

                        "query":
                            query
                    }
                )

            time.sleep(
                1
            )


        # ====================================================
        # SORT OSM CANDIDATES
        # ====================================================

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        if candidates:

            best = candidates[0]

            if (
                best["score"]
                >= self.min_confidence
            ):

                candidate = best[
                    "candidate"
                ]

                address = candidate.get(
                    "address",
                    {}
                )

                city_result = (
                    address.get(
                        "city"
                    )
                    or address.get(
                        "town"
                    )
                    or address.get(
                        "village"
                    )
                    or address.get(
                        "municipality"
                    )
                    or ""
                )

                governorate_result = (
                    address.get(
                        "state"
                    )
                    or address.get(
                        "state_district"
                    )
                    or ""
                )

                country = address.get(
                    "country",
                    ""
                )

                print(
                    "   ✅ OSM location found"
                )

                print(
                    f"   🎯 Confidence:"
                    f" {best['score']:.3f}"
                )

                return LocationSearchResult(

                    landmark_name=
                        landmark_name,

                    latitude=
                        float(
                            candidate["lat"]
                        ),

                    longitude=
                        float(
                            candidate["lon"]
                        ),

                    display_name=
                        candidate.get(
                            "display_name",
                            ""
                        ),

                    city=
                        city_result,

                    governorate=
                        governorate_result,

                    country=
                        country,

                    source=
                        "OpenStreetMap",

                    source_url=
                        NOMINATIM_URL,

                    confidence=
                        best["score"],

                    status=
                        "success",

                    query_used=
                        best["query"]
                )


        # ====================================================
        # SOURCE 2 — WIKIPEDIA
        # ====================================================

        print(
            "   🔄 OSM failed."
        )

        print(
            "   🔎 Trying Wikipedia..."
        )


        wiki_candidates = (
            self.search_web_sources(
                landmark_name
            )
        )


        if wiki_candidates:

            best = wiki_candidates[0]

            confidence = best[
                "score"
            ]


            if (
                confidence
                >= self.min_confidence
            ):

                coordinates = (
                    best["coordinates"]
                )

                title = best[
                    "title"
                ]

                wiki_url = (
                    "https://en.wikipedia.org/wiki/"
                    + quote(
                        title.replace(
                            " ",
                            "_"
                        )
                    )
                )


                print(
                    "   ✅ Wikipedia "
                    "location found"
                )

                print(
                    f"   📌 {title}"
                )

                print(
                    f"   🎯 Confidence:"
                    f" {confidence:.3f}"
                )


                return LocationSearchResult(

                    landmark_name=
                        landmark_name,

                    latitude=
                        float(
                            coordinates["lat"]
                        ),

                    longitude=
                        float(
                            coordinates["lon"]
                        ),

                    display_name=
                        title
                        + ", Egypt",

                    city=
                        city,

                    governorate=
                        governorate,

                    country=
                        "Egypt",

                    source=
                        "Wikipedia",

                    source_url=
                        wiki_url,

                    confidence=
                        confidence,

                    status=
                        "success",

                    query_used=
                        title
                )


        # ====================================================
        # NOTHING FOUND
        # ====================================================

        print(
            "   ❌ No reliable location found."
        )


        return LocationSearchResult(

            landmark_name=
                landmark_name,

            source=
                "",

            confidence=
                0.0,

            status=
                "not_found"
        )


# ============================================================
# HELPER
# ============================================================

def find_location(
    landmark_name: str,
    city: str = "",
    governorate: str = ""
):

    agent = LocationSearchAgent()

    result = agent.find_location(
        landmark_name,
        city,
        governorate
    )

    return asdict(
        result
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_places = [

        "Great Sphinx of Giza",

        "Pyramid of Khafra",

        "Nubia Museum, Aswan",

        "Temple of Isis in Philae"
    ]


    agent = LocationSearchAgent()


    for place in test_places:

        result = agent.find_location(
            place
        )

        print(
            "\n" + "=" * 70
        )

        print(
            result
        )