# 🎓 AI-Powered Adaptive Education Tutor Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-green.svg)](https://langchain.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent tutoring system powered by LLM agents that delivers personalized, adaptive learning experiences. The system employs Socratic questioning, multi-level concept explanation, adaptive quiz generation, personalized learning paths, and comprehensive progress tracking — built with **LangChain**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                       │
│  ┌──────────┐ ┌───────────┐ ┌─────────┐ ┌───────────────┐  │
│  │ Tutoring │ │  Concept  │ │  Quiz   │ │   Progress    │  │
│  │   Chat   │ │ Explorer  │ │  Mode   │ │   Dashboard   │  │
│  └────┬─────┘ └─────┬─────┘ └────┬────┘ └───────┬───────┘  │
└───────┼──────────────┼───────────┼───────────────┼──────────┘
        │              │           │               │
┌───────▼──────────────▼───────────▼───────────────▼──────────┐
│                      FastAPI Backend                         │
│  /tutor/ask  /explain  /quiz/generate  /progress/{id}       │
└───────┬──────────────┬───────────┬───────────────┬──────────┘
        │              │           │               │
┌───────▼──────────────▼───────────▼───────────────▼──────────┐
│                     Agent Orchestration                      │
│  ┌──────────────┐ ┌────────────────┐ ┌───────────────────┐  │
│  │   Socratic   │ │    Concept     │ │   Quiz Generator  │  │
│  │    Tutor     │ │   Explainer    │ │   (Adaptive)      │  │
│  └──────┬───────┘ └───────┬────────┘ └────────┬──────────┘  │
│  ┌──────▼───────┐ ┌───────▼────────┐ ┌────────▼──────────┐  │
│  │  Learning    │ │   Progress     │ │   RAG Pipeline    │  │
│  │ Path Planner │ │   Tracker      │ │   (ChromaDB)      │  │
│  └──────────────┘ └────────────────┘ └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
        │                                          │
┌───────▼──────────────────────────────────────────▼──────────┐
│                    Knowledge Base (ChromaDB)                  │
│  ┌────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────────┐  │
│  │  Math  │ │ Science  │ │   CS    │ │     History      │  │
│  │Algebra │ │ Physics  │ │  DSA    │ │   World History  │  │
│  │Calculus│ │Chemistry │ │  Algo   │ │   US History     │  │
│  └────────┘ └──────────┘ └─────────┘ └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 🤔 Socratic Tutor Agent
- Never gives direct answers — guides students through leading questions
- Adapts question difficulty based on student responses
- Tracks and addresses misconceptions in real-time
- Uses RAG to pull relevant curriculum content for accurate guidance

### 📚 Multi-Level Concept Explainer
- **Beginner (ELI5)**: Simple analogies and everyday examples
- **Intermediate**: Standard explanations with worked examples
- **Advanced**: Formal definitions, proofs, and edge cases
- Auto-detects appropriate level from student's questions

### 📝 Adaptive Quiz Generator
- Multiple question types: MCQ, fill-in-blank, short answer, coding
- Difficulty adapts dynamically based on performance
- Generates distractors based on common misconceptions
- Provides detailed explanations for incorrect answers
- Tracks topic mastery scores

### 🗺️ Personalized Learning Path Planner
- Diagnostic assessment of current knowledge
- Maps prerequisite dependency graphs
- Suggests optimal topic ordering
- Adjusts pace based on quiz performance
- Recommends review topics when mastery drops

### 📊 Progress Tracker & Analytics
- Per-topic mastery scores with trend analysis
- Strength/weakness identification
- Time-on-topic analytics
- Learning velocity estimation
- Automated progress report generation

## Supported Subjects

| Subject | Topics |
|---------|--------|
| **Mathematics** | Algebra, Calculus, Linear Algebra, Statistics |
| **Computer Science** | Data Structures, Algorithms, OOP, Databases |
| **Science** | Physics, Chemistry, Biology |
| **History** | World History, US History, Ancient Civilizations |

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key

### Installation

```bash
git clone https://github.com/naresh-sampangi/education-tutor-agent.git
cd education-tutor-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Load Curriculum Data

```bash
python -m src.knowledge.sample_curriculum
python -m src.knowledge.curriculum_loader
```

### Run the API Server

```bash
make api
# or
uvicorn src.api.app:app --reload --port 8000
```

### Run the Dashboard

```bash
make dashboard
# or
streamlit run src/dashboard/app.py --server.port 8501
```

### Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tutor/ask` | Socratic tutoring session |
| POST | `/explain` | Concept explanation at chosen level |
| POST | `/quiz/generate` | Generate adaptive quiz |
| POST | `/quiz/evaluate` | Evaluate quiz answers |
| POST | `/learning-path` | Generate personalized learning path |
| GET | `/progress/{student_id}` | Get student progress report |
| GET | `/health` | Health check |

## Project Structure

```
education-tutor-agent/
├── src/
│   ├── agents/
│   │   ├── socratic_tutor.py       # Socratic questioning agent
│   │   ├── concept_explainer.py    # Multi-level explanations
│   │   ├── quiz_generator.py       # Adaptive quiz generation
│   │   ├── learning_path_planner.py# Learning path creation
│   │   └── progress_tracker.py     # Progress analytics
│   ├── knowledge/
│   │   ├── curriculum_loader.py    # ChromaDB ingestion
│   │   └── sample_curriculum.py    # Sample data generator
│   ├── api/
│   │   └── app.py                  # FastAPI backend
│   └── dashboard/
│       └── app.py                  # Streamlit frontend
├── data/curricula/                 # Curriculum text files
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

## Author

**Naresh Sampangi**

## License

This project is licensed under the MIT License.
