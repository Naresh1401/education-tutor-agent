"""
Learning Path Planner Agent — Creates personalized learning paths with
prerequisite mapping, diagnostic assessment, and adaptive pacing.
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

# Prerequisite dependency graphs per subject
PREREQUISITE_GRAPH = {
    "math": {
        "arithmetic": [],
        "algebra": ["arithmetic"],
        "geometry": ["arithmetic"],
        "trigonometry": ["algebra", "geometry"],
        "precalculus": ["algebra", "trigonometry"],
        "calculus": ["precalculus"],
        "linear_algebra": ["algebra"],
        "statistics": ["algebra"],
        "differential_equations": ["calculus", "linear_algebra"],
    },
    "cs": {
        "programming_basics": [],
        "data_types": ["programming_basics"],
        "control_flow": ["programming_basics"],
        "functions": ["control_flow"],
        "oop": ["functions", "data_types"],
        "arrays_strings": ["data_types", "control_flow"],
        "linked_lists": ["arrays_strings", "oop"],
        "stacks_queues": ["linked_lists"],
        "trees": ["stacks_queues"],
        "graphs": ["trees"],
        "sorting": ["arrays_strings", "functions"],
        "searching": ["sorting"],
        "dynamic_programming": ["functions", "arrays_strings"],
        "algorithms": ["sorting", "searching", "graphs", "dynamic_programming"],
    },
    "science": {
        "measurement": [],
        "kinematics": ["measurement"],
        "forces": ["kinematics"],
        "energy": ["forces"],
        "momentum": ["forces"],
        "thermodynamics": ["energy"],
        "waves": ["energy"],
        "electrostatics": ["forces"],
        "circuits": ["electrostatics"],
        "electromagnetism": ["circuits", "waves"],
        "atomic_structure": ["measurement"],
        "chemical_bonding": ["atomic_structure"],
        "reactions": ["chemical_bonding"],
        "equilibrium": ["reactions"],
    },
    "history": {
        "ancient_civilizations": [],
        "classical_era": ["ancient_civilizations"],
        "medieval_period": ["classical_era"],
        "renaissance": ["medieval_period"],
        "age_of_exploration": ["renaissance"],
        "enlightenment": ["renaissance"],
        "revolutions": ["enlightenment"],
        "industrial_revolution": ["revolutions"],
        "modern_era": ["industrial_revolution"],
    },
}

DIAGNOSTIC_PROMPT = """You are an educational diagnostician. Generate {num_questions} diagnostic
questions to assess a student's current knowledge level in {subject}, specifically around {topic}.

Questions should range from foundational to advanced to pinpoint where the student's
understanding begins to break down.

Return a JSON array of objects with:
- "id": sequential integer
- "question": the diagnostic question
- "difficulty": integer 1-4
- "prerequisite_topic": which prerequisite topic this tests
- "correct_answer": brief correct answer

Return ONLY the JSON array."""

LEARNING_PATH_PROMPT = """You are an expert curriculum designer. Create a personalized learning
path for a student based on their diagnostic results.

Subject: {subject}
Target topic: {target_topic}
Diagnostic results: {diagnostic_results}
Known prerequisites: {prerequisites}
Current mastery levels: {mastery_levels}
Available topics: {available_topics}

Create an optimal learning path as a JSON object with:
- "path": ordered array of topic objects, each containing:
  - "topic": topic name
  - "priority": "required" | "recommended" | "optional"
  - "estimated_hours": float
  - "reason": why this topic is in the path
  - "learning_objectives": array of 2-3 specific objectives
- "total_estimated_hours": float
- "recommendations": array of general study recommendations
- "review_topics": array of topics that should be periodically reviewed

