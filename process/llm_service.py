from __future__ import annotations
import json, os
from typing import Any, Dict, List, Optional
try:
    import requests
except Exception:
    requests=None

SYSTEM_PROMPT="""Ты городской аналитический ИИ-помощник. Используй только входные карточки проблем. Не придумывай факты, не меняй complexity_score и метрики."""
class LLMService:
    def __init__(self, backend:Optional[str]=None, model:Optional[str]=None):
        self.backend=(backend or os.getenv("LLM_BACKEND") or "heuristic").lower(); self.model=model or os.getenv("OLLAMA_MODEL") or "mistral"; self.url=os.getenv("OLLAMA_URL","http://localhost:11434/api/chat")
    @staticmethod
    def brief(c:Dict[str,Any])->Dict[str,Any]:
        return {"candidate_id":c.get("candidate_id"),"title":c.get("title") or c.get("Проблема"),"problem_type":c.get("problem_type") or c.get("Тип_проблемы"),"complexity_score":c.get("complexity_score") or c.get("Complexity_score"),"metrics":c.get("metrics",{}),"score_factors":c.get("score_factors",{}),"entities":c.get("entities",[])[:15],"actions":c.get("actions",[])[:10],"actors":c.get("actors",[])[:10],"problem_anchors":c.get("problem_anchors",[])[:10],"territories":c.get("territories",[])[:10],"evidence_appeals":c.get("evidence_appeals",[])[:3]}
    def _ollama(self,prompt):
        if requests is None: return None
        try:
            r=requests.post(self.url,json={"model":self.model,"messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}],"stream":False,"options":{"temperature":0.2}},timeout=120); r.raise_for_status(); return r.json().get("message",{}).get("content")
        except Exception: return None
    def summarize_candidate(self,c):
        if self.backend=="ollama":
            text=self._ollama("Верни JSON с ключами short_title, problem_essence, why_complex, risks, management_actions, evidence_summary.\n"+json.dumps(self.brief(c),ensure_ascii=False,indent=2))
            if text:
                try:
                    return json.loads(text[text.find('{'):text.rfind('}')+1])
                except Exception: return {"raw_llm_text":text}
        return self._heuristic_summary(c)
    def _heuristic_summary(self,c):
        title=c.get("title") or c.get("Проблема") or "Кандидат проблемы"; score=c.get("complexity_score") or c.get("Complexity_score") or 0; m=c.get("metrics",{}) or {}; freq=m.get("frequency") or len(c.get("appeal_ids",[])); anchors=c.get("problem_anchors",[])[:4]; actors=c.get("actors",[])[:4]; actions=c.get("actions",[])[:4]; terr=c.get("territories",[])[:4]
        why=[f"подтвержден {freq} обращениями",f"индекс комплексности {score}"]
        if actors: why.append("участники: "+", ".join(actors))
        if actions: why.append("повторяются действия/состояния: "+", ".join(actions))
        if terr: why.append("территории: "+", ".join(terr))
        return {"short_title":str(title)[:100],"problem_essence":f"В обращениях повторяется проблемный узел «{title}». Признаки: {', '.join(anchors) if anchors else 'связанные жалобы' }.","why_complex":"; ".join(why)+".","risks":["рост повторных обращений","размывание ответственности между исполнителями","закрытие заявок без устранения причины"],"management_actions":["проверить подтверждающие обращения","назначить владельца проблемы","согласовать ответственных исполнителей","поставить срок устранения причины повторяемости"],"evidence_summary":"Карточка основана на метриках, связях и примерах обращений."}
    def answer_question(self, query:str, candidates:List[Dict[str,Any]])->str:
        if not candidates: return "Не нашел релевантных кандидатов проблем."
        if self.backend in {"ollama","llm"}:
            text=self._ollama(f"Вопрос: {query}\nКандидаты:\n"+json.dumps([self.brief(c) for c in candidates[:8]],ensure_ascii=False,indent=2))
            if text: return text
        lines=["По запросу наиболее релевантны:"]
        for i,c in enumerate(candidates[:5],1): lines.append(f"{i}. **{c.get('title') or c.get('Проблема')}** — score={float(c.get('complexity_score') or c.get('Complexity_score') or 0):.3f}, обращений={len(c.get('appeal_ids',[])) or (c.get('metrics',{}) or {}).get('frequency',0)}.")
        return "\n".join(lines)
