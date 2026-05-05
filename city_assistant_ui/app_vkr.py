from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

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
    candidate_score,
    candidate_title,
    inject_vkr_css,
    render_problem_card,
    render_problem_preview,
    render_topbar,
)


def load_candidates() -> tuple[List[Dict[str, Any]], str]:
    cfg = AppConfig()
    artifacts_root = APP_DIR / "artifacts"
    repo = DataRepository(artifacts_root, cfg.scenario_id)
    candidates = repo.load_candidates(cfg.candidates_jsonl, cfg.problems_csv)
    return candidates, cfg.scenario_id


def candidate_markdown(candidate: Dict[str, Any]) -> str:
    summary = candidate.get("llm_summary") or {}
    metrics = candidate.get("metrics") or {}
    lines = [
        f"# {candidate_title(candidate)}",
        "",
        f"ID: `{candidate.get('candidate_id', '')}`",
        f"Тип: {candidate.get('problem_type', '')}",
        f"Индекс комплексности: {candidate_score(candidate):.3f}",
        f"Обращений: {metrics.get('frequency', len(candidate.get('appeal_ids', [])))}",
        f"Связей: {metrics.get('relations_count', 0)}",
        "",
        "## Описание",
        summary.get("problem_essence", "Нет описания."),
        "",
        "## Почему проблема комплексная",
        summary.get("why_complex", "Нет пояснения."),
        "",
        "## Рекомендуемые действия",
    ]
    for action in summary.get("management_actions", []) or []:
        lines.append(f"- {action}")
    lines += ["", "## Подтверждающие обращения"]
    for ev in candidate.get("evidence_appeals", [])[:10]:
        lines.append(f"- `{ev.get('appeal_id')}` {ev.get('date') or ''} {ev.get('address') or ''}: {str(ev.get('text') or '')[:500]}")
    return "\n".join(lines)


def filter_candidates(candidates: List[Dict[str, Any]], category: str, query: str, only_high: bool) -> List[Dict[str, Any]]:
    result = candidates[:]
    if category != "Все категории":
        result = [c for c in result if str(c.get("problem_type") or "") == category]
    if only_high:
        result = [c for c in result if candidate_score(c) >= 0.70]
    if query.strip():
        result = retrieve_relevant_candidates(result, query, top_k=max(20, len(result)))
    return sorted(result, key=candidate_score, reverse=True)


def open_card(candidate_id: str) -> None:
    st.session_state.vkr_selected_candidate_id = candidate_id
    st.session_state.vkr_screen = "card"
    st.rerun()


