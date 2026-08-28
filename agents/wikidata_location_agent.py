# ============================================================
# 🇪🇬 EGYPT EXPLORER AI
# 📍 WIKIDATA LOCATION RECOVERY AGENT
# ============================================================

from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from typing import Optional

import requests


# ============================================================
# CONFIG
# ============================================================

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

WIKIDATA_ENTITY_API = (
    "https://www.wikidata.org/wiki/Special:EntityData/"
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
class WikidataLocationResult:

    landmark_name: str

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    wikidata_id: str = ""

    wikidata_label: str = ""

    description: str = ""

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

class WikidataLocationAgent:

    def __init__(
        self,
        min_confidence: float = MIN_CONFIDENCE
    ):

        self.min_confidence = min_confidence

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

        return set(
            cls.normalize(
                text
            ).split()
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

        target = cls.tokens(
            landmark_name
        )

        candidate = cls.tokens(
            candidate_name
        )

        if not target or not candidate:

            return 0.0

        common = target & candidate

        overlap = (
            len(common)
            / len(target)
        )

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
                0.90
            )

        return round(
            min(overlap, 1.0),
            3
        )


    # ========================================================
    # SEARCH WIKIDATA
    # ========================================================

    def search_entities(
        self,
        query: str,
        limit: int = 10
    ):

        params = {

            "action":
                "wbsearchentities",

            "search":
                query,

            "language":
                "en",

            "uselang":
                "en",

            "format":
                "json",

            "limit":
                limit
        }

        try:

            response = self.session.get(
                WIKIDATA_API,
                params=params,
                timeout=TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            return data.get(
                "search",
                []
            )

        except Exception as exc:

            print(
                f"   ⚠️ Wikidata search error:"
                f" {exc}"
            )

            return []


    # ========================================================
    # GET ENTITY
    # ========================================================

    def get_entity(
        self,
        entity_id: str
    ):

        url = (
            WIKIDATA_ENTITY_API
            + entity_id
            + ".json"
        )

        try:

            response = self.session.get(
                url,
                timeout=TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            return (
                data
                .get(
                    "entities",
                    {}
                )
                .get(
                    entity_id
                )
            )

        except Exception as exc:

            print(
                f"   ⚠️ Wikidata entity error:"
                f" {exc}"
            )

            return None


    # ========================================================
    # EXTRACT COORDINATES
    # ========================================================

    @staticmethod
    def extract_coordinates(
        entity
    ):

        if not entity:

            return None

        claims = entity.get(
            "claims",
            {}
        )

        coordinate_claims = claims.get(
            "P625",
            []
        )

        for claim in coordinate_claims:

            mainsnak = claim.get(
                "mainsnak",
                {}
            )

            datavalue = mainsnak.get(
                "datavalue"
            )

            if not datavalue:

                continue

            value = datavalue.get(
                "value",
                {}
            )

            latitude = value.get(
                "latitude"
            )

            longitude = value.get(
                "longitude"
            )

            if (
                latitude is not None
                and longitude is not None
            ):

                return (
                    float(latitude),
                    float(longitude)
                )

        return None


    # ========================================================
    # EXTRACT LABEL
    # ========================================================

    @staticmethod
    def extract_label(
        entity
    ):

        if not entity:

            return ""

        labels = entity.get(
            "labels",
            {}
        )

        english = labels.get(
            "en"
        )

        if english:

            return english.get(
                "value",
                ""
            )

        # Fallback to any label.
        for value in labels.values():

            if value.get("value"):

                return value["value"]

        return ""


    # ========================================================
    # EXTRACT DESCRIPTION
    # ========================================================

    @staticmethod
    def extract_description(
        entity
    ):

        if not entity:

            return ""

        descriptions = entity.get(
            "descriptions",
            {}
        )

        english = descriptions.get(
            "en"
        )

        if english:

            return english.get(
                "value",
                ""
            )

        return ""


    # ========================================================
    # EXTRACT COUNTRY
    # ========================================================

    @staticmethod
    def has_egypt_claim(
        entity
    ):

        if not entity:

            return False

        claims = entity.get(
            "claims",
            {}
        )

        # P17 = country.
        country_claims = claims.get(
            "P17",
            []
        )

        for claim in country_claims:

            mainsnak = claim.get(
                "mainsnak",
                {}
            )

            datavalue = mainsnak.get(
                "datavalue"
            )

            if not datavalue:

                continue

            value = datavalue.get(
                "value",
                {}
            )

            entity_id = value.get(
                "id"
            )

            # Q79 = Egypt.
            if entity_id == "Q79":

                return True

        return False


    # ========================================================
    # EXTRACT COORDINATE COUNTRY
    # ========================================================

    @staticmethod
    def extract_claim_ids(
        entity,
        property_id: str
    ):

        ids = []

        if not entity:

            return ids

        claims = entity.get(
            "claims",
            {}
        )

        for claim in claims.get(
            property_id,
            []
        ):

            mainsnak = claim.get(
                "mainsnak",
                {}
            )

            datavalue = mainsnak.get(
                "datavalue"
            )

            if not datavalue:

                continue

            value = datavalue.get(
                "value",
                {}
            )

            entity_id = value.get(
                "id"
            )

            if entity_id:

                ids.append(
                    entity_id
                )

        return ids


    # ========================================================
    # BUILD QUERIES
    # ========================================================

    @staticmethod
    def build_queries(
        landmark_name: str,
        city: str = "",
        governorate: str = ""
    ):

        name = landmark_name.strip()

        queries = []

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
                name
            ]
        )

        return list(
            dict.fromkeys(
                queries
            )
        )


    # ========================================================
    # SCORE ENTITY
    # ========================================================

    def score_entity(
        self,
        landmark_name: str,
        entity: dict,
        city: str = "",
        governorate: str = ""
    ):

        label = entity.get(
            "label",
            ""
        )

        description = entity.get(
            "description",
            ""
        )


        score = (
            0.75
            * self.similarity(
                landmark_name,
                label
            )
        )


        searchable_text = (
            label
            + " "
            + description
        )


        if "egypt" in self.normalize(
            searchable_text
        ):

            score += 0.10


        if city and (
            self.normalize(city)
            in self.normalize(
                searchable_text
            )
        ):

            score += 0.075


        if governorate and (
            self.normalize(
                governorate
            )
            in self.normalize(
                searchable_text
            )
        ):

            score += 0.075


        return round(
            min(score, 1.0),
            3
        )


    # ========================================================
    # FIND LOCATION
    # ========================================================

    def find_location(
        self,
        landmark_name: str,
        city: str = "",
        governorate: str = ""
    ) -> WikidataLocationResult:

        print(
            f"\n🌍 Wikidata Agent:"
            f" {landmark_name}"
        )


        queries = self.build_queries(
            landmark_name,
            city,
            governorate
        )


        candidates = []


        # ====================================================
        # SEARCH
        # ====================================================

        for query in queries:

            print(
                f"   🔎 Wikidata:"
                f" {query}"
            )

            results = (
                self.search_entities(
                    query
                )
            )


            for item in results:

                entity_id = item.get(
                    "id",
                    ""
                )

                if not entity_id:

                    continue


                label = item.get(
                    "label",
                    ""
                )

                description = item.get(
                    "description",
                    ""
                )


                score = self.score_entity(
                    landmark_name,
                    item,
                    city,
                    governorate
                )


                candidates.append(
                    {
                        "id":
                            entity_id,

                        "label":
                            label,

                        "description":
                            description,

                        "score":
                            score,

                        "query":
                            query
                    }
                )


            time.sleep(
                0.5
            )


        # ====================================================
        # REMOVE DUPLICATES
        # ====================================================

        unique = {}

        for candidate in candidates:

            entity_id = candidate["id"]

            if (
                entity_id not in unique
                or candidate["score"]
                > unique[entity_id]["score"]
            ):

                unique[entity_id] = candidate


        candidates = list(
            unique.values()
        )


        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        # ====================================================
        # VALIDATE CANDIDATES
        # ====================================================

        for candidate in candidates:

            entity_id = candidate[
                "id"
            ]

            print(
                f"   📌 Candidate:"
                f" {candidate['label']}"
                f" ({entity_id})"
            )


            entity = self.get_entity(
                entity_id
            )


            if not entity:

                continue


            coordinates = (
                self.extract_coordinates(
                    entity
                )
            )


            if not coordinates:

                continue


            # ------------------------------------------------
            # Egypt validation
            # ------------------------------------------------

            egypt_confirmed = (
                self.has_egypt_claim(
                    entity
                )
            )


            lat, lon = coordinates


            # Reject impossible coordinates.
            if not (
                22.0 <= lat <= 32.5
                and
                24.0 <= lon <= 37.5
            ):

                print(
                    "   ⚠️ Coordinates are"
                    " outside Egypt."
                )

                continue


            confidence = candidate[
                "score"
            ]


            if egypt_confirmed:

                confidence = min(
                    confidence + 0.10,
                    1.0
                )


            # ------------------------------------------------
            # Require confidence
            # ------------------------------------------------

            if (
                confidence
                < self.min_confidence
            ):

                print(
                    f"   ⚠️ Low confidence:"
                    f" {confidence:.3f}"
                )

                continue


            label = self.extract_label(
                entity
            )

            description = (
                self.extract_description(
                    entity
                )
            )


            wikidata_url = (
                "https://www.wikidata.org/wiki/"
                + entity_id
            )


            print(
                "   ✅ Verified Wikidata"
                " coordinates"
            )

            print(
                f"   📍 "
                f"{lat}, {lon}"
            )

            print(
                f"   🎯 Confidence:"
                f" {confidence:.3f}"
            )


            return WikidataLocationResult(

                landmark_name=
                    landmark_name,

                latitude=
                    lat,

                longitude=
                    lon,

                wikidata_id=
                    entity_id,

                wikidata_label=
                    label,

                description=
                    description,

                city=
                    city,

                governorate=
                    governorate,

                country=
                    "Egypt",

                source=
                    "Wikidata",

                source_url=
                    wikidata_url,

                confidence=
                    confidence,

                status=
                    "success",

                query_used=
                    candidate["query"]
            )


        # ====================================================
        # NOT FOUND
        # ====================================================

        print(
            "   ❌ No reliable Wikidata"
            " location found."
        )


        return WikidataLocationResult(

            landmark_name=
                landmark_name,

            source=
                "Wikidata",

            status=
                "not_found"
        )


# ============================================================
# HELPER
# ============================================================

def find_wikidata_location(
    landmark_name: str,
    city: str = "",
    governorate: str = ""
):

    agent = WikidataLocationAgent()

    result = agent.find_location(
        landmark_name,
        city,
        governorate
    )

    return asdict(
        result
    )


# ============================================================
# MODULE MODE
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "🇪🇬 EGYPT EXPLORER AI"
    )

    print(
        "📍 WIKIDATA LOCATION RECOVERY AGENT"
    )

    print(
        "=" * 70
    )

    print(
        "\nModule ready."
    )

    print(
        "It should be called from the"
        " Colab pipeline."
    )