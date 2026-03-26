"""
Progress Tracker Agent — Tracks and analyzes student learning progress
with mastery scores, strength/weakness analysis, and learning velocity.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

load_dotenv()

PROGRESS_REPORT_PROMPT = """You are an educational analytics expert. Generate a comprehensive
progress report for a student based on the following data.

Student ID: {student_id}
Subject: {subject}

Topic Mastery Scores: {mastery_scores}
Strengths: {strengths}
Weaknesses: {weaknesses}
Total Study Sessions: {total_sessions}
Total Questions Answered: {total_questions}
Overall Accuracy: {overall_accuracy}%
Learning Velocity: {velocity} (topics mastered per week)
Time Spent Per Topic: {time_per_topic}
Recent Activity: {recent_activity}

Generate a report with:
1. **Overall Assessment**: Brief summary of the student's progress
2. **Strengths**: Topics the student excels at with specific observations
3. **Areas for Improvement**: Topics needing more work with actionable suggestions
4. **Learning Pace Analysis**: Whether the student is on track, ahead, or behind
5. **Recommendations**: 3-5 specific, prioritized next steps
6. **Encouragement**: A motivating note based on their progress

Keep the tone supportive and constructive."""


class TopicProgress(BaseModel):
    """Tracks progress for a single topic."""

    topic: str
    questions_attempted: int = 0
    questions_correct: int = 0
    mastery_score: float = 0.0
    time_spent_minutes: float = 0.0
    last_activity: Optional[str] = None
    score_history: list[float] = Field(default_factory=list)


class StudentProgress(BaseModel):
    """Complete progress record for a student."""

    student_id: str
    subject: str = ""
    topics: dict[str, TopicProgress] = Field(default_factory=dict)
    total_sessions: int = 0
    session_dates: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ProgressTracker:
    """Tracks and analyzes student learning progress."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.4,
        )
        self.students: dict[str, StudentProgress] = {}

    def _get_or_create_student(self, student_id: str, subject: str = "") -> StudentProgress:
        if student_id not in self.students:
            self.students[student_id] = StudentProgress(
                student_id=student_id, subject=subject
            )
        student = self.students[student_id]
        if subject:
            student.subject = subject
        return student

    def record_answer(
        self,
        student_id: str,
        topic: str,
        is_correct: bool,
        score: float = 1.0,
        time_spent: float = 0.0,
        subject: str = "",
    ) -> dict:
        """Record a student's answer and update mastery tracking."""
        student = self._get_or_create_student(student_id, subject)
        now = datetime.now().isoformat()

        if topic not in student.topics:
            student.topics[topic] = TopicProgress(topic=topic)

        tp = student.topics[topic]
        tp.questions_attempted += 1
        if is_correct:
            tp.questions_correct += 1
        tp.time_spent_minutes += time_spent
        tp.last_activity = now

        # Weighted mastery: recent performance weighs more
        old_score = tp.mastery_score
        alpha = 0.3  # learning rate for exponential moving average
        tp.mastery_score = alpha * score + (1 - alpha) * old_score
        tp.score_history.append(round(tp.mastery_score, 3))

        student.updated_at = now

        return {
            "topic": topic,
            "mastery_score": round(tp.mastery_score, 3),
            "questions_attempted": tp.questions_attempted,
            "accuracy": round(tp.questions_correct / tp.questions_attempted, 3),
        }

    def start_session(self, student_id: str, subject: str = "") -> dict:
        """Record the start of a study session."""
        student = self._get_or_create_student(student_id, subject)
        student.total_sessions += 1
        student.session_dates.append(datetime.now().isoformat())
        student.updated_at = datetime.now().isoformat()
        return {"session_number": student.total_sessions}

    def get_strengths_weaknesses(self, student_id: str) -> dict:
        """Analyze student's strengths and weaknesses across topics."""
        student = self.students.get(student_id)
        if not student:
            return {"strengths": [], "weaknesses": [], "neutral": []}

        strengths = []
        weaknesses = []
        neutral = []

        for topic, tp in student.topics.items():
            entry = {
                "topic": topic,
                "mastery": round(tp.mastery_score, 3),
                "accuracy": round(tp.questions_correct / tp.questions_attempted, 3)
                if tp.questions_attempted > 0
                else 0.0,
                "questions_attempted": tp.questions_attempted,
            }
            if tp.mastery_score >= 0.75:
                strengths.append(entry)
            elif tp.mastery_score < 0.45:
                weaknesses.append(entry)
            else:
                neutral.append(entry)

        strengths.sort(key=lambda x: x["mastery"], reverse=True)
        weaknesses.sort(key=lambda x: x["mastery"])

        return {"strengths": strengths, "weaknesses": weaknesses, "neutral": neutral}

    def get_learning_velocity(self, student_id: str) -> dict:
        """Estimate learning velocity: topics mastered per week."""
        student = self.students.get(student_id)
        if not student or not student.session_dates:
            return {"velocity": 0.0, "trend": "insufficient_data"}

        dates = sorted(student.session_dates)
        first = datetime.fromisoformat(dates[0])
        last = datetime.fromisoformat(dates[-1])
        weeks = max((last - first).days / 7.0, 1.0)

        mastered = sum(
            1 for tp in student.topics.values() if tp.mastery_score >= 0.75
        )
        velocity = mastered / weeks

        # Trend: compare recent vs overall velocity
        recent_cutoff = (datetime.now() - timedelta(days=14)).isoformat()
        recent_topics = [
            tp for tp in student.topics.values()
            if tp.last_activity and tp.last_activity >= recent_cutoff
        ]
        recent_mastered = sum(1 for tp in recent_topics if tp.mastery_score >= 0.75)

        if len(recent_topics) == 0:
            trend = "inactive"
        elif recent_mastered / max(len(recent_topics), 1) > mastered / max(len(student.topics), 1):
            trend = "accelerating"
        elif recent_mastered / max(len(recent_topics), 1) < mastered / max(len(student.topics), 1):
            trend = "slowing"
        else:
            trend = "steady"

        return {
            "velocity": round(velocity, 2),
            "topics_mastered": mastered,
            "total_topics": len(student.topics),
            "weeks_active": round(weeks, 1),
            "trend": trend,
        }

    def get_time_analytics(self, student_id: str) -> dict:
        """Get time-on-topic analytics."""
        student = self.students.get(student_id)
        if not student:
            return {"total_time": 0, "per_topic": {}}

        per_topic = {}
        total = 0
        for topic, tp in student.topics.items():
            per_topic[topic] = {
                "minutes": round(tp.time_spent_minutes, 1),
                "questions": tp.questions_attempted,
                "minutes_per_question": round(
                    tp.time_spent_minutes / tp.questions_attempted, 1
                )
                if tp.questions_attempted > 0
                else 0,
            }
            total += tp.time_spent_minutes

        return {"total_minutes": round(total, 1), "per_topic": per_topic}

    async def generate_report(self, student_id: str, subject: str = "") -> dict:
        """Generate a comprehensive AI-driven progress report."""
        student = self.students.get(student_id)
        if not student:
            return {"error": "Student not found"}

        sw = self.get_strengths_weaknesses(student_id)
        velocity = self.get_learning_velocity(student_id)
        time_analytics = self.get_time_analytics(student_id)

        total_q = sum(tp.questions_attempted for tp in student.topics.values())
        total_correct = sum(tp.questions_correct for tp in student.topics.values())
        accuracy = round(total_correct / total_q * 100, 1) if total_q > 0 else 0

        mastery_scores = {
            t: round(tp.mastery_score, 3) for t, tp in student.topics.items()
        }

        recent = sorted(
            student.topics.values(),
            key=lambda tp: tp.last_activity or "",
            reverse=True,
        )[:5]
        recent_activity = [
            {"topic": tp.topic, "last_active": tp.last_activity, "mastery": round(tp.mastery_score, 3)}
            for tp in recent
        ]

        prompt = ChatPromptTemplate.from_template(PROGRESS_REPORT_PROMPT)
        chain = prompt | self.llm | StrOutputParser()

        report_text = await chain.ainvoke({
            "student_id": student_id,
            "subject": subject or student.subject,
            "mastery_scores": str(mastery_scores),
            "strengths": str([s["topic"] for s in sw["strengths"]]),
            "weaknesses": str([w["topic"] for w in sw["weaknesses"]]),
            "total_sessions": student.total_sessions,
            "total_questions": total_q,
            "overall_accuracy": accuracy,
            "velocity": velocity["velocity"],
            "time_per_topic": str(time_analytics["per_topic"]),
            "recent_activity": str(recent_activity),
        })

        return {
            "student_id": student_id,
            "subject": subject or student.subject,
            "report": report_text,
            "mastery_scores": mastery_scores,
            "strengths_weaknesses": sw,
            "velocity": velocity,
            "time_analytics": time_analytics,
            "overall_accuracy": accuracy,
            "total_questions": total_q,
            "generated_at": datetime.now().isoformat(),
        }

    def get_all_progress(self, student_id: str) -> Optional[dict]:
        """Get raw progress data for a student."""
        student = self.students.get(student_id)
        if not student:
            return None
        return student.model_dump()
