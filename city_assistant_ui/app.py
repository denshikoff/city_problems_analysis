from __future__ import annotations
from pathlib import Path
import streamlit as st
from city_assistant.config import AppConfig
from city_assistant.data_repository import DataRepository
from city_assistant.chat_service import ChatService
from city_assistant.retrieval import retrieve_relevant_candidates
from city_assistant.ui_components import render_problem_card
from city_assistant.report_renderer import render_markdown_report

st.set_page_config(page_title="Городской ИИ-помощник", layout="wide")
st.title("Городской ИИ-помощник по комплексным проблемам")
st.caption("Работает с `json/problem_candidates.jsonl`, созданным пайплайном обработки.")
cfg=AppConfig(); APP_DIR=Path(__file__).resolve().parent; ARTIFACTS_ROOT=APP_DIR/"artifacts"
repo_tmp=DataRepository(ARTIFACTS_ROOT,cfg.scenario_id); scenarios=repo_tmp.list_scenarios() or [cfg.scenario_id]
with st.sidebar:
    st.header("Данные")
    scenario_id=st.selectbox("Сценарий",scenarios,index=scenarios.index(cfg.scenario_id) if cfg.scenario_id in scenarios else 0)
    repo=DataRepository(ARTIFACTS_ROOT,scenario_id)
    candidates_jsonl=st.text_input("JSONL кандидатов",value=cfg.candidates_jsonl)
    problems_csv=st.text_input("CSV fallback",value=cfg.problems_csv)
    st.divider(); st.header("Фильтры")
    min_score=st.slider("Минимальный Complexity_score",0.0,1.0,0.0,0.01)
    only_systemic=st.checkbox("Только score ≥ 0.7",value=False)
    type_filter=st.text_input("Тип/направление",value="")
    query_filter=st.text_input("Поиск по карточкам",value="")
    st.divider(); st.header("Чат")
    chat_mode=st.selectbox("Режим",["heuristic","ollama"],index=0 if cfg.chat_mode!="ollama" else 1)
    top_k_ctx=st.slider("Контекст, топ-N",3,30,cfg.top_k_ctx_default,1)
    if st.button("Очистить чат"):
        st.session_state.messages=[]; st.rerun()

candidates=repo.load_candidates(candidates_jsonl,problems_csv)
if not candidates:
    st.warning("Кандидаты проблем не найдены. Запусти: `python process/main.py --input data_all.xlsx --output-dir city_assistant_ui/artifacts/default --max-rows 5000`")
    st.stop()
filtered=[]
for c in candidates:
    score=float(c.get("complexity_score") or c.get("Complexity_score") or 0)
    if score<min_score or (only_systemic and score<.7): continue
    if type_filter and type_filter.lower() not in str(c.get("problem_type") or c.get("Тип_проблемы") or "").lower(): continue
    filtered.append(c)
if query_filter.strip(): filtered=retrieve_relevant_candidates(filtered,query_filter,top_k=max(20,top_k_ctx))
filtered=sorted(filtered,key=lambda c:float(c.get("complexity_score") or 0),reverse=True)

st.subheader("Сводка"); c1,c2,c3=st.columns(3); c1.metric("Кандидатов",len(filtered)); c2.metric("Всего",len(candidates)); c3.metric("Score ≥ 0.7",sum(1 for c in filtered if float(c.get("complexity_score") or 0)>=.7))
st.divider(); left,right=st.columns([1.2,1])
with left:
    st.subheader("Топ проблем")
    for i,c in enumerate(filtered[:10],1): render_problem_card(c,expanded=i<=2)
    st.download_button("Скачать markdown-отчет",data=render_markdown_report(filtered,10),file_name=f"{scenario_id}_complex_problems_report.md",mime="text/markdown")
with right:
    st.subheader("Диалог"); chat=ChatService(filtered,chat_mode=chat_mode)
    if "messages" not in st.session_state: st.session_state.messages=[]
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    user_msg=st.chat_input("Спроси: топ проблем, почему kp_0001 комплексная, покажи карточку...")
    if user_msg:
        st.session_state.messages.append({"role":"user","content":user_msg}); answer=chat.answer(user_msg,top_k_ctx=top_k_ctx)
        with st.chat_message("assistant"): st.markdown(answer)
        st.session_state.messages.append({"role":"assistant","content":answer})
