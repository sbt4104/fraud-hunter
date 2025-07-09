# Fraud Hunter

Fraud Hunter is a lightweight, modular system for detecting fraud using FastAPI, LangChain, and Qdrant.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/sbt4104/fraud-hunter.git
cd fraud-hunter
```

### 2. Create and activate a virtual environment

**On macOS/Linux:**
```bash
python -m venv fraud-hunter
source fraud-hunter/bin/activate
```

**On Windows:**
```bash
python -m venv fraud-hunter
fraud-hunter\Scripts\activate
```

### 3. Install dependencies

If you have a `requirements.txt` file:
```bash
pip install -r requirements.txt
```

Otherwise, install manually:
```bash
pip install fastapi uvicorn qdrant-client langchain langchain-openai langgraph python-dotenv jinja2 aiofiles pydantic
```

---

## create .env 

```bash
OPENAI_API_KEY=sk-your_openai_key

# Qdrant Configuration  
QDRANT_URL=http://localhost:6333

# Events API (mock for demo)
EVENTS_API_URL=http://localhost:8000/mock-events
```

Verify Qdrant is running:
```bash
curl http://localhost:6333/health
```

---

## Run Qdrant (Vector Database)

Start Qdrant using Docker Compose:
```bash
docker-compose up -d
```

Verify Qdrant is running:
```bash
curl http://localhost:6333/collections
```

---

## Start the Fraud Detection System

Ensure your `.env` file is configured if needed.

Run the system:
```bash
python run.py
```

By default, FastAPI will be available at: [http://localhost:8000](http://localhost:8000)

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
