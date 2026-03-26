"""
FastAPI Backend — REST API for the AI Education Tutor Agent.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.agents.socratic_tutor import SocraticTutor
from src.agents.concept_explainer import ConceptExplainer
from src.agents.quiz_generator import QuizGenerator, QuizConfig
from src.agents.learning_path_planner import LearningPathPlanner, LearningPathConfig
from src.agents.progress_tracker import ProgressTracker

load_dotenv()

# Shared agent instances
tutor: SocraticTutor
explainer: ConceptExplainer
quiz_gen: QuizGenerator
path_planner: LearningPathPlanner
progress: ProgressTracker


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tutor, explainer, quiz_gen, path_planner, progress
    tutor = SocraticTutor()
    explainer = ConceptExplainer()
    quiz_gen = QuizGenerator()
    path_planner = LearningPathPlanner()
    progress = ProgressTracker()
    yield


app = FastAPI(
    title="AI Education Tutor Agent",
    description="Intelligent tutoring system with Socratic questioning, adaptive quizzes, and personalized learning paths.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Request / Response Models ──────────────────────────────────────


class TutorRequest(BaseModel):
    message: str
    student_id: str = "anonymous"
    subject: str = ""
    topic: str = ""


class ExplainRequest(BaseModel):
    concept: str
    subject: str = ""
    level: Optional[str] = None  # beginner, intermediate, advanced


class QuizGenerateRequest(BaseModel):
    subject: str
    topic: str
    num_questions: int = 5
    difficulty: int = 2
    question_types: list[str] = Field(
        default_factory=lambda: ["multiple_choice", "short_answer"]
    )
    student_id: str = "anonymous"
    adaptive: bool = True


class QuizEvaluateRequest(BaseModel):
    question: dict
    student_answer: str
    student_id: str = "anonymous"


class LearningPathRequest(BaseModel):
    student_id: str = "anonymous"
    subject: str
    target_topic: str
    current_knowledge: dict[str, float] = Field(default_factory=dict)


# ── Endpoints ──────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "education-tutor-agent"}


@app.post("/tutor/ask")
async def tutor_ask(request: TutorRequest):
    """Socratic tutoring session — responds with guiding questions."""
    try:
        result = await tutor.ask(
            student_message=request.message,
            student_id=request.student_id,
            subject=request.subject,
            topic=request.topic,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain")
async def explain_concept(request: ExplainRequest):
    """Explain a concept at the chosen (or auto-detected) level."""
    try:
        result = await explainer.explain(
            concept=request.concept,
            subject=request.subject,
            level=request.level,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quiz/generate")
async def generate_quiz(request: QuizGenerateRequest):
    """Generate an adaptive quiz for a topic."""
    try:
        config = QuizConfig(
            subject=request.subject,
            topic=request.topic,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            question_types=request.question_types,
        )
        result = await quiz_gen.generate_quiz(
            config=config,
            student_id=request.student_id,
            adaptive=request.adaptive,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quiz/evaluate")
async def evaluate_quiz(request: QuizEvaluateRequest):
    """Evaluate a student's quiz answer."""
    try:
        result = await quiz_gen.evaluate_answer(
            question=request.question,
            student_answer=request.student_answer,
            student_id=request.student_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learning-path")
async def generate_learning_path(request: LearningPathRequest):
    """Generate a personalized learning path."""
    try:
        config = LearningPathConfig(
            student_id=request.student_id,
            subject=request.subject,
            target_topic=request.target_topic,
            current_knowledge=request.current_knowledge,
        )
        result = await path_planner.create_learning_path(config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/progress/{student_id}")
async def get_progress(student_id: str, subject: str = ""):
    """Get comprehensive progress report for a student."""
    try:
        report = await progress.generate_report(student_id, subject)
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
