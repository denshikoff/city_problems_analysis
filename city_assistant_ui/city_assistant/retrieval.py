from __future__ import annotations
import re
from typing import Any, Dict, List

def normalize_text(v:Any)->str: return re.sub(r"\s+"," ",str(v or "").lower().replace("ё","е")).strip()
def tokens(q): return [t for t in re.findall(r"[а-яa-z0-9]{3,}",normalize_text(q)) if t not in {"что","как","это","почему","какие","покажи"}]
def cand_text(c:Dict[str,Any])->str:
    parts=[c.get("candidate_id"),c.get("title") or c.get("Проблема"),c.get("problem_type") or c.get("Тип_проблемы")]
    for k in ["entities","actions","actors","problem_anchors","territories","thematic_areas"]: parts += c.get(k,[]) or []
    for ev in c.get("evidence_appeals",[])[:3]: parts += [ev.get("text",""),ev.get("address","")]
    return normalize_text(" ".join(str(x) for x in parts if x))
def retrieve_relevant_candidates(candidates:List[Dict[str,Any]], query:str, top_k:int=10):
    if not candidates: return []
    q=normalize_text(query); ts=tokens(q); scored=[]
    for c in candidates:
        text=cand_text(c); score=float(c.get("complexity_score") or c.get("Complexity_score") or 0)*.75; cid=normalize_text(c.get("candidate_id")); title=normalize_text(c.get("title") or c.get("Проблема"))
        if cid and cid in q: score+=10
        if title and title in q: score+=6
        for t in ts: score+=2.5 if t in title else (1.0 if t in text else 0)
        scored.append((score,c))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [c for s,c in scored[:top_k] if s>0] if ts else sorted(candidates,key=lambda c:float(c.get("complexity_score") or 0),reverse=True)[:top_k]
