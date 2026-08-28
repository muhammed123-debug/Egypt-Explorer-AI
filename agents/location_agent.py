# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# 📍 LOCATION AGENT
# ============================================================

from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from typing import Optional

import requests


# ============================================================
# CONFIGURATION
# ============================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

HEADERS = {
    "User-Agent": (
        "EgyptExplorerAI/1.0 "
        "(Educational Tourism RAG Project)"
    )
}

REQUEST_TIMEOUT = 20

MIN_CONFIDENCE = 0.60


# ============================================================
# RESULT
# ============================================================

@dataclass
class LocationResult:

    landmark_name: str

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    display_name: str = ""

    city: str = ""

    governorate: str = ""

    country: str = ""

    osm_type: str = ""

    source: str = ""

    confidence: float = 0.0

    status: str = "not_found"

    query_used: str = ""


# ============================================================
# LOCATION AGENT
# ============================================================

class LocationAgent:
    """
    Intelligent location discovery agent.

    It searches OpenStreetMap/Nominatim using
    multiple query strategies and validates
    the returned candidates before accepting one.
    """

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
    # TEXT NORMALIZATION
    # ========================================================

    @staticmethod
    def normalize(text: str) -> str:

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
    # TOKENIZATION
    # ========================================================

    @classmethod
    def tokens(
        cls,
        text: str
    ):

        normalized = cls.normalize(
            text
        )

        if not normalized:
            return set()

        return set(
            normalized.split()
        )


    # ========================================================
    # SIMILARITY
    # ========================================================

    @classmethod
    def similarity(
        cls,
        landmark_name: str,
        candidate_name: str
    ) -> float:

        target = cls.normalize(
            landmark_name
        )

        candidate = cls.normalize(
            candidate_name
        )

        if not target or not candidate:

            return 0.0

        if target == candidate:

            return 1.0

        target_tokens = cls.tokens(
            target
        )

        candidate_tokens = cls.tokens(
            candidate
        )

        if not target_tokens:

            return 0.0

        common = (
            target_tokens
            & candidate_tokens
        )

        overlap = (
            len(common)
            / len(target_tokens)
        )

        # Containment bonus.
        if (
            target in candidate
            or candidate in target
        ):

            overlap = max(
                overlap,
                0.80
            )

        return round(
            min(overlap, 1.0),
            3
        )


    # ========================================================
    # BUILD QUERIES
    # ========================================================

    @staticmethod
    def build_queries(
        landmark_name: str,
        city: str = "",
        governorate: str = ""
    ):

        queries = []

        landmark_name = (
            landmark_name.strip()
        )

        city = (
            city.strip()
            if city
            else ""
        )

        governorate = (
            governorate.strip()
            if governorate
            else ""
        )


        # ----------------------------------------------------
        # Most specific
        # ----------------------------------------------------

        if city:

            queries.append(
                f"{landmark_name}, "
                f"{city}, Egypt"
            )


        if governorate:

            queries.append(
                f"{landmark_name}, "
                f"{governorate}, Egypt"
            )


        # ----------------------------------------------------
        # Egypt fallback
        # ----------------------------------------------------

        queries.append(
            f"{landmark_name}, Egypt"
        )


        # ----------------------------------------------------
        # Raw name
        # ----------------------------------------------------

        queries.append(
            landmark_name
        )


        # Remove duplicates.
        unique = []

        for query in queries:

            if query not in unique:

                unique.append(
                    query
                )

        return unique


    # ========================================================
    # SEARCH NOMINATIM
    # ========================================================

    def search(
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
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except Exception as exc:

            print(
                f"⚠️ Location search failed:"
                f" {exc}"
            )

            return []


    # ========================================================
    # SCORE CANDIDATE
    # ========================================================

    def score_candidate(
        self,
        landmark_name: str,
        candidate: dict,
        city: str = "",
        governorate: str = ""
    ):

        display_name = candidate.get(
            "display_name",
            ""
        )

        candidate_name = candidate.get(
            "name",
            ""
        )

        candidate_type = candidate.get(
            "type",
            ""
        )

        candidate_class = candidate.get(
            "class",
            ""
        )

        address = candidate.get(
            "address",
            {}
        )


        # ----------------------------------------------------
        # Name score
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # Location bonus
        # ----------------------------------------------------

        location_bonus = 0.0

        candidate_city = (
            address.get(
                "city",
                ""
            )
            or address.get(
                "town",
                ""
            )
            or address.get(
                "municipality",
                ""
            )
            or address.get(
                "village",
                ""
            )
        )

        candidate_state = (
            address.get(
                "state",
                ""
            )
            or address.get(
                "state_district",
                ""
            )
        )


        if city:

            if self.normalize(city) in (
                self.normalize(
                    candidate_city
                )
                + " "
                + self.normalize(
                    display_name
                )
            ):

                location_bonus += 0.15


        if governorate:

            if self.normalize(
                governorate
            ) in self.normalize(
                candidate_state
            ):

                location_bonus += 0.10


        # ----------------------------------------------------
        # Tourism POI bonus
        # ----------------------------------------------------

        poi_bonus = 0.0

        tourism_types = {

            "tourism",
            "historic",
            "attraction",
            "museum",
            "archaeological_site",
            "monument",
            "castle",
            "palace",
            "place_of_worship",
            "beach",
            "park"
        }


        if (
            candidate_class
            in tourism_types
        ):

            poi_bonus = 0.10


        if (
            candidate_type
            in tourism_types
        ):

            poi_bonus = max(
                poi_bonus,
                0.10
            )


        # ----------------------------------------------------
        # Final score
        # ----------------------------------------------------

        score = (
            0.75 * name_score
            + location_bonus
            + poi_bonus
        )


        return round(
            min(score, 1.0),
            3
        )


    # ========================================================
    # EXTRACT ADDRESS
    # ========================================================

    @staticmethod
    def extract_address(
        candidate: dict
    ):

        address = candidate.get(
            "address",
            {}
        )

        city = (
            address.get(
                "city"
            )
            or address.get(
                "town"
            )
            or address.get(
                "municipality"
            )
            or address.get(
                "village"
            )
            or ""
        )

        governorate = (
            address.get(
                "state"
            )
            or address.get(
                "state_district"
            )
            or ""
        )

        country = (
            address.get(
                "country",
                ""
            )
        )

        return (
            city,
            governorate,
            country
        )


    # ========================================================
    # FIND LOCATION
    # ========================================================

    def find_location(
        self,
        landmark_name: str,
        city: str = "",
        governorate: str = ""
    ) -> LocationResult:

        print(
            f"\n📍 Location Agent:"
            f" {landmark_name}"
        )


        queries = self.build_queries(
            landmark_name,
            city,
            governorate
        )


        candidates = []


        # ====================================================
        # SEARCH ALL QUERY STRATEGIES
        # ====================================================

        for query in queries:

            print(
                f"   🔎 Query:"
                f" {query}"
            )

            results = self.search(
                query
            )


            for candidate in results:

                score = (
                    self.score_candidate(
                        landmark_name,
                        candidate,
                        city,
                        governorate
                    )
                )

                candidates.append(
                    {
                        "candidate":
                            candidate,

                        "score":
                            score,

                        "query":
                            query
                    }
                )


            # Respect Nominatim usage.
            time.sleep(
                1
            )


        # ====================================================
        # NO RESULTS
        # ====================================================

        if not candidates:

            print(
                "   ❌ No location found."
            )

            return LocationResult(
                landmark_name=landmark_name
            )


        # ====================================================
        # SORT
        # ====================================================

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        best = candidates[0]

        candidate = best[
            "candidate"
        ]

        confidence = best[
            "score"
        ]

        query_used = best[
            "query"
        ]


        # ====================================================
        # VALIDATE
        # ====================================================

        if confidence < self.min_confidence:

            print(
                f"   ⚠️ Low confidence:"
                f" {confidence:.3f}"
            )

            return LocationResult(

                landmark_name=
                    landmark_name,

                confidence=
                    confidence,

                status=
                    "low_confidence",

                query_used=
                    query_used,

                source=
                    "OpenStreetMap/Nominatim"
            )


        # ====================================================
        # EXTRACT
        # ====================================================

        city_result, governorate_result, country = (
            self.extract_address(
                candidate
            )
        )


        latitude = candidate.get(
            "lat"
        )

        longitude = candidate.get(
            "lon"
        )


        print(
            f"   ✅ Location found"
        )

        print(
            f"   📌 "
            f"{candidate.get('display_name', '')}"
        )

        print(
            f"   🎯 Confidence:"
            f" {confidence:.3f}"
        )


        return LocationResult(

            landmark_name=
                landmark_name,

            latitude=
                float(latitude)
                if latitude
                else None,

            longitude=
                float(longitude)
                if longitude
                else None,

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

            osm_type=
                (
                    candidate.get(
                        "type",
                        ""
                    )
                ),

            source=
                "OpenStreetMap/Nominatim",

            confidence=
                confidence,

            status=
                "success",

            query_used=
                query_used
        )


# ============================================================
# HELPER FUNCTION
# ============================================================

def find_landmark_location(
    landmark_name: str,
    city: str = "",
    governorate: str = ""
):

    agent = LocationAgent()

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

    result = find_landmark_location(
        "Agiba beach"
    )

    print("\n" + "=" * 60)

    print(
        "📍 LOCATION RESULT"
    )

    print("=" * 60)

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )