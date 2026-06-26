# Doctor Appointment Booking AI – Backend

A **FastAPI** backend that powers a voice‑AI receptionist for **Dr. John Smith**'s clinic.  It combines:

* **SQLModel / SQLite** – stores patients and appointments.
* **LangChain + ChromaDB** – Retrieval‑Augmented Generation (RAG) over a static knowledge‑base (`clinic_knowledge.md`).
* **Voice‑AI webhook endpoints** – ready to be called by Vapi.ai, Bland.ai, or any similar service.

---

## 📂 Project Layout
```
appointment_ai/
├─ app/
│  ├─ __init__.py
│  ├─ main.py                # FastAPI entry point
│  ├─ config/
│  │   ├─ __init__.py
│  │   ├─ settings.py        # pydantic Settings (loads .env)
│  │   └─ system_prompt.txt # Prompt given to the voice LLM
│  ├─ database/
│  │   ├─ __init__.py
│  │   ├─ models.py          # Patient & Appointment ORM models
│  │   └─ session.py         # Engine & Session factory
│  ├─ rag/
│  │   ├─ __init__.py
│  │   ├─ loader.py          # Load & chunk clinic_knowledge.md
│  │   ├─ vectorstore.py     # Chroma wrapper + embedding model
│  │   └─ queries.py         # Public ``get_clinic_answer`` function
│  └─ api/
│      └─ routes/
│          ├─ __init__.py
│          ├─ trigger_call.py   # POST /api/trigger‑call (outbound voice call)
│          ├─ voice_query.py    # POST /api/webhook/voice‑query
│          ├─ availability.py   # POST /api/webhook/check‑availability
│          └─ booking.py        # POST /api/webhook/create‑booking
├─ clinic_knowledge.md      # Static markdown knowledge base (doctor info, fees, policies)
├─ .env.example             # Example environment variables
├─ requirements.txt
└─ README.md                # You are reading it! 🎉
```

---

## 🛠️ Prerequisites
* **Python ≥ 3.9**
* **Git** (optional – the repo is already on disk)
* Access to a voice‑AI provider (Vapi.ai, Bland.ai, etc.) and its API key.

---

## 🚀 Quick‑Start (local development)
```bash
# 1. Clone / navigate to the project directory (already done for you)
cd /path/to/appointment_ai

# 2. Create a virtual environment and activate it
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate   # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example env file and fill in your secrets
cp .env.example .env
# Edit .env – add VAPI_API_KEY, optional OPENAI_API_KEY, etc.

# 5. Populate the vector store (runs automatically on startup, but you can do it now)
python -m app.rag.loader

# 6. Launch the FastAPI server (hot‑reload enabled for dev)
uvicorn app.main:app --reload
```
The API will be reachable at `http://127.0.0.1:8000`.

---

## 📚 API Reference
| Endpoint | Method | Body | Description |
|---|---|---|---|
| `/api/trigger‑call` | **POST** | `{ "name": "Jane Doe", "phone_number": "+15551234567" }` | Starts an outbound call via the configured voice‑AI provider. Returns the provider's `call_id`. |
| `/api/webhook/voice‑query` | **POST** | `{ "question": "What are your clinic hours?" }` | Runs a similarity search on the knowledge base and returns the best answer. |
| `/api/webhook/check‑availability` | **POST** | `{ "desired_time": "2026-07-01T14:00:00" }` | Returns `{ "available": true }` if no pending/confirmed appointment exists at that ISO‑8601 timestamp. |
| `/api/webhook/create‑booking` | **POST** | `{ "name": "Jane Doe", "phone_number": "+15551234567", "desired_time": "2026-07-01T14:00:00" }` | Creates a patient (if needed) and a confirmed appointment. Returns the new appointment ID. |
| `/health` | **GET** | – | Simple health‑check, returns `{ "status": "healthy" }`. |

All responses follow the pattern `{ "success": true, "data": {...}, "error": null }` or raise appropriate HTTP errors.

---

## 🔧 Configuration Details
* **`.env` variables** – see `.env.example`.
* **Vector store path** – controlled by `CHROMA_DB_PATH` (defaults to `./vectorstore.db`).
* **Embedding model** – `sentence‑transformers/all‑MiniLM‑L6‑v2` (CPU‑friendly).  Swap the model name in `app/rag/vectorstore.py` if you need a different one.
* **CORS** – open to all origins in dev (`*`).  Tighten in production.

---

## 🧪 Testing the Endpoints (cURL examples)
```bash
# Trigger a call (replace the API key in .env first)
curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"Alice","phone_number":"+15551234567"}' \
     http://127.0.0.1:8000/api/trigger-call

# Ask a question via the RAG webhook
curl -X POST -H "Content-Type: application/json" \
     -d '{"question":"Do you accept Aetna insurance?"}' \
     http://127.0.0.1:8000/api/webhook/voice-query

# Check slot availability
curl -X POST -H "Content-Type: application/json" \
     -d '{"desired_time":"2026-07-01T14:00:00"}' \
     http://127.0.0.1:8000/api/webhook/check-availability

# Create a booking (after confirming the slot is free)
curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"Alice","phone_number":"+15551234567","desired_time":"2026-07-01T14:00:00"}' \
     http://127.0.0.1:8000/api/webhook/create-booking
```

---

## 📦 Production Tips
* **Run behind a proper ASGI server** – e.g. `uvicorn app.main:app --workers 4` or **Gunicorn** with `uvicorn.workers.UvicornWorker`.
* **TLS / HTTPS** – terminate TLS at a reverse proxy (NGINX, Traefik) before exposing the API.
* **Database backups** – the SQLite file (`appointments.db`) should be backed up regularly or swapped for Postgres/MySQL in production.
* **Rate limiting / auth** – add an API‑key or OAuth layer to protect the webhook endpoints from abuse.
* **Monitoring** – integrate Prometheus metrics (`fastapi[all]` includes a `/metrics` endpoint) and log aggregation.

---

## 🙋‍♀️ Need Help?
Feel free to open an issue or contact the maintainer.  The code is deliberately lightweight and easy to extend – add more FAQ documents, swap in a better embedding model, or enrich the booking workflow with reminders and SMS notifications.

Happy coding! 🚀