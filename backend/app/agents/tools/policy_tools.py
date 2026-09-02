"""The one deliberate exception to tools/base.py's "model never sees the
real data" rule: search_policy_knowledge_base is where model paraphrase is
the actual point (turning retrieved passages into a concise grounded
answer). Citations, however, are still built in Python from the retrieved
hits and never touched by the model - see ToolOutcome.needs_model_text."""

from typing import Callable

from app.agents.tools.base import ALREADY_SHOWN, ToolOutcome, logged_tool
from app.core.config import settings
from app.prompts.loader import load_prompt
from app.schemas.chat import ChatMessage, Citation
from app.services import rag_service

_NOT_FOUND_MESSAGE = ChatMessage(
    type="text",
    content="I don't have that in the knowledge base - it may not be documented yet.",
    status="final",
)

_SEARCH_POLICY_KB_DOC = load_prompt("tools/search_policy_kb")


def _extract_snippet(indexed_text: str, max_chars: int = 480) -> str:
    """rag_service embeds each chunk as "{title} - {section}\\n{body}" (see
    ingest_document) - strip that prefix so the citation shows the actual
    source passage, not a repeat of the title/section already shown above
    it. Truncated to a readable preview length."""
    body = indexed_text.split("\n", 1)[1] if "\n" in indexed_text else indexed_text
    body = body.strip()
    if len(body) > max_chars:
        body = body[:max_chars].rsplit(" ", 1)[0] + "…"
    return body


def _build_citations(hits: list[dict]) -> list[Citation]:
    seen = set()
    citations = []
    for hit in hits:
        key = (hit["document_title"], hit["section"])
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            Citation(
                document_title=hit["document_title"],
                version=hit["version"],
                source_updated_at=hit["source_updated_at"],
                section=hit["section"],
                snippet=_extract_snippet(hit["text"]),
            )
        )
    return citations


def build_tools(outcomes: list[ToolOutcome]) -> list[Callable]:
    @logged_tool
    def search_policy_knowledge_base(query: str) -> str:
        hits = rag_service.search(query)
        if not hits or hits[0]["similarity"] < settings.rag_min_similarity:
            outcomes.append(ToolOutcome(chat_message=_NOT_FOUND_MESSAGE))
            return "No relevant documentation was found - this refusal was already shown to the user. Do not attempt to answer from general knowledge."

        relevant_hits = [h for h in hits if h["similarity"] >= settings.rag_min_similarity]
        citations = _build_citations(relevant_hits)
        outcomes.append(
            ToolOutcome(
                chat_message=ChatMessage(
                    type="citation-answer", content="", citations=citations, status="final"
                ),
                needs_model_text=True,
            )
        )

        passages = "\n\n".join(
            f"[Passage {i + 1} - {hit['document_title']}, {hit['section']}]\n{hit['text']}"
            for i, hit in enumerate(relevant_hits)
        )
        return (
            "Retrieved passages (compose your final answer from these only, per your "
            f"instructions):\n\n{passages}"
        )

    search_policy_knowledge_base.__doc__ = _SEARCH_POLICY_KB_DOC

    return [search_policy_knowledge_base]