def selected_candidate(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    selected_id = st.session_state.get("vkr_selected_candidate_id")
    if selected_id:
        for c in candidates:
            if str(c.get("candidate_id")) == str(selected_id):
                return c
    return candidates[0]


st.set_page_config(page_title="Анализ комплексных городских проблем", layout="wide", initial_sidebar_state="expanded")
inject_vkr_css()
render_topbar()

if "vkr_screen" not in st.session_state:
    st.session_state.vkr_screen = "assistant"
if "vkr_selected_candidate_id" not in st.session_state:
    st.session_state.vkr_selected_candidate_id = None
if "vkr_chat_messages" not in st.session_state:
    st.session_state.vkr_chat_messages = []
if "vkr_analysis_started" not in st.session_state:
    st.session_state.vkr_analysis_started = False

all_candidates, scenario_id = load_candidates()
if not all_candidates:
    st.error("Кандидаты комплексных проблем не найдены. Сначала запусти обработку данных и сформируй артефакты анализа.")
    st.code("python process/main.py --input data_all.xlsx --output-dir city_assistant_ui/artifacts/default", language="bash")
    st.stop()

categories = sorted({str(c.get("problem_type") or "Другое") for c in all_candidates if c.get("problem_type")})

with st.sidebar:
    st.markdown("# Параметры анализа")
    st.markdown("<div class='vkr-side-note'>Источник данных</div>", unsafe_allow_html=True)
    st.text_input("Источник данных", value="ЦУР + городские платформы", label_visibility="collapsed")
    st.markdown("<div class='vkr-side-note'>Период</div>", unsafe_allow_html=True)
    st.text_input("Период", value="2022 год", label_visibility="collapsed")
    st.markdown("<div class='vkr-side-note'>Регион</div>", unsafe_allow_html=True)
    region = st.text_input("Регион", value="Санкт-Петербург", label_visibility="collapsed")
    st.markdown("<div class='vkr-side-note'>Категория</div>", unsafe_allow_html=True)
    category = st.selectbox("Категория", ["Все категории"] + categories, label_visibility="collapsed")
    st.markdown("<div style='height:34px'></div>", unsafe_allow_html=True)
    if st.button("Запустить анализ", use_container_width=True):
        st.session_state.vkr_analysis_started = True
        st.session_state.vkr_screen = "assistant"
        st.toast("Анализ загружен. Можно задавать вопросы по комплексным проблемам.")
        st.rerun()
    st.markdown("---")
    only_high = st.checkbox("Показывать только высокий индекс", value=False)
    search_query = st.text_input("Поиск по проблемам", value="")
    if st.button("Сбросить диалог", use_container_width=True):
        st.session_state.vkr_chat_messages = []
        st.session_state.vkr_screen = "assistant"
        st.rerun()

filtered = filter_candidates(all_candidates, category, search_query, only_high)
if not filtered:
    st.info("По текущим параметрам не найдено комплексных проблем.")
    st.stop()

if not st.session_state.vkr_selected_candidate_id:
    st.session_state.vkr_selected_candidate_id = str(filtered[0].get("candidate_id"))

chat = ChatService(filtered, chat_mode="heuristic")

if st.session_state.vkr_screen == "assistant":
    st.markdown("<div class='vkr-chat-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='vkr-clean-title'>Интерфейс ИИ-помощника для анализа комплексных городских проблем</div>", unsafe_allow_html=True)
    st.markdown("<div class='vkr-subtitle'>Задай вопрос в формате диалога. Помощник использует рассчитанные карточки комплексных проблем и не меняет индекс комплексности.</div>", unsafe_allow_html=True)

    if not st.session_state.vkr_chat_messages:
        with st.chat_message("user"):
            st.markdown("Какие комплексные проблемы ты видишь в городе?")
        with st.chat_message("assistant"):
            st.markdown("На основе графового анализа выявлены наиболее значимые комплексные проблемы города.")
            st.markdown("<div class='vkr-dialog-list'><h3>Топ-5 комплексных проблем</h3></div>", unsafe_allow_html=True)
            for i, candidate in enumerate(filtered[:5], 1):
                col_preview, col_button = st.columns([0.78, 0.22])
                with col_preview:
                    render_problem_preview(candidate, i)
                with col_button:
                    st.write("")
                    st.write("")
                    if st.button("Открыть карточку →", key=f"open_top_{candidate.get('candidate_id')}", use_container_width=True):
                        open_card(str(candidate.get("candidate_id")))
            st.caption("Выбери проблему, чтобы открыть подробную карточку с метриками, обращениями, сущностями и рекомендуемыми действиями.")
    else:
        for idx, msg in enumerate(st.session_state.vkr_chat_messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("show_cards"):
                    for i, candidate in enumerate(filtered[:5], 1):
                        col_preview, col_button = st.columns([0.78, 0.22])
                        with col_preview:
                            render_problem_preview(candidate, i)
                        with col_button:
                            st.write("")
                            st.write("")
                            if st.button("Открыть карточку →", key=f"open_msg_{idx}_{candidate.get('candidate_id')}", use_container_width=True):
                                open_card(str(candidate.get("candidate_id")))

    prompt = st.chat_input("Например: покажи топ проблем, почему первая комплексная, что делать по отоплению…")
    if prompt:
        st.session_state.vkr_chat_messages.append({"role": "user", "content": prompt})
        q = prompt.lower()
        show_cards = any(word in q for word in ["топ", "список", "какие", "покажи"])
        answer = chat.answer(prompt, top_k_ctx=8)
        st.session_state.vkr_chat_messages.append({"role": "assistant", "content": answer, "show_cards": show_cards})
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

else:
    candidate = selected_candidate(filtered)
    top_cols = st.columns([0.18, 0.44, 0.18, 0.20])
    if top_cols[0].button("← К диалогу", use_container_width=True):
        st.session_state.vkr_screen = "assistant"
        st.rerun()
    candidate = top_cols[1].selectbox(
        "Выберите проблему",
        filtered,
        index=filtered.index(candidate) if candidate in filtered else 0,
        format_func=lambda c: f"{c.get('candidate_id')} · {candidate_title(c)}",
        label_visibility="collapsed",
        key="vkr_card_select",
    )
    st.session_state.vkr_selected_candidate_id = str(candidate.get("candidate_id"))
    top_cols[2].download_button(
        "Экспорт JSON",
        data=json.dumps(candidate, ensure_ascii=False, indent=2, default=str),
        file_name=f"{candidate.get('candidate_id', 'problem')}.json",
        mime="application/json",
        use_container_width=True,
    )
    top_cols[3].download_button(
        "Экспорт отчёта",
        data=candidate_markdown(candidate),
        file_name=f"{candidate.get('candidate_id', 'problem')}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    render_problem_card(candidate, region=region)
