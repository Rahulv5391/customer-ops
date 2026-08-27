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
    """What the LLM actually decides, given passages the agent already
    retrieved deterministically. Citation metadata (document_title,
    version, source_updated_at, section) is never asked of the LLM - it
    comes straight from the retrieved chunks themselves, so a citation can
    never be something the model invented (Architecture.md §5)."""

    answer: str
    confidence: Literal["grounded", "insufficient"]


class RAGAgent:
    """Policy/FAQ sub-agent (Architecture.md §5). Always direct-execute -
    read-only by nature, no propose/confirm needed.

    Similarity-threshold refusal lives here, not in rag_service: a
    below-threshold (or empty) retrieval result short-circuits to a
    deterministic refusal without even calling the LLM - cheaper, and
    guarantees "not found" never depends on the model's cooperation. A
    retrieval that clears the threshold still goes to the LLM, which can
    independently report `confidence="insufficient"` if the passages don't
    actually answer what was asked - catching a near-miss the raw
    similarity score alone wouldn't.
    """

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

        # Only cite passages that actually cleared the relevance bar - the
        # rest of top_k exists to give the LLM context, not to be claimed
        # as a source for the answer it wrote.
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
        # Dedup by (document, section) - multiple chunks can point at the
        # same section if the LLM retrieved overlapping passages.
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
                )
            )
        return citations


rag_agent = RAGAgent()
