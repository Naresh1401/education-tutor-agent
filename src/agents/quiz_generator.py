"""
Adaptive Quiz Generator Agent — Generates quizzes with multiple question types,
adaptive difficulty, misconception-based distractors, and mastery tracking.
"""

import os
import json
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from src.knowledge.curriculum_loader import get_retriever

load_dotenv()

QUIZ_GENERATION_PROMPT = """You are an expert quiz generator for educational assessments.
Generate a quiz based on the following parameters.

Subject: {subject}
Topic: {topic}
Difficulty: {difficulty} (scale: 1=easy, 2=medium, 3=hard, 4=expert)
Number of questions: {num_questions}
Question types requested: {question_types}

Relevant curriculum material:
{context}

Student's known weaknesses: {weaknesses}

Generate questions as a JSON array. Each question object must have:
- "id": sequential integer
- "type": one of "multiple_choice", "fill_in_blank", "short_answer", "coding"
- "question": the question text
- "difficulty": integer 1-4
- "topic": specific sub-topic
- "options": array of 4 options (for multiple_choice only, null otherwise)
- "correct_answer": the correct answer
- "explanation": detailed explanation of why the answer is correct
- "misconception_note": common misconception this question targets (if any)
- "hints": array of 1-2 progressive hints

For multiple choice, generate distractors based on common misconceptions.
For coding questions, include a function signature and expected behavior.

Return ONLY the JSON array, no other text."""

EVALUATION_PROMPT = """Evaluate the student's answer to the following question.

Question: {question}
Question Type: {question_type}
Correct Answer: {correct_answer}
Student's Answer: {student_answer}

Evaluate and return a JSON object with:
- "is_correct": boolean
- "score": float between 0.0 and 1.0 (partial credit for partially correct answers)
- "feedback": detailed feedback explaining what was right/wrong
- "misconception": any misconception detected in the answer (null if none)
- "suggestion": what to study or review

Return ONLY the JSON object."""


class QuizConfig(BaseModel):
    subject: str
    topic: str
    num_questions: int = 5
    difficulty: int = 2  # 1-4
    question_types: list[str] = Field(
        default_factory=lambda: ["multiple_choice", "short_answer"]
    )


class StudentMastery(BaseModel):
    """Tracks per-topic mastery for a student."""

    student_id: str
    topic_scores: dict[str, float] = Field(default_factory=dict)  # topic -> score [0,1]
    total_questions: dict[str, int] = Field(default_factory=dict)
    correct_answers: dict[str, int] = Field(default_factory=dict)
    weaknesses: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)


class QuizGenerator:
    """Generates adaptive quizzes with mastery tracking."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.6,
        )
        self.retriever = get_retriever({"k": 4})
        self.student_mastery: dict[str, StudentMastery] = {}

    def _get_mastery(self, student_id: str) -> StudentMastery:
        if student_id not in self.student_mastery:
            self.student_mastery[student_id] = StudentMastery(student_id=student_id)
        return self.student_mastery[student_id]

    def _adaptive_difficulty(self, student_id: str, topic: str) -> int:
        """Calculate difficulty based on student's past performance on this topic."""
        mastery = self._get_mastery(student_id)
        score = mastery.topic_scores.get(topic, 0.5)
        if score >= 0.85:
            return 4
        elif score >= 0.7:
            return 3
        elif score >= 0.4:
            return 2
        return 1

    def _retrieve_context(self, subject: str, topic: str) -> str:
        query = f"{subject} {topic}"
        docs = self.retriever.invoke(query)
        if not docs:
            return "No specific curriculum context found."
        return "\n\n".join(doc.page_content for doc in docs[:3])

    async def generate_quiz(
        self,
        config: QuizConfig,
        student_id: str = "anonymous",
        adaptive: bool = True,
    ) -> dict:
        """Generate a quiz with optional adaptive difficulty."""
        difficulty = config.difficulty
        if adaptive:
            difficulty = self._adaptive_difficulty(student_id, config.topic)

        mastery = self._get_mastery(student_id)
        context = self._retrieve_context(config.subject, config.topic)

        prompt = ChatPromptTemplate.from_template(QUIZ_GENERATION_PROMPT)
        chain = prompt | self.llm | StrOutputParser()

        result = await chain.ainvoke({
            "subject": config.subject,
            "topic": config.topic,
            "difficulty": difficulty,
            "num_questions": config.num_questions,
            "question_types": ", ".join(config.question_types),
            "context": context,
            "weaknesses": ", ".join(mastery.weaknesses) if mastery.weaknesses else "None identified",
        })

        try:
            questions = json.loads(result)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                questions = json.loads(result[start:end])
            else:
                questions = []

        return {
            "quiz_id": f"{student_id}_{config.topic}_{config.difficulty}",
            "subject": config.subject,
            "topic": config.topic,
            "difficulty": difficulty,
            "num_questions": len(questions),
            "questions": questions,
        }

    async def evaluate_answer(
        self,
        question: dict,
        student_answer: str,
        student_id: str = "anonymous",
    ) -> dict:
        """Evaluate a student's answer and update mastery tracking."""
        prompt = ChatPromptTemplate.from_template(EVALUATION_PROMPT)
        chain = prompt | self.llm | StrOutputParser()

        result = await chain.ainvoke({
            "question": question.get("question", ""),
            "question_type": question.get("type", "short_answer"),
            "correct_answer": question.get("correct_answer", ""),
            "student_answer": student_answer,
        })

        try:
            evaluation = json.loads(result)
        except json.JSONDecodeError:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                evaluation = json.loads(result[start:end])
            else:
                evaluation = {
                    "is_correct": False,
                    "score": 0.0,
                    "feedback": "Unable to evaluate response.",
                    "misconception": None,
                    "suggestion": "Please try again.",
                }

        # Update mastery
        topic = question.get("topic", "general")
        mastery = self._get_mastery(student_id)
        mastery.total_questions[topic] = mastery.total_questions.get(topic, 0) + 1
        if evaluation.get("is_correct", False):
            mastery.correct_answers[topic] = mastery.correct_answers.get(topic, 0) + 1

        total = mastery.total_questions[topic]
        correct = mastery.correct_answers.get(topic, 0)
        mastery.topic_scores[topic] = correct / total if total > 0 else 0.0

        if evaluation.get("misconception"):
            misconception = evaluation["misconception"]
            if misconception not in mastery.misconceptions:
                mastery.misconceptions.append(misconception)

        if mastery.topic_scores[topic] < 0.5 and topic not in mastery.weaknesses:
            mastery.weaknesses.append(topic)
        elif mastery.topic_scores[topic] >= 0.7 and topic in mastery.weaknesses:
            mastery.weaknesses.remove(topic)

        return {
            **evaluation,
            "topic": topic,
            "mastery_score": mastery.topic_scores[topic],
            "total_attempted": total,
        }

    def get_mastery_report(self, student_id: str) -> Optional[dict]:
        """Get mastery report for a student."""
        mastery = self.student_mastery.get(student_id)
        if not mastery:
            return None
        return mastery.model_dump()
