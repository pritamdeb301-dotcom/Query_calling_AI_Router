from typing import List
import json
import string
from app.rag.vectorstore import get_vectorstore
from sentence_transformers import SentenceTransformer, util
from pathlib import Path
# 1. Dynamically build the path to the JSON file
# Path(__file__).parent gets the 'rag' folder. .parent goes up to the 'app' folder.
current_file_path = Path(__file__).resolve()
json_path = current_file_path.parent.parent / 'config' / 'patient_intents.json'

# Open the file using the dynamic path
with open(json_path, 'r', encoding='utf-8') as f:
    patient_intents = json.load(f)

# 2. THEN: Use that variable to set up the semantic model
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
intent_list = patient_intents.get('intents', [])
intent_questions = [intent.get('question', '') for intent in intent_list]
intent_embeddings = semantic_model.encode(intent_questions, convert_to_tensor=True)




def find_intent_match(question: str, threshold: float = 0.40) -> str | None:
    """Finds an intent by checking semantic mathematical similarity."""
    if not intent_questions:
        return None
        
    # 1. Convert user text to math
    query_embedding = semantic_model.encode(question, convert_to_tensor=True)
    
    # 2. Calculate similarities
    cos_scores = util.cos_sim(query_embedding, intent_embeddings)[0]
    
    # 3. Find the best score
    best_match_idx = cos_scores.argmax().item()
    best_score = cos_scores[best_match_idx].item()
    matched_intent = intent_list[best_match_idx]
    
    # --- X-RAY VISION (Prints to your VS Code Terminal) ---
    print("\n--- 🧠 AI THINKING PROCESS ---")
    print(f"User Typed:        '{question}'")
    print(f"Closest JSON File: '{matched_intent.get('question', '')}'")
    print(f"Similarity Score:  {best_score:.2f} (Needs {threshold:.2f} to pass)")
    
    # 4. Make the decision
    if best_score >= threshold:
        print("✅ MATCH PASSED! Answering from JSON file.\n")
        return matched_intent.get('answer')
        
    print("❌ SCORE TOO LOW! Falling back to clinic_knowledge.md.\n")
    return None

async def get_clinic_answer(question: str, top_k: int = 4) -> str:
    # Check for match in patient intents first
    intent_answer = find_intent_match(question)
    if intent_answer:
        return intent_answer

    # If no match in intents, proceed with vectorstore search
    store = get_vectorstore()
    results = store.similarity_search(question, k=top_k)
    if not results:
        return "I'm sorry, I don't have that information right now."

    # Sort by distance and return best match
    sorted_results = sorted(results, key=lambda r: r["distance"])
    best = sorted_results[0]["document"].strip()
    return best