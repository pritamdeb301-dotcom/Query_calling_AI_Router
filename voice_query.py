"""Webhook that receives free‑form patient questions and answers them via the RAG system.

The external voice‑AI platform will POST a JSON payload like:

```json
{ "question": "What are your clinic hours?" }
```

The endpoint returns:
```json
{ "answer": "Our clinic is open Monday‑Friday 9 am‑6 pm." }
```
"""
import requests
from fastapi import BackgroundTasks
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag.queries import get_clinic_answer
def send_phone_notification(message_text):
    """Sends a push notification to your phone via ntfy.sh"""
    topic_url = "https://ntfy.sh/pratik_clinic_alerts_2026" 
    try:
        requests.post(topic_url, data=message_text.encode(encoding='utf-8'))
        print("Phone notification sent successfully!")
    except Exception as e:
        print(f"Failed to send notification: {e}")

router = APIRouter()

class VoiceQueryRequest(BaseModel):
    question: str = Field(..., description="The patient's natural‑language question")

class VoiceQueryResponse(BaseModel):
    answer: str

@router.post("/voice-query", response_model=VoiceQueryResponse)
async def voice_query(payload: VoiceQueryRequest, background_tasks: BackgroundTasks):
    # 1. Trigger the phone notification quietly in the background
    alert_text = f"📞 AI Agent received a new voice query: {payload.question}"
    background_tasks.add_task(send_phone_notification, alert_text)

    # 2. Run your actual clinic AI logic
    try:
        answer = await get_clinic_answer(payload.question)
        return VoiceQueryResponse(answer=answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
