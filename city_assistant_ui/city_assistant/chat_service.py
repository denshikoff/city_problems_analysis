from __future__ import annotations
from typing import Any, Dict, List
from city_assistant.retrieval import normalize_text, retrieve_relevant_candidates
try:
    from llm_service import LLMService
except Exception:
    LLMService=None
class ChatService:
    def __init__(self,candidates:List[Dict[str,Any]],chat_mode="heuristic"):
        self.candidates=candidates or []; self.chat_mode=chat_mode; self.llm=LLMService(backend=chat_mode) if LLMService else None
    def answer(self,user_query:str,top_k_ctx:int=10)->str:
        ctx=retrieve_relevant_candidates(self.candidates,user_query,top_k_ctx); q=normalize_text(user_query)
        if self.chat_mode in {"ollama","llm"} and self.llm: return self.llm.answer_question(user_query,ctx)
        if any(k in q for k in ["топ","самые","главные","ключевые","список"]): return self._top(ctx)
        if any(k in q for k in ["почему","объясни","поясни","комплекс"]): return self._why(ctx[:1])
        if any(k in q for k in ["карточ","подробнее","доказ","обращен"]): return self._card(ctx[:1])
        if any(k in q for k in ["что делать","действ","рекомендац","управлен"]): return self._actions(ctx[:1])
        return self._overview(ctx)
    def score(self,c): return f"{float(c.get('complexity_score') or c.get('Complexity_score') or 0):.3f}"
    def freq(self,c): return int((c.get("metrics",{}) or {}).get("frequency") or len(c.get("appeal_ids",[])) or c.get("Частота_упоминаний") or 0)
    def _top(self,ctx):
        if not ctx: return "Кандидаты проблем не найдены."
        lines=["Топ комплексных проблем:"]
        for i,c in enumerate(ctx[:10],1): lines.append(f"{i}. **{c.get('title') or c.get('Проблема')}** ({c.get('problem_type') or c.get('Тип_проблемы')}) — score={self.score(c)}, обращений={self.freq(c)}, id=`{c.get('candidate_id')}`")
        return "\n".join(lines)
    def _why(self,ctx):
        if not ctx: return "Не нашел подходящую проблему для объяснения."
        c=ctx[0]; raw=(c.get("score_factors",{}) or {}).get("raw",{}) or {}; lines=[f"**Почему «{c.get('title')}» комплексная:**",f"- Complexity_score: **{self.score(c)}**.",f"- Подтверждающих обращений: **{self.freq(c)}**.",f"- Субъекты: {', '.join(c.get('actors',[])[:6]) or 'нет данных'}.",f"- Действия/состояния: {', '.join(c.get('actions',[])[:6]) or 'нет данных'}.",f"- Признаки: {', '.join(c.get('problem_anchors',[])[:6]) or 'нет данных'}." ]
        if raw: lines.append(f"- Факторы score: frequency={raw.get('frequency')}, entities={raw.get('unique_entities')}, actions={raw.get('unique_actions')}, relations={raw.get('relations_count')}, density={raw.get('subgraph_density')}.")
        return "\n".join(lines)
    def _card(self,ctx):
        if not ctx: return "Не нашел карточку. Укажи id вида `kp_0001`."
        c=ctx[0]; s=c.get("llm_summary") or {}; lines=[f"## {s.get('short_title') or c.get('title')}",f"**Тип:** {c.get('problem_type')}  ",f"**Complexity_score:** {self.score(c)}  "]
        if s.get("problem_essence"): lines.append(f"\n**Суть:** {s['problem_essence']}")
        if s.get("why_complex"): lines.append(f"\n**Почему комплексная:** {s['why_complex']}")
        lines.append("\n**Подтверждающие обращения:**")
        for ev in c.get("evidence_appeals",[])[:3]: lines.append(f"- `{ev.get('appeal_id')}` {ev.get('date') or ''} {ev.get('address') or ''}: {str(ev.get('text') or '')[:350]}")
        if not c.get("evidence_appeals"): lines.append("- В CSV-режиме примеры недоступны. Используй JSONL-артефакт.")
        return "\n".join(lines)
    def _actions(self,ctx):
        if not ctx: return "Не нашел проблему для рекомендаций."
        c=ctx[0]; actions=(c.get("llm_summary") or {}).get("management_actions") or ["проверить подтверждающие обращения","назначить владельца проблемы","согласовать ответственных исполнителей","задать срок устранения причины повторяемости"]
        return "\n".join([f"Для **{c.get('title')}**:"]+[f"{i}. {a}" for i,a in enumerate(actions,1)])
    def _overview(self,ctx):
        total=len(self.candidates); systemic=sum(1 for c in self.candidates if float(c.get("complexity_score") or 0)>=.7); lines=[f"В базе кандидатов: **{total}**, score ≥ 0.7: **{systemic}**."]
        if ctx:
            lines.append("Релевантные запросу:")
            for i,c in enumerate(ctx[:5],1): lines.append(f"{i}. **{c.get('title')}** — score={self.score(c)}, id=`{c.get('candidate_id')}`")
        lines.append("\nСпроси: **топ проблем**, **почему kp_0001 комплексная**, **покажи карточку kp_0001**.")
        return "\n".join(lines)
