import os
from pathlib import Path

import streamlit as st

from city_assistant.config import AppConfig
from city_assistant.data_repository import DataRepository
from city_assistant.chat_service import ChatService


st.set_page_config(page_title="Городской ИИ-помощник", layout="wide")
st.title("Чат с городским ИИ-помощником")

cfg = AppConfig()

# Надёжный путь к артефактам рядом с app.py (Render-safe)
APP_DIR = Path(__file__).resolve().parent
ARTIFACTS_ROOT = APP_DIR / "artifacts"

# Repo для списка сценариев
tmp_repo = DataRepository(str(ARTIFACTS_ROOT), cfg.scenario_id)
scenario_options = tmp_repo.list_scenarios() or [cfg.scenario_id]

with st.sidebar:
    st.header("Настройки")

    scenario_id = st.selectbox(
        "Сценарий",
        options=scenario_options,
        index=scenario_options.index(cfg.scenario_id) if cfg.scenario_id in scenario_options else 0,
    )

    repo = DataRepository(str(ARTIFACTS_ROOT), scenario_id)

    problems_file = st.text_input("CSV проблем", value=cfg.problems_csv)
    agent_report_file = st.text_input("JSON отчёта агента (опционально)", value=cfg.agent_report_json)

    st.divider()
    st.subheader("Фильтры")
    min_score = st.slider("Минимальный Complexity_score", 0.0, 1.0, 0.0, 0.01)
    only_systemic = st.checkbox("Только системные (score ≥ 0.7)", value=False)
    type_filter = st.text_input("Тип проблемы (например: транспорт / ЖКХ)", value="").strip()

    st.divider()
    st.subheader("Чат")
    top_k_ctx = st.slider("Контекст (топ-N проблем)", 5, 30, cfg.top_k_ctx_default, 1)

    if st.button("Очистить чат"):
        st.session_state.messages = []
        st.rerun()

# Собираем абсолютные пути и грузим данные
problems_path = Path(repo.path(problems_file))
agent_report_path = Path(repo.path(agent_report_file))  # опционально, можно не использовать

problems_df = repo.load_problems(str(problems_path))
# agent_report = repo.load_json(str(agent_report_path))  # если понадобится позже

# Применяем фильтры
df_view = problems_df[problems_df["Complexity_score"] >= float(min_score)].copy()
if only_systemic:
    df_view = df_view[df_view["Complexity_score"] >= 0.7]
if type_filter:
    df_view = df_view[df_view["Тип_проблемы"].str.contains(type_filter, case=False, na=False)]

chat = ChatService(df_view, chat_mode=cfg.chat_mode)

# --------------------------
# CHAT UI
# --------------------------
st.subheader("Диалог")

if "messages" not in st.session_state:
    st.session_state.messages = []

# История
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Ввод
user_msg = st.chat_input("Спроси: «топ проблем», «почему X комплексная?», «покажи транспорт»…")

if user_msg:
    st.session_state.messages.append({"role": "user", "content": user_msg})

    answer = chat.answer(user_msg, top_k_ctx=top_k_ctx)

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})