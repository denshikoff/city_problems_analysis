import streamlit as st
import pandas as pd


def render_human_report(agent_report: dict):
    if not agent_report:
        st.warning("Отчёт агента не найден или пустой.")
        return

    # 1) Summary
    st.subheader("Резюме")
    summary = agent_report.get("summary", {}) or {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего проблем (в отчёте)", summary.get("total_problems", "—"))
    c2.metric("Системных", summary.get("systemic_problems_count", "—"))
    c3.metric("Локальных", summary.get("local_problems_count", "—"))
    c4.metric("Уверенность", agent_report.get("confidence", "—"))

    st.divider()

    # 2) Systemic problems
    st.subheader("Топ системных проблем")
    sys_probs = agent_report.get("systemic_problems", []) or []
    if sys_probs:
        df = pd.DataFrame(sys_probs)
        # нормализуем имена колонок, если они отличаются
        # ожидаем: problem, complexity_score, reason
        cols = [c for c in ["problem", "complexity_score", "reason"] if c in df.columns]
        st.dataframe(df[cols] if cols else df, use_container_width=True)
    else:
        st.info("Системные проблемы не указаны в отчёте агента.")

    st.divider()

    # 3) Patterns
    st.subheader("Ключевые паттерны")
    patterns = agent_report.get("key_patterns", []) or []
    if patterns:
        for p in patterns:
            st.write("• " + str(p))
    else:
        st.caption("Паттерны не указаны.")

    st.divider()

    # 4) Insights
    st.subheader("Рекомендации и управленческие выводы")
    insights = agent_report.get("management_insights", []) or []
    if insights:
        for i in insights:
            st.write("• " + str(i))
    else:
        st.caption("Рекомендации не указаны.")
