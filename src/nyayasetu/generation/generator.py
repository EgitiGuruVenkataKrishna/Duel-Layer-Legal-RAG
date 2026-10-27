import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class LegalAnswerGenerator:
    """
    Evidence-grounded statutory answer synthesizer using live Groq models.
    Enforces strict citation constraints and abstention on out-of-scope or ungrounded questions.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Groq client: {e}")

    def generate(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        temporal_info: Optional[Dict[str, Any]] = None,
        offence_info: Optional[Dict[str, Any]] = None,
        transition_info: Optional[Dict[str, Any]] = None,
        use_llm: bool = True,
        strict_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes an answer with statutory citations.
        """
        # Build context from retrieved documents
        context_parts = []
        for doc in retrieved_docs:
            act = doc.get("act", doc.get("act_code", "Statute"))
            chap = doc.get("chapter", "")
            sec = doc.get("section_no", "")
            title = doc.get("title", "")
            page = doc.get("page", "")
            text = doc.get("text", "")

            header = f"[Source: Act: {act}, Section {sec} ({title}), Page {page}]"
            context_parts.append(f"{header}\n{text}")

        context_str = "\n\n---\n\n".join(context_parts)

        # Append structured metadata if present
        extra_context = []
        if temporal_info:
            extra_context.append(
                f"[Temporal Legality Analysis]\n"
                f"Offence Date: {temporal_info.get('offence_date')}\n"
                f"FIR Date: {temporal_info.get('fir_date')}\n"
                f"Substantive Law: {temporal_info.get('substantive_law')}\n"
                f"Reason: {temporal_info.get('substantive_reason')}\n"
                f"Procedural Law: {temporal_info.get('procedural_law')}\n"
                f"Reason: {temporal_info.get('procedural_reason')}"
            )
        if offence_info:
            extra_context.append(
                f"[Offence Classification]\n"
                f"Section: {offence_info.get('section')}\n"
                f"Offence: {offence_info.get('offence')}\n"
                f"Punishment: {offence_info.get('punishment')}\n"
                f"Cognizable: {offence_info.get('cognizable')}\n"
                f"Bailable: {offence_info.get('bailable')}\n"
                f"Compoundable: {offence_info.get('compoundable')}\n"
                f"Triable By: {offence_info.get('triable_by')}"
            )
        if transition_info:
            extra_context.append(
                f"[Transitional Difference]\n"
                f"Old Law: {transition_info.get('old_code')} Section {transition_info.get('old_sec')}\n"
                f"New Law: {transition_info.get('new_code')} Section {transition_info.get('new_sec')}\n"
                f"Subject: {transition_info.get('title')}\n"
                f"Key Changes: {transition_info.get('key_differences')}"
            )

        if extra_context:
            context_str += "\n\n" + "\n\n".join(extra_context)

        allowed = ", ".join(strict_ids) if strict_ids else "only sections present in the evidence"
        sys_prompt = (
            "You are NyayaSetu, an Indian criminal-law research assistant. "
            "Use ONLY the statutory evidence provided. This is not legal advice.\n"
            "Rules:\n"
            "1. Every legal assertion must end with a citation of the form [Act: BNS, Section 103].\n"
            "2. Cite only these section ids: "
            f"{allowed}. Never invent a section number.\n"
            "3. If evidence is insufficient, say so and do not guess.\n"
            "4. Prefer quoting short phrases from the provided text in double quotes.\n"
            "5. Phrase offence analysis as provisions potentially attracted, never a guilt verdict."
        )

        user_content = f"Query: {query}\n\nStatutory Evidence Context:\n{context_str}\n\nProvide a structured, citation-grounded response:"

        if use_llm and self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.0,
                    max_tokens=1024,
                )
                answer = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else 0
                return {
                    "answer": answer,
                    "model": self.model_name,
                    "tokens_used": tokens_used,
                    "grounded": True,
                }
            except Exception as e:
                print(f"Groq API error ({self.model_name}): {e}. Falling back to deterministic synthesis.")

        # Deterministic evidence synthesis fallback (ensures tests & offline demo work without API key)
        fallback_answer = self._synthesize_deterministic(query, retrieved_docs, temporal_info, offence_info, transition_info)
        return {
            "answer": fallback_answer,
            "model": "deterministic-evidence-synthesizer",
            "tokens_used": len(fallback_answer.split()) * 2,
            "grounded": True,
        }

    def _synthesize_deterministic(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        temporal_info: Optional[Dict[str, Any]],
        offence_info: Optional[Dict[str, Any]],
        transition_info: Optional[Dict[str, Any]],
    ) -> str:
        lines = []
        if temporal_info:
            lines.append("### Temporal Applicability Analysis")
            lines.append(f"- **Substantive Law**: {temporal_info['substantive_law']}")
            lines.append(f"  *Reason*: {temporal_info['substantive_reason']}")
            lines.append(f"- **Procedural Law**: {temporal_info['procedural_law']}")
            lines.append(f"  *Reason*: {temporal_info['procedural_reason']}")
            lines.append(f"- **Evidence**: {temporal_info['evidence_law']}")
            lines.append(f"- **Constitutional Basis**: {temporal_info['constitutional_basis']}\n")

        if transition_info:
            lines.append("### Statutory Transition Details")
            lines.append(f"- **Old Provision**: {transition_info['old_code']} Section {transition_info['old_sec']}")
            lines.append(f"- **New Provision**: {transition_info['new_code']} Section {transition_info['new_sec']}")
            lines.append(f"- **Subject**: {transition_info['title']}")
            lines.append(f"- **Key Differences**: {transition_info['key_differences']}\n")

        if offence_info:
            lines.append("### Offence Classification (BNSS First Schedule)")
            lines.append(f"- **Section**: {offence_info['section']} ({offence_info['act']})")
            lines.append(f"- **Offence**: {offence_info['offence']}")
            lines.append(f"- **Punishment**: {offence_info['punishment']}")
            lines.append(f"- **Cognizable**: {offence_info['cognizable']}")
            lines.append(f"- **Bailable**: {offence_info['bailable']}")
            lines.append(f"- **Triable By**: {offence_info['triable_by']}\n")

        if retrieved_docs:
            lines.append("### Primary Statutory Evidence")
            for doc in retrieved_docs[:3]:
                act = doc.get("act_code", "Statute")
                sec = doc.get("section_no", "")
                title = doc.get("title", "")
                page = doc.get("page", "")
                body = doc.get("text", "")[:350].strip()
                lines.append(f"**[Act: {act}, Section {sec}]** ({title}, page {page})")
                lines.append(f"{body}...\n")
        else:
            lines.append("Insufficient legal precedent or statutory clarity in the corpus to ground a definitive response.")

        return "\n".join(lines)


if __name__ == "__main__":
    generator = LegalAnswerGenerator()
    dummy_doc = {
        "act_code": "BNS",
        "act": "Bharatiya Nyaya Sanhita, 2023",
        "section_no": "103",
        "title": "Punishment for murder.",
        "page": 34,
        "text": "103. (1) Whoever commits murder shall be punished with death or imprisonment for life...",
    }
    ans = generator.generate("What is the penalty for murder in BNS?", [dummy_doc])
    print(ans["answer"])
