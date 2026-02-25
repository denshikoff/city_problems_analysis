import streamlit as st

from city_assistant.config import AppConfig
from city_assistant.data_repository import DataRepository
from city_assistant.chat_service import ChatService
from city_assistant.ui_components import render_metrics, render_problem_table, render_problem_card
from city_assistant.report_renderer import render_human_report  # если уже добавили

st.set_page_config(page_title="Городской ИИ-помощник", layout="wide")
st.title("Городской ИИ-помощник для служб: выявление и ранжирование проблем")

cfg = AppConfig()
from pathlib import Path
import os
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ARTIFACTS_ROOT = APP_DIR / "artifacts"   # <-- ВАЖНО: абсолютный корректный root

st.write("CWD:", os.getcwd())
st.write("APP_DIR:", str(APP_DIR))
st.write("ARTIFACTS_ROOT (forced):", str(ARTIFACTS_ROOT))
st.write("ARTIFACTS_ROOT exists:", ARTIFACTS_ROOT.exists())

# 1) список сценариев
tmp_repo = DataRepository(str(ARTIFACTS_ROOT), cfg.scenario_id)
scenario_options = tmp_repo.list_scenarios() or [cfg.scenario_id]

with st.sidebar:
    st.header("Сценарий")
    scenario_id = st.selectbox(
        "Выбери сценарий",
        options=scenario_options,
        index=scenario_options.index(cfg.scenario_id) if cfg.scenario_id in scenario_options else 0
    )

    repo = DataRepository(cfg.artifacts_root, scenario_id)

    st.divider()
    st.header("Файлы")
    problems_file = st.text_input("CSV проблем", value=cfg.problems_csv)
    agent_report_file = st.text_input("JSON отчёта агента", value=cfg.agent_report_json)

    st.caption(f"Папка сценария: `{repo.scenario_dir()}`")

    st.divider()
    st.header("Фильтры")
    min_score = st.slider("Минимальный Complexity_score", 0.0, 1.0, 0.0, 0.01)
    only_systemic = st.checkbox("Только системные (score ≥ 0.7)", value=False)
    type_filter = st.text_input("Тип проблемы (например: транспорт / ЖКХ / инфраструктура)", value="").strip()

    st.divider()
    st.header("Чат")
    top_k_ctx = st.slider("Контекст (топ-N проблем)", 5, 30, cfg.top_k_ctx_default, 1)
    st.caption(f"CHAT_MODE: {cfg.chat_mode}")

    if st.button("Очистить чат"):
        st.session_state.messages = []
        st.rerun()
st.write("Artifacts root:", cfg.artifacts_root)

agent_report_path = Path(repo.path(agent_report_file))
st.write("Agent report path:", str(agent_report_path))
st.write("Exists:", agent_report_path.exists())

# 2) загрузка
problems_df = repo.load_problems(problems_file)
agent_report = repo.load_json(agent_report_file)

# 3) фильтрация
df_view = problems_df[problems_df["Complexity_score"] >= float(min_score)].copy()
if only_systemic:
    df_view = df_view[df_view["Complexity_score"] >= 0.7]
if type_filter:
    df_view = df_view[df_view["Тип_проблемы"].str.contains(type_filter, case=False, na=False)]

chat = ChatService(df_view, chat_mode=cfg.chat_mode)

# --------------------------
# MAIN: обзор + чат как GPT
# --------------------------

# Верх: метрики и обзор
left, right = st.columns([2, 1])

with left:
    st.subheader("ТОП проблем по комплексности")
    render_problem_table(df_view, n=30)

with right:
    st.subheader("Сводные метрики")
    render_metrics(df_view)

    st.divider()
    st.subheader("Отчёт агента")
    if agent_report:
        # кнопка "человеческий отчёт"
        if st.button("Сгенерировать человекочитаемый отчёт"):
            render_human_report(agent_report)
        else:
            st.caption("Нажми кнопку, чтобы собрать отчёт из final_agent_report.json")
    else:
        st.caption("final_agent_report.json не найден — это нормально.")

st.divider()

# Карточка проблемы (по желанию — компактно на главной)
st.subheader("Карточка проблемы")
options = df_view.sort_values("Complexity_score", ascending=False)["Проблема"].head(200).tolist()
chosen = st.selectbox("Выбери проблему", options=options if options else ["—"])
if chosen and chosen != "—":
    render_problem_card(df_view, chosen)

st.divider()

# ЧАТ как GPT
st.subheader("Чат с помощником")

if "messages" not in st.session_state:
    st.session_state.messages = []

# показать историю
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# поле ввода снизу
user_msg = st.chat_input("Спроси: «топ проблем», «почему Автобус комплексный?», «покажи транспорт»…")

if user_msg:
    st.session_state.messages.append({"role": "user", "content": user_msg})

    answer = chat.answer(user_msg, top_k_ctx=top_k_ctx)

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
