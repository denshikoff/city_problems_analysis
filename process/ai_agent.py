from __future__ import annotations
from typing import Any, Dict
from llm_service import LLMService

def run_agent(payload:Dict[str,Any])->Dict[str,Any]:
    service=LLMService(); candidates=payload.get("candidates") or payload.get("problems") or []
    return {"meta":payload.get("meta",{}),"summary":service.answer_question("Какие главные комплексные проблемы выявлены?", candidates[:10]),"candidate_summaries":[{"candidate_id":c.get("candidate_id"),"summary":service.summarize_candidate(c)} for c in candidates[:20]],"note":"LLM/heuristic не меняет метрики и complexity_score."}