Return ONLY the JSON object."""


class LearningPathConfig(BaseModel):
    student_id: str = "anonymous"
    subject: str
    target_topic: str
    current_knowledge: dict[str, float] = Field(default_factory=dict)  # topic -> mastery [0,1]


class LearningPathPlanner:
    """Creates personalized learning paths with prerequisite awareness."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.4,
        )
        self.retriever = get_retriever({"k": 3})

    def _get_prerequisites(self, subject: str, topic: str) -> list[str]:
        """Recursively resolve all prerequisites for a topic."""
        graph = PREREQUISITE_GRAPH.get(subject, {})
        if topic not in graph:
            return []

        visited = set()
        result = []

        def dfs(t: str):
            if t in visited:
                return
            visited.add(t)
            for prereq in graph.get(t, []):
                dfs(prereq)
                if prereq not in result:
                    result.append(prereq)

        dfs(topic)
        return result

    def _find_gaps(
        self, prerequisites: list[str], current_knowledge: dict[str, float], threshold: float = 0.6
    ) -> list[str]:
        """Identify prerequisite topics where mastery is below threshold."""
        gaps = []
        for topic in prerequisites:
            mastery = current_knowledge.get(topic, 0.0)
            if mastery < threshold:
                gaps.append(topic)
        return gaps

    async def generate_diagnostic(
        self, subject: str, topic: str, num_questions: int = 5
    ) -> list[dict]:
        """Generate diagnostic questions to assess current knowledge."""
        prompt = ChatPromptTemplate.from_template(DIAGNOSTIC_PROMPT)
        chain = prompt | self.llm | StrOutputParser()

        result = await chain.ainvoke({
            "subject": subject,
            "topic": topic,
            "num_questions": num_questions,
        })

        try:
            questions = json.loads(result)
        except json.JSONDecodeError:
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                questions = json.loads(result[start:end])
            else:
                questions = []

        return questions

    async def create_learning_path(self, config: LearningPathConfig) -> dict:
        """Create a personalized learning path based on prerequisites and mastery."""
        prerequisites = self._get_prerequisites(config.subject, config.target_topic)
        gaps = self._find_gaps(prerequisites, config.current_knowledge)

        graph = PREREQUISITE_GRAPH.get(config.subject, {})
        available_topics = list(graph.keys())

        prompt = ChatPromptTemplate.from_template(LEARNING_PATH_PROMPT)
        chain = prompt | self.llm | StrOutputParser()

        result = await chain.ainvoke({
            "subject": config.subject,
            "target_topic": config.target_topic,
            "diagnostic_results": json.dumps(gaps),
            "prerequisites": json.dumps(prerequisites),
            "mastery_levels": json.dumps(config.current_knowledge),
            "available_topics": json.dumps(available_topics),
        })

        try:
            learning_path = json.loads(result)
        except json.JSONDecodeError:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                learning_path = json.loads(result[start:end])
            else:
                learning_path = {
                    "path": [{"topic": t, "priority": "required", "estimated_hours": 2.0,
                              "reason": "Gap identified", "learning_objectives": []}
                             for t in gaps],
                    "total_estimated_hours": len(gaps) * 2.0,
                    "recommendations": ["Focus on foundational topics first."],
                    "review_topics": [],
                }

        return {
            "student_id": config.student_id,
            "subject": config.subject,
            "target_topic": config.target_topic,
            "prerequisites": prerequisites,
            "gaps": gaps,
            "learning_path": learning_path,
        }

    def get_prerequisite_graph(self, subject: str) -> dict:
        """Return the prerequisite dependency graph for a subject."""
        return PREREQUISITE_GRAPH.get(subject, {})

    def get_topic_order(self, subject: str) -> list[str]:
        """Return a topologically sorted list of topics for a subject."""
        graph = PREREQUISITE_GRAPH.get(subject, {})
        visited = set()
        order = []

        def topo_sort(topic: str):
            if topic in visited:
                return
            visited.add(topic)
            for prereq in graph.get(topic, []):
                topo_sort(prereq)
            order.append(topic)

        for topic in graph:
            topo_sort(topic)

        return order
