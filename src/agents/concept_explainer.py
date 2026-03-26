"""
Concept Explainer Agent — Explains concepts at multiple difficulty levels,
from ELI5 to advanced formal definitions. Auto-detects appropriate level.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from src.knowledge.curriculum_loader import get_retriever

load_dotenv()

LEVEL_PROMPTS = {
    "beginner": """Explain the following concept as if you're talking to a 10-year-old (ELI5 style).
Use simple everyday analogies, relatable examples, and avoid jargon.
If you must use a technical term, immediately define it in simple words.
Use comparisons to everyday objects and experiences.

Concept: {concept}
Subject: {subject}

Relevant curriculum material:
{context}

Provide your explanation with:
1. A simple one-line summary
2. An analogy from everyday life
3. A step-by-step explanation using the analogy
4. A "Try this" activity or thought experiment""",

    "intermediate": """Explain the following concept at a standard educational level suitable for a
high school or early college student. Include worked examples and clear definitions.

Concept: {concept}
Subject: {subject}

Relevant curriculum material:
{context}

Provide your explanation with:
1. Clear definition
2. Key properties or characteristics
3. One or two worked examples with step-by-step solutions
4. Common pitfalls or mistakes to avoid
5. How this concept connects to related topics""",

    "advanced": """Explain the following concept at an advanced level suitable for an upper-level
undergraduate or graduate student. Include formal definitions, proofs where applicable,
edge cases, and connections to broader theory.

Concept: {concept}
Subject: {subject}

Relevant curriculum material:
{context}

Provide your explanation with:
1. Formal mathematical or technical definition
2. Proof or derivation (if applicable)
3. Edge cases and boundary conditions
4. Connections to more advanced topics
5. Historical context or notable applications
6. Open problems or current research directions (if relevant)""",
}

LEVEL_DETECTION_PROMPT = """Analyze the following student question and determine the appropriate
explanation level. Consider vocabulary complexity, specificity, and implied knowledge.

Question: {question}

Respond with exactly one of: beginner, intermediate, advanced

Your assessment:"""


class ExplanationRequest(BaseModel):
    concept: str
    subject: str = ""
    level: Optional[str] = None  # beginner, intermediate, advanced, or None for auto-detect


class ConceptExplainer:
    """Explains concepts at multiple levels with auto-detection."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.5,
        )
        self.retriever = get_retriever({"k": 4})

    def _retrieve_context(self, concept: str, subject: str = "") -> str:
        query = f"{subject} {concept}" if subject else concept
        docs = self.retriever.invoke(query)
        if not docs:
            return "No specific curriculum context found."
        return "\n\n".join(doc.page_content for doc in docs[:3])

    async def detect_level(self, question: str) -> str:
        """Auto-detect the appropriate explanation level from a student's question."""
        prompt = ChatPromptTemplate.from_template(LEVEL_DETECTION_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({"question": question})
        level = result.strip().lower()
        if level not in LEVEL_PROMPTS:
            return "intermediate"
        return level

    async def explain(
        self,
        concept: str,
        subject: str = "",
        level: Optional[str] = None,
    ) -> dict:
        """Generate a concept explanation at the specified or auto-detected level."""
        if level is None or level not in LEVEL_PROMPTS:
            level = await self.detect_level(concept)

        context = self._retrieve_context(concept, subject)
        template = LEVEL_PROMPTS[level]
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        explanation = await chain.ainvoke({
            "concept": concept,
            "subject": subject or "General",
            "context": context,
        })

        return {
            "concept": concept,
            "subject": subject,
            "level": level,
            "explanation": explanation,
        }

    async def explain_all_levels(self, concept: str, subject: str = "") -> dict:
        """Generate explanations at all three levels for comparison."""
        results = {}
        for level in ["beginner", "intermediate", "advanced"]:
            result = await self.explain(concept, subject, level)
            results[level] = result["explanation"]

        return {
            "concept": concept,
            "subject": subject,
            "explanations": results,
        }
