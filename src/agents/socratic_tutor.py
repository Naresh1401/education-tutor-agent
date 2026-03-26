"""
Socratic Tutor Agent — Guides students through Socratic questioning,
never providing direct answers. Uses RAG for curriculum-aligned guidance.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from src.knowledge.curriculum_loader import get_retriever

load_dotenv()

SOCRATIC_SYSTEM_PROMPT = """You are a Socratic tutor — an expert educator who NEVER gives direct answers.
Instead, you guide students to discover answers themselves through carefully crafted questions.

Your approach:
1. When a student asks a question, respond with a leading question that guides them toward the answer.
2. Break complex problems into smaller, manageable steps.
3. If the student is stuck, provide a hint in the form of another question.
4. Acknowledge correct reasoning and gently redirect incorrect reasoning.
5. Adapt your question difficulty based on the student's responses:
   - If they're struggling, ask simpler foundational questions.
   - If they're progressing well, ask deeper questions to extend understanding.
6. Track and address misconceptions — when you detect a misconception, ask questions
   that expose the flaw in reasoning rather than correcting it directly.

Relevant curriculum context:
{context}

Current student level assessment: {student_level}
Identified misconceptions so far: {misconceptions}

Guidelines:
- Be encouraging and patient.
- Use phrases like "What do you think would happen if...?", "Can you recall...?", "How might we approach...?"
- If the student gives a correct answer, affirm it and ask a follow-up to deepen understanding.
- Keep responses concise — one or two questions at a time.
"""


class TutorState(BaseModel):
    """Tracks the state of a Socratic tutoring session."""

    student_id: str = "anonymous"
    subject: str = ""
    topic: str = ""
    student_level: str = "intermediate"
    misconceptions: list[str] = Field(default_factory=list)
    question_count: int = 0
    correct_responses: int = 0
    conversation_history: list[dict] = Field(default_factory=list)


class SocraticTutor:
    """LangChain agent implementing the Socratic method for tutoring."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.7,
        )
        self.retriever = get_retriever({"k": 4})
        self.sessions: dict[str, TutorState] = {}

    def _get_or_create_session(self, student_id: str, subject: str = "", topic: str = "") -> TutorState:
        if student_id not in self.sessions:
            self.sessions[student_id] = TutorState(
                student_id=student_id, subject=subject, topic=topic
            )
        session = self.sessions[student_id]
        if subject:
            session.subject = subject
        if topic:
            session.topic = topic
        return session

    def _retrieve_context(self, query: str, subject: str = "", topic: str = "") -> str:
        """Retrieve relevant curriculum content for the current question."""
        search_query = query
        if subject:
            search_query = f"{subject} {topic} {query}" if topic else f"{subject} {query}"

        docs = self.retriever.invoke(search_query)
        if not docs:
            return "No specific curriculum context available."
        return "\n\n".join(doc.page_content for doc in docs[:3])

    def _assess_response(self, student_message: str, session: TutorState) -> str:
        """Dynamically assess student level based on their response quality."""
        session.question_count += 1
        word_count = len(student_message.split())

        if word_count < 5:
            return "beginner"

        technical_indicators = [
            "because", "therefore", "since", "implies", "given that",
            "formula", "equation", "theorem", "proof", "derive",
        ]
        technical_count = sum(1 for ind in technical_indicators if ind in student_message.lower())

        if technical_count >= 3:
            session.correct_responses += 1
            return "advanced"
        elif technical_count >= 1:
            session.correct_responses += 1
            return "intermediate"
        return "beginner"

    def _detect_misconceptions(self, student_message: str, context: str, session: TutorState) -> list[str]:
        """Use LLM to detect potential misconceptions in student's response."""
        if not session.conversation_history:
            return session.misconceptions

        detection_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze the student's response for misconceptions about {topic}.
            Curriculum context: {context}
            Return a JSON list of misconception strings, or an empty list if none detected.
            Only return the JSON list, nothing else."""),
            ("human", "{student_message}"),
        ])

        chain = detection_prompt | self.llm | StrOutputParser()
        try:
            result = chain.invoke({
                "topic": session.topic or session.subject,
                "context": context,
                "student_message": student_message,
            })
            import json
            new_misconceptions = json.loads(result)
            if isinstance(new_misconceptions, list):
                for m in new_misconceptions:
                    if m not in session.misconceptions:
                        session.misconceptions.append(m)
        except (json.JSONDecodeError, Exception):
            pass

        return session.misconceptions

    async def ask(
        self,
        student_message: str,
        student_id: str = "anonymous",
        subject: str = "",
        topic: str = "",
    ) -> dict:
        """Process a student message and return a Socratic response."""
        session = self._get_or_create_session(student_id, subject, topic)
        context = self._retrieve_context(student_message, session.subject, session.topic)
        session.student_level = self._assess_response(student_message, session)
        self._detect_misconceptions(student_message, context, session)

        prompt = ChatPromptTemplate.from_messages([
            ("system", SOCRATIC_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])

        history_messages = []
        for entry in session.conversation_history[-10:]:
            if entry["role"] == "student":
                history_messages.append(HumanMessage(content=entry["content"]))
            else:
                history_messages.append(AIMessage(content=entry["content"]))

        chain = prompt | self.llm | StrOutputParser()
        response = await chain.ainvoke({
            "context": context,
            "student_level": session.student_level,
            "misconceptions": ", ".join(session.misconceptions) if session.misconceptions else "None identified yet",
            "history": history_messages,
            "input": student_message,
        })

        session.conversation_history.append({"role": "student", "content": student_message})
        session.conversation_history.append({"role": "tutor", "content": response})

        return {
            "response": response,
            "student_level": session.student_level,
            "misconceptions": session.misconceptions,
            "question_count": session.question_count,
        }

    def get_session_state(self, student_id: str) -> Optional[dict]:
        """Return current session state for a student."""
        session = self.sessions.get(student_id)
        if not session:
            return None
        return session.model_dump()
