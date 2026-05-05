from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
PROCESS_DIR = ROOT_DIR / "process"
if str(PROCESS_DIR) not in sys.path:
    sys.path.insert(0, str(PROCESS_DIR))

from city_assistant.config import AppConfig
from city_assistant.data_repository import DataRepository
from city_assistant.retrieval import retrieve_relevant_candidates
from city_assistant.chat_service import ChatService
from city_assistant.vkr_components import (
    inject_vkr_css,
    render_topbar,
    render_assistant_page,
    render_problem_card_page,
    candidate_title,
    candidate_score,
)

st.set_page_config(page_title="Аналитическая платформа", layout="wide", initial_sidebar_state="expanded")
inject_vkr_css()
render_topbar("Анализ проблем")

cfg = AppConfig()
ARTIFACTS_ROOT = APP_DIR / "artifacts"
repo_tmp = DataRepository(ARTIFACTS_ROOT, cfg.scenario_id)
scenarios = repo_tmp.list_scenarios() or [cfg.scenario_id]

with st.sidebar:
    st.header("Параметры анализа")
    scenario_id = st.selectbox("Сценарий", scenarios, index=scenarios.index(cfg.scenario_id) if cfg.scenario_id in scenarios else 0)
    repo = DataRepository(ARTIFACTS_ROOT, scenario_id)
    candidates_jsonl = st.text_input("JSONL кандидатов", value=cfg.candidates_jsonl)
    problems_csv = st.text_input("CSV fallback", value=cfg.problems_csv)
    st.divider()
    screen = st.radio("Экран", ["ИИ-помощник", "Карточка проблемы"], horizontal=False)
    min_score = st.slider("Минимальный индекс", 0.0, 1.0, 0.0, 0.01)
    search = st.text_input("Поиск", value="")
    st.caption("Визуальный слой не меняет расчетные данные: он отображает уже подготовленные карточки кандидатов.")

candidates = repo.load_candidates(candidates_jsonl, problems_csv)
if not candidates:
    st.warning("Кандидаты проблем не найдены. Сначала запусти пайплайн: `python process/main.py --input data_all.xlsx --output-dir city_assistant_ui/artifacts/default`.")
    st.stop()

filtered = [c for c in candidates if candidate_score(c) >= min_score]
if search.strip():
    filtered = retrieve_relevant_candidates(filtered, search, top_k=max(20, len(filtered)))
filtered = sorted(filtered, key=candidate_score, reverse=True)

if not filtered:
    st.info("По текущим фильтрам ничего не найдено.")
    st.stop()

if screen == "ИИ-помощник":
    render_assistant_page(filtered)
    chat = ChatService(filtered, chat_mode="heuristic")
    prompt = st.chat_input("Задай вопрос по найденным комплексным проблемам…")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            st.markdown(chat.answer(prompt, top_k_ctx=8))
else:
    titles = [f"{c.get('candidate_id', '')} · {candidate_title(c)}" for c in filtered]
    idx = st.selectbox("Выберите кандидата комплексной проблемы", range(len(filtered)), format_func=lambda i: titles[i])
    render_problem_card_page(filtered[idx])
