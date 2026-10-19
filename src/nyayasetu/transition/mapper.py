from typing import Any, Dict, List, Optional


class StatutoryTransitionMapper:
    """
    Authoritative cross-statute transitional mapping and comparative diff analysis:
    - IPC (1860) <-> BNS (2023)
    - CrPC (1973) <-> BNSS (2023)
    - IEA (1872) <-> BSA (2023)
    """

    # Comprehensive transition table
    MAPPINGS: List[Dict[str, Any]] = [
        # IPC -> BNS landmark transitions
        {
            "old_code": "IPC",
            "old_sec": "302",
            "new_code": "BNS",
            "new_sec": "103(1)",
            "title": "Murder",
            "change_type": "Restructured / Number Renumbered",
            "key_differences": "Murder punishment moved from IPC 302 to BNS 103(1). BNS 103(2) introduces separate severe punishment for murder committed by a group of five or more persons on grounds of race, caste, sex, or place of birth (mob lynching) with death or life imprisonment."
        },
        {
            "old_code": "IPC",
            "old_sec": "307",
            "new_code": "BNS",
            "new_sec": "109",
            "title": "Attempt to Murder",
            "change_type": "Renumbered",
            "key_differences": "Renumbered from IPC 307 to BNS 109. Retains imprisonment up to 10 years and fine; if hurt caused, life imprisonment or up to 10 years."
        },
        {
            "old_code": "IPC",
            "old_sec": "375",
            "new_code": "BNS",
            "new_sec": "63",
            "title": "Rape (Definition)",
            "change_type": "Renumbered and Updated",
            "key_differences": "Definition renumbered from IPC 375 to BNS 63. Age of consent affirmed at eighteen years."
        },
        {
            "old_code": "IPC",
            "old_sec": "376",
            "new_code": "BNS",
            "new_sec": "64",
            "title": "Punishment for Rape",
            "change_type": "Renumbered & Enhanced Penalties",
            "key_differences": "Moved to BNS 64. Rigorous imprisonment for not less than 10 years up to life imprisonment."
        },
        {
            "old_code": "IPC",
            "old_sec": "376D",
            "new_code": "BNS",
            "new_sec": "70(1)",
            "title": "Gang Rape",
            "change_type": "Renumbered",
            "key_differences": "Gang rape moved to BNS 70(1); gang rape of woman under eighteen moved to BNS 70(2) punishable with life imprisonment (natural life) or death."
        },
        {
            "old_code": "IPC",
            "old_sec": "420",
            "new_code": "BNS",
            "new_sec": "318(4)",
            "title": "Cheating and dishonestly inducing delivery of property",
            "change_type": "Sub-clause Restructuring",
            "key_differences": "IPC 420 is now codified under BNS Section 318, sub-section (4). Retains imprisonment up to 7 years and fine."
        },
        {
            "old_code": "IPC",
            "old_sec": "378",
            "new_code": "BNS",
            "new_sec": "303(1)",
            "title": "Theft (Definition)",
            "change_type": "Consolidated",
            "key_differences": "Definition codified under BNS 303(1). Punishment under BNS 303(2) introduces community service for first-time theft where value of stolen property is less than Rs 5,000 upon return."
        },
        {
            "old_code": "IPC",
            "old_sec": "379",
            "new_code": "BNS",
            "new_sec": "303(2)",
            "title": "Punishment for Theft",
            "change_type": "Penalty Reform",
            "key_differences": "Punishment up to 3 years or fine or both; community service provision for petty theft under Rs 5,000."
        },
        {
            "old_code": "IPC",
            "old_sec": "None (New)",
            "new_code": "BNS",
            "new_sec": "304",
            "title": "Snatching",
            "change_type": "New Offence",
            "key_differences": "Specific offence of snatching introduced with imprisonment up to 3 years and fine."
        },
        {
            "old_code": "IPC",
            "old_sec": "None (New)",
            "new_code": "BNS",
            "new_sec": "111",
            "title": "Organised Crime",
            "change_type": "New Offence",
            "key_differences": "Comprehensive offence of organised crime covering continuing unlawful activities by crime syndicates."
        },
        {
            "old_code": "IPC",
            "old_sec": "None (New)",
            "new_code": "BNS",
            "new_sec": "113",
            "title": "Terrorist Act",
            "change_type": "New Offence in General Penal Code",
            "key_differences": "Terrorist acts explicitly incorporated into general penal law alongside special statutes."
        },
        {
            "old_code": "IPC",
            "old_sec": "124A",
            "new_code": "BNS",
            "new_sec": "152",
            "title": "Acts endangering sovereignty, unity and integrity of India",
            "change_type": "Repeal and Modernization",
            "key_differences": "Colonial sedition (IPC 124A) repealed. Replaced by Section 152 punishing acts endangering sovereignty, unity, and integrity of India with enhanced safeguard against penalizing legitimate democratic dissent."
        },
        {
            "old_code": "IPC",
            "old_sec": "498A",
            "new_code": "BNS",
            "new_sec": "85 / 86",
            "title": "Cruelty by Husband or Relatives",
            "change_type": "Bifurcated",
            "key_differences": "Cruelty by husband or relative bifurcated: punishment under Section 85 (up to 3 years), definition of cruelty under Section 86."
        },
        {
            "old_code": "IPC",
            "old_sec": "499 / 500",
            "new_code": "BNS",
            "new_sec": "356",
            "title": "Defamation",
            "change_type": "Penalty Option Expanded",
            "key_differences": "Defamation consolidated under Section 356. Community service added as alternative penalty alongside simple imprisonment up to 2 years or fine."
        },

        # CrPC -> BNSS landmark transitions
        {
            "old_code": "CRPC",
            "old_sec": "154",
            "new_code": "BNSS",
            "new_sec": "173",
            "title": "Information in cognizable cases (FIR)",
            "change_type": "Modernization / e-FIR",
            "key_differences": "BNSS 173 formally legalizes electronic communication (e-FIR), requiring signature within three days; mandatory preliminary inquiry within 14 days for offences punishable between 3 to 7 years."
        },
        {
            "old_code": "CRPC",
            "old_sec": "161",
            "new_code": "BNSS",
            "new_sec": "180",
            "title": "Examination of witnesses by police",
            "change_type": "Audio-Video Recording",
            "key_differences": "Statements of witnesses may be recorded by audio-video electronic means."
        },
        {
            "old_code": "CRPC",
            "old_sec": "167",
            "new_code": "BNSS",
            "new_sec": "187",
            "title": "Procedure when investigation cannot be completed in 24 hours (Custody)",
            "change_type": "Custody Flexibility",
            "key_differences": "Police custody of 15 days can now be sought in whole or in parts during the first 40 or 60 days of the total detention period of 60 or 90 days."
        },
        {
            "old_code": "CRPC",
            "old_sec": "173",
            "new_code": "BNSS",
            "new_sec": "193",
            "title": "Police report on completion of investigation (Chargesheet)",
            "change_type": "Strict Timelines",
            "key_differences": "Mandatory completion of investigation within 90 days in rape cases; police must inform informant or victim of progress within 90 days."
        },
        {
            "old_code": "CRPC",
            "old_sec": "437",
            "new_code": "BNSS",
            "new_sec": "480",
            "title": "When bail may be taken in case of non-bailable offence",
            "change_type": "Renumbered",
            "key_differences": "CrPC 437 is now BNSS Section 480. First-time offenders and women/sick persons receive statutory consideration."
        },
        {
            "old_code": "CRPC",
            "old_sec": "438",
            "new_code": "BNSS",
            "new_sec": "482",
            "title": "Anticipatory Bail (Direction for grant of bail)",
            "change_type": "Renumbered",
            "key_differences": "CrPC 438 is now BNSS Section 482. Application lies before High Court or Court of Session."
        },
        {
            "old_code": "CRPC",
            "old_sec": "439",
            "new_code": "BNSS",
            "new_sec": "483",
            "title": "Special powers of High Court or Court of Session regarding bail",
            "change_type": "Renumbered",
            "key_differences": "CrPC 439 is now BNSS Section 483."
        },

        # IEA -> BSA landmark transitions
        {
            "old_code": "IEA",
            "old_sec": "65B",
            "new_code": "BSA",
            "new_sec": "61 / 63",
            "title": "Electronic Records and Digital Evidence",
            "change_type": "Digital Primacy",
            "key_differences": "BSA elevates electronic records to primary evidence under Section 61. Certificate under Section 63 aligns with Schedule for digital devices, cloud data, and mobile communications."
        },
        {
            "old_code": "IEA",
            "old_sec": "32(1)",
            "new_code": "BSA",
            "new_sec": "26",
            "title": "Dying Declaration",
            "change_type": "Renumbered",
            "key_differences": "Statement of relevant fact by dead or untraceable person moved to BSA Section 26."
        },
    ]

    @classmethod
    def lookup_transition(cls, query_code: str, query_sec: str) -> Optional[Dict[str, Any]]:
        clean_code = query_code.upper().strip()
        clean_sec = query_sec.strip()

        for m in cls.MAPPINGS:
            old_secs = [s.strip() for s in m["old_sec"].split("/")]
            new_secs = [s.strip() for s in m["new_sec"].split("/")]

            if m["old_code"] == clean_code:
                if any(clean_sec == s or clean_sec.startswith(s) for s in old_secs):
                    return m
            if m["new_code"] == clean_code:
                if any(clean_sec == s or clean_sec.startswith(s) for s in new_secs):
                    return m
        return None

    @classmethod
    def search_transitions(cls, keyword: str) -> List[Dict[str, Any]]:
        kw = keyword.lower()
        results = []
        for m in cls.MAPPINGS:
            if (
                kw in m["title"].lower()
                or kw in m["key_differences"].lower()
                or kw in m["old_sec"].lower()
                or kw in m["new_sec"].lower()
            ):
                results.append(m)
        return results


if __name__ == "__main__":
    mapper = StatutoryTransitionMapper()
    res = mapper.lookup_transition("IPC", "302")
    print("IPC 302 -> BNS:", res)
    res2 = mapper.lookup_transition("CRPC", "438")
    print("CrPC 438 -> BNSS:", res2)
