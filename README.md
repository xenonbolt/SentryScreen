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

#### Running the UI on a Remote Machine
If the backend is hosted remotely (e.g. on a Jupyter Notebook proxy) and you want to run the React frontend on your local PC, you can inject the backend URL and your Jupyter Authentication Token via the command line to bypass the login wall.

**Linux / macOS:**
```bash
VITE_API_BASE="https://notebooks.amd.com/your-workspace-id/proxy/8000/api" \
VITE_JUPYTER_TOKEN="your_jupyter_token_here" \
npm run dev
```
**Windows (PowerShell):**
```powershell
$env:VITE_API_BASE="https://notebooks.amd.com/your-workspace-id/proxy/8000/api"; $env:VITE_JUPYTER_TOKEN="your_jupyter_token_here"; npm run dev
```

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

streamlit run streamlit_app.py --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false

jupyter server list

VITE_API_BASE="base_jupyter_url" \
VITE_JUPYTER_TOKEN="access_token" \
npm run dev