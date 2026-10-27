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

    Tier 1 — Direct lookup:
        Named sections, definitions, bare-act text, "which section covers X",
        punishment-for-named-offence, short factual queries.

    Tier 2 — Scenario-based:
        Facts with actors/events, FIR/police narratives, hypotheticals,
        multi-party disputes, consequence-from-facts, what-offence-is-made-out.
    """

    # ── Tier-1 signals ────────────────────────────────────────────────────

    SECTION_CODE = re.compile(
        r"\b(?:section|sec\.?|article|art\.?)\s*\d+|\b(?:bns|bnss|bsa|ipc|crpc|iea)\s*\d+",
        re.IGNORECASE,
    )

    DIRECT_LOOKUP = re.compile(
        r"\b(what is|what's|whats|define|definition of|meaning of|"
        r"punishment (?:for|under)|what is the punishment|"
        r"which section|related section|corresponding section|"
        r"bare act|explain section|tell me (?:about )?section|"
        r"what does section|text of section|"
        r"ingredients of|essentials of|elements of|"
        r"maximum (?:punishment|sentence|penalty)|"
        r"minimum (?:punishment|sentence|penalty)|"
        r"difference between .+ and .+ (?:section|act|provision)|"
        r"list (?:the )?sections|"
        r"new (?:section|provision) for|"
        r"old (?:section|provision) for|"
        r"ipc equivalent|bns equivalent)\b",
        re.IGNORECASE,
    )

    # ── Tier-2 signals ────────────────────────────────────────────────────

    HYPOTHETICAL = re.compile(
        r"\b(suppose|what if|in this case|in such (?:a )?case|scenario|"
        r"imagine|hypothetical|consider (?:a |the |this )?(?:situation|case)|"
        r"if a (?:person|man|woman|boy|girl|minor|juvenile|he|she|they)|"
        r"if someone|in (?:a |the )?given (?:scenario|situation|facts)|"
        r"let us say|let's say|assume that|assuming)\b",
        re.IGNORECASE,
    )

    EVENT = re.compile(
        r"\b(happened|yesterday|last night|this morning|on \d|"
        r"accused|complainant|neighbour|neighbor|my friend|"
        r"police (?:came|came to|registered|filed|arrest)|"
        r"\bfir\b|chargesheet|bail|remand|custody|"
        r"what (?:offence|offense|crime|charge) (?:is|are|may be|can be|would be) (?:made out|attracted|applicable|filed)|"
        r"can (?:he|she|they|i|we) be|will (?:he|she|they|i|we) get|"
        r"provisions? (?:attracted|applicable|that apply)|sections? (?:apply|applicable|attracted)|"
        r"what (?:action|steps?|remedy|remedies) (?:can|should|may)|"
        r"can (?:a |the )?(?:complaint|case|fir) be (?:filed|registered|lodged)|"
        r"is (?:it|this) (?:a |an )?(?:cognizable|bailable|compoundable)|"
        r"legal (?:consequences?|implications?|liability|recourse|remedy)|"
        r"what (?:can|should|will) happen|"
        r"how (?:to|can|should) (?:file|register|lodge) (?:a |an )?(?:fir|complaint|case)|"
        r"rights? of (?:the )?(?:accused|victim|complainant))\b",
        re.IGNORECASE,
    )

    INCIDENT_VERB = re.compile(
        r"\b(stole|stolen|steal|snatched|snatching|robbed|robbery|"
        r"assaulted|assault|beat|beaten|beating|"
        r"killed|murdered|stabbed|shot|"
        r"cheated|cheating|defrauded|fraud|"
        r"forged|forgery|counterfeited|"
        r"kidnapped|kidnapping|abducted|abduction|"
        r"raped|molested|molestation|sexual (?:assault|harassment)|"
        r"threatened|threatening|extorted|extortion|blackmailed|"
        r"broke into|trespassed|trespassing|"
        r"hurt|injured|grievous|"
        r"hit me|hit him|hit her|"
        r"took (?:my|his|her|the)|took away|"
        r"filed (?:an )?fir|registered (?:an )?fir|"
        r"attacked|poisoned|strangled|"
        r"defamed|slandered|stalked|stalking|"
        r"bribed|bribing|"
        r"damaged (?:my|his|her|the|property)|"
        r"set fire|arson|burnt|"
        r"eloped|absconded|fled|escaped|"
        r"caught (?:red.?handed|stealing|cheating)|"
        r"detained|confined|imprisoned|wrongful)"
        r"\b",
        re.IGNORECASE,
    )

    ACTOR = re.compile(
        r"\b(a (?:man|woman|person|boy|girl|minor|juvenile|group|gang)|"
        r"someone|the accused|the victim|"
        r"husband|wife|father|mother|son|daughter|"
        r"neighbour|neighbor|shopkeeper|driver|employer|employee|"
        r"landlord|tenant|teacher|student|doctor|patient|"
        r"servant|domestic help|"
        r"my|his|her|their|our)\b",
        re.IGNORECASE,
    )

    FIRST_PERSON = re.compile(r"\b(i|we|my|our|me)\b", re.IGNORECASE)

    # Multi-party / dispute patterns
    DISPUTE = re.compile(
        r"\b(dispute|quarrel|fight|altercation|argument|conflict|"
        r"domestic violence|dowry|cruelty|maintenance|"
        r"property dispute|land dispute|boundary dispute|"
        r"consumer complaint|medical negligence|"
        r"road (?:accident|rage)|hit and run|"
        r"cyber (?:crime|fraud|bullying|stalking)|"
        r"online (?:fraud|cheating|harassment))\b",
        re.IGNORECASE,
    )

    # Procedural / consequence questions (always Tier-2)
    PROCEDURE_CONSEQUENCE = re.compile(
        r"\b(what (?:is|are) (?:the )?(?:procedure|process|steps?)|"
        r"how (?:to|can|do|does|should|will)|"
        r"where (?:to|should|can) (?:file|complain|report)|"
        r"which court|which (?:authority|forum)|"
        r"anticipatory bail|regular bail|interim bail|"
        r"investigation (?:procedure|process)|"
        r"punishment (?:if|when|for a person)|"
        r"sentence (?:for|if|when)|"
        r"imprisonment (?:for|if|when)|"
        r"fine (?:for|if|when)|"
        r"compensation (?:for|if|when))\b",
        re.IGNORECASE,
    )

    def __init__(self, exact_router: ExactMatchRouter | None = None, max_tier1_words: int = 28):
        self.exact_router = exact_router or ExactMatchRouter()
        self.max_tier1_words = max_tier1_words

    def classify(self, query: str) -> TierDecision:
        q = (query or "").strip()
        words = [w for w in re.split(r"\s+", q) if w]
        n_words = len(words)
        signals: List[str] = []

        # ── Check Tier-2 (scenario) signals first ─────────────────────────
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

        if self.DISPUTE.search(q):
            signals.append("dispute_scenario")
            is_scenario = True

        if self.PROCEDURE_CONSEQUENCE.search(q) and (
            self.INCIDENT_VERB.search(q)
            or self.ACTOR.search(q)
            or self.DISPUTE.search(q)
            or n_words >= 15
        ):
            signals.append("procedural_with_facts")
            is_scenario = True

        if n_words >= 36:
            signals.append("long_query")
            is_scenario = True

        if q.count(".") + q.count(";") >= 2:
            signals.append("multi_sentence")
            is_scenario = True

        # Multiple incident verbs or actors → strong scenario signal
        incident_matches = self.INCIDENT_VERB.findall(q)
        if len(incident_matches) >= 2:
            signals.append("multiple_incidents")
            is_scenario = True

        if is_scenario:
            return TierDecision("tier2", "scenario_based", signals)

        # ── Check Tier-1 (direct lookup) signals ──────────────────────────

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

        # ── Default to Tier-2 for ambiguous longer queries ────────────────
        signals.append("default_scenario")
        return TierDecision("tier2", "scenario_based", signals)
