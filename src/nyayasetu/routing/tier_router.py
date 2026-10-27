import re
from dataclasses import dataclass, field
from typing import List

from src.nyayasetu.retrieval.exact_router import ExactMatchRouter


@dataclass
class TierDecision:
    tier: str
    reason: str
    signals: List[str] = field(default_factory=list)


class DualTierClassifier:
    """
    Deterministic dual-tier router. No LLM.

    Tier 1 — direct lookup: named sections, definitions, “which section covers X”.
    Tier 2 — scenario: facts, people, events, FIR/police narratives, hypotheticals.
    """

    SECTION_CODE = re.compile(
        r"\b(?:section|sec\.?|article|art\.?)\s*\d+|\b(?:bns|bnss|bsa|ipc|crpc|iea)\s*\d+",
        re.IGNORECASE,
    )
    DIRECT_LOOKUP = re.compile(
        r"\b(what is|what's|whats|define|definition of|meaning of|"
        r"punishment (?:for|under)|what is the punishment|"
        r"which section|related section|corresponding section|"
        r"bare act|explain section|tell me (?:about )?section|"
        r"what does section|text of section)\b",
        re.IGNORECASE,
    )
    HYPOTHETICAL = re.compile(
        r"\b(suppose|what if|in this case|in such (?:a )?case|scenario|"
        r"imagine|hypothetical|if a (?:person|man|woman|he|she))\b",
        re.IGNORECASE,
    )
    EVENT = re.compile(
        r"\b(happened|yesterday|last night|this morning|on \d|"
        r"accused|complainant|neighbour|neighbor|my friend|"
        r"police (?:came|came to|registered|filed|arrest)|"
        r"\bfir\b|chargesheet|bail|"
        r"what (?:offence|offense) (?:is|are|may be) made out|"
        r"can (?:he|she|they|i) be|will (?:he|she|they|i) get|"
        r"provisions? (?:attracted|applicable)|sections? apply)\b",
        re.IGNORECASE,
    )
    INCIDENT_VERB = re.compile(
        r"\b(stole|stolen|steal|snatched|snatching|robbed|assaulted|beat|beaten|"
        r"killed|murdered|stabbed|cheated|forged|kidnapped|raped|threatened|"
        r"broke into|trespassed|hurt|hit me|took (?:my|his|her|the)|"
        r"filed (?:an )?fir|registered (?:an )?fir)\b",
        re.IGNORECASE,
    )
    ACTOR = re.compile(
        r"\b(a (?:man|woman|person|boy|girl)|someone|the accused|"
        r"husband|wife|neighbour|neighbor|shopkeeper|driver|my)\b",
        re.IGNORECASE,
    )
    FIRST_PERSON = re.compile(r"\b(i|we|my|our|me)\b", re.IGNORECASE)

    def __init__(self, exact_router: ExactMatchRouter | None = None, max_tier1_words: int = 28):
        self.exact_router = exact_router or ExactMatchRouter()
        self.max_tier1_words = max_tier1_words

    def classify(self, query: str) -> TierDecision:
        q = (query or "").strip()
        words = [w for w in re.split(r"\s+", q) if w]
        n_words = len(words)
        signals: List[str] = []

        is_scenario = False
        if self.HYPOTHETICAL.search(q):
            signals.append("hypothetical")
            is_scenario = True
        if self.EVENT.search(q):
            signals.append("event_or_procedure")
            is_scenario = True
        if self.INCIDENT_VERB.search(q) and (self.ACTOR.search(q) or n_words >= 12):
            signals.append("incident_narrative")
            is_scenario = True
        if self.FIRST_PERSON.search(q) and self.INCIDENT_VERB.search(q):
            signals.append("first_person_incident")
            is_scenario = True
        if n_words >= 36:
            signals.append("long_query")
            is_scenario = True
        if q.count(".") + q.count(";") >= 2:
            signals.append("multi_sentence")
            is_scenario = True

        if is_scenario:
            return TierDecision("tier2", "scenario_based", signals)

        exact = self.exact_router.route(q)
        if exact:
            signals.append("named_section")
            return TierDecision("tier1", "named_section_lookup", signals)

        if self.SECTION_CODE.search(q) or self.DIRECT_LOOKUP.search(q):
            signals.append("direct_lookup_language")
            return TierDecision("tier1", "direct_statutory_lookup", signals)

        if n_words <= self.max_tier1_words and not self.INCIDENT_VERB.search(q):
            signals.append("short_lookup")
            return TierDecision("tier1", "short_direct_question", signals)

        signals.append("default_scenario")
        return TierDecision("tier2", "scenario_based", signals)
