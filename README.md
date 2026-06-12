# Adverse Media Screening Copilot

A production-grade, multi-agent AI system that screens entities (companies/persons) against adverse media. Optimised for on-premises deployment on **AMD MI300X** (ROCm support).

## Architecture

The system uses a 6-agent pipeline:
1. **Entity Resolver**: Fuzzy matching and alias expansion (`RapidFuzz`).
2. **Media Retrieval**: Vector search across a custom dataset (`SentenceTransformers` + `FAISS` GPU).
3. **Relevance Scorer**: Normalisation and exponential recency decay.
4. **Risk Analyst**: Weighted formula based on relevance, severity, frequency, and recency.
5. **Explainability**: Keyword extraction (`KeyBERT` / rules) and automated summaries (optional `Ollama` support).
6. **Decision**: Final verdict, confidence score, and JSONL audit logging.

## Tech Stack
- **Backend**: Python 3.10+, FastAPI, PyTorch (ROCm), SentenceTransformers, FAISS
- **Frontend**: React 18, Vite, Tailwind CSS v3, Recharts
- **Dataset**: Auto-generated synthetic adverse media dataset (200 records, 9 risk categories)

## Setup & Installation

1. Make the setup script executable and run it:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   *Note: This script installs PyTorch with ROCm 6.2 support by default.*

2. (Optional) Configure `backend/.env`
   - Set `OLLAMA_ENABLED=true` if you have a local Ollama instance running.
   - Adjust scoring weights or match thresholds.

## 🚀 How to Run the App

After completing the **Setup & Installation** above, you need to run both the backend API and the frontend UI. 

You will need **two separate terminals**.

### Step 1: Start the FastAPI Backend
Open your first terminal, navigate to the project root, and run:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*The backend API will be available at http://localhost:8000*

### Step 2: Start the React Frontend
Open your second terminal, navigate to the project root, and run:
```bash
cd frontend
npm run dev
```
*The frontend UI will be accessible at **http://localhost:8501***

## Usage
1. Enter an entity name (e.g., `Nexum Capital Partners`, `Viktor Dragan`, `Clean Corp`).
2. The UI will display a comprehensive dashboard including:
   - **Risk Gauge**: 0-100 score + Category
   - **Explainability**: Executive summary and key risk factors
   - **Timeline**: Distribution of adverse media over time
   - **Articles List**: Expandable list with keyword highlighting
   - **Human Review**: Analyst decision buttons that append to an audit log

## GPU Support (AMD ROCm)
- **SentenceTransformers** automatically detects and uses the ROCm device (exised as `cuda` via PyTorch HIP).
- **FAISS**: The backend attempts to load `faiss-gpu`. If not available (requires custom ROCm build), it gracefully falls back to CPU indexing.
- Device detection is surfaced in the UI footer.
