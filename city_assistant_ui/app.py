import streamlit as st
from city_assistant.config import AppConfig
from city_assistant.data_repository import DataRepository
from city_assistant.chat_service import ChatService
from city_assistant.ui_components import render_metrics, render_problem_table, render_problem_card

st.set_page_config(page_title="Городской ИИ-помощник", layout="wide")
st.title("Городской ИИ-помощник для служб: выявление и ранжирование проблем")

cfg = AppConfig()

# временно создаём repo чтобы получить список сценариев
tmp_repo = DataRepository(cfg.artifacts_root, cfg.scenario_id)
scenario_options = tmp_repo.list_scenarios() or [cfg.scenario_id]

with st.sidebar:
    st.header("Сценарий")
    scenario_id = st.selectbox("Выбери сценарий", options=scenario_options, index=scenario_options.index(cfg.scenario_id) if cfg.scenario_id in scenario_options else 0)

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

# загрузка из artifacts/<scenario_id>/
problems_df = repo.load_problems(problems_file)
agent_report = repo.load_json(agent_report_file)

# фильтры как раньше
df_view = problems_df[problems_df["Complexity_score"] >= float(min_score)].copy()
if only_systemic:
    df_view = df_view[df_view["Complexity_score"] >= 0.7]
if type_filter:
    df_view = df_view[df_view["Тип_проблемы"].str.contains(type_filter, case=False, na=False)]

chat = ChatService(df_view, chat_mode=cfg.chat_mode)
