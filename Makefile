.PHONY: install api dashboard load-data docker-up docker-down clean

install:
	pip install -r requirements.txt

load-data:
	python -m src.knowledge.sample_curriculum
	python -m src.knowledge.curriculum_loader

api:
	uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

dashboard:
	streamlit run src/dashboard/app.py --server.port 8501

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf data/chroma_db
