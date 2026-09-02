from typing import Literal

from pydantic import BaseModel

from app.agents.base_agent import BaseSubAgent
from app.agents.messages import UNAVAILABLE_MESSAGE
from app.core.config import settings
from app.core.exceptions import CircuitOpenError, LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger
from app.prompts.loader import load_prompt
from app.schemas.chat import ChatMessage, Citation
from app.services import rag_service

logger = get_logger("rag_agent")

_NOT_FOUND_MESSAGE = ChatMessage(
    type="text",
    content="I don't have that in the knowledge base - it may not be documented yet.",
    status="final",
)


class RAGAgentLLMOutput(BaseModel):
    """The LLM's answer and self-reported confidence, given retrieved
    passages. Citation metadata comes from the passages, not the LLM."""

    answer: str
    confidence: Literal["grounded", "insufficient"]


class RAGAgent:
    """Policy/FAQ sub-agent. Refuses immediately if the top search result
    is below the similarity threshold; otherwise asks the LLM to answer
    from the retrieved passages."""

    def __init__(self):
        instruction = load_prompt("rag_agent")
        self._sub_agent = BaseSubAgent(
            agent_name="rag_agent", instruction=instruction, output_schema=RAGAgentLLMOutput
        )

    async def handle_message(self, message: str) -> ChatMessage:
        hits = rag_service.search(message)
        if not hits or hits[0]["similarity"] < settings.rag_min_similarity:
            return _NOT_FOUND_MESSAGE

        prompt = self._build_prompt(message, hits)
        try:
            parsed = await self._sub_agent.run(prompt, user_id="rag_agent")
        except (LLMTransientError, LLMOutputValidationError, CircuitOpenError) as exc:
            logger.warning(f"RAG agent generation failed: {exc}")
            return UNAVAILABLE_MESSAGE

        if parsed.confidence == "insufficient":
            return _NOT_FOUND_MESSAGE

        # Only cite passages that cleared the relevance bar.
        relevant_hits = [h for h in hits if h["similarity"] >= settings.rag_min_similarity]
        citations = self._build_citations(relevant_hits)
        return ChatMessage(
            type="citation-answer",
            content=parsed.answer,
            citations=citations,
            status="final",
        )

    def _build_prompt(self, message: str, hits: list[dict]) -> str:
        passages = "\n\n".join(
            f"[Passage {i + 1} - {hit['document_title']}, {hit['section']}]\n{hit['text']}"
            for i, hit in enumerate(hits)
        )
        return f"Question: {message}\n\nRetrieved passages:\n{passages}"

    def _build_citations(self, hits: list[dict]) -> list[Citation]:
        # Dedup by (document, section).
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
                    snippet=self._extract_snippet(hit["text"]),
                )
            )
        return citations

    def _extract_snippet(self, indexed_text: str, max_chars: int = 480) -> str:
        """rag_service embeds each chunk as "{title} - {section}\\n{body}"
        (see ingest_document) - strip that prefix so the citation shows the
        actual source passage, not a repeat of the title/section already
        shown above it. Truncated to a readable preview length."""
        body = indexed_text.split("\n", 1)[1] if "\n" in indexed_text else indexed_text
        body = body.strip()
        if len(body) > max_chars:
            body = body[:max_chars].rsplit(" ", 1)[0] + "…"
        return body


rag_agent = RAGAgent()
