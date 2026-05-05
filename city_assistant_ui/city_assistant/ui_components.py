from __future__ import annotations
from typing import Any, Dict
import streamlit as st

def render_problem_card(c:Dict[str,Any], expanded=False):
    title=c.get("title") or c.get("Проблема") or "Проблема"; cid=c.get("candidate_id") or ""; m=c.get("metrics",{}) or {}
    with st.expander(f"{cid} · {title}", expanded=expanded):
        cols=st.columns(4); cols[0].metric("Complexity_score",f"{float(c.get('complexity_score') or 0):.3f}"); cols[1].metric("Обращений",int(m.get("frequency") or len(c.get("appeal_ids",[])) or 0)); cols[2].metric("Связей",int(m.get("relations_count") or 0)); cols[3].metric("Плотность",f"{float(m.get('subgraph_density') or 0):.3f}")
        s=c.get("llm_summary") or {}
        if s.get("problem_essence"): st.markdown(f"**Суть:** {s['problem_essence']}")
        if s.get("why_complex"): st.markdown(f"**Почему комплексная:** {s['why_complex']}")
        st.write({"тип":c.get("problem_type"),"сущности":c.get("entities",[])[:12],"действия":c.get("actions",[])[:8],"акторы":c.get("actors",[])[:8],"территории":c.get("territories",[])[:8],"период":c.get("time_window",{})})
        if s.get("management_actions"):
            st.markdown("**Возможные действия**")
            for a in s["management_actions"]: st.markdown(f"- {a}")
        if c.get("evidence_appeals"):
            st.markdown("**Подтверждающие обращения**")
            for ev in c.get("evidence_appeals",[])[:5]: st.markdown(f"- `{ev.get('appeal_id')}` · {ev.get('date') or ''} · {ev.get('address') or ''}"); st.caption(str(ev.get("text") or "")[:700])
