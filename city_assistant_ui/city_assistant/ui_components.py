import numpy as np
import pandas as pd
import streamlit as st


def render_metrics(df: pd.DataFrame):
    total = len(df)
    systemic = int((df["Complexity_score"] >= 0.7).sum()) if total else 0
    st.metric("Проблем (после фильтров)", total)
    st.metric("Системных (score ≥ 0.7)", systemic)
    st.metric("Средняя комплексность", f"{df['Complexity_score'].mean():.3f}" if total else "—")
    st.metric("P90 комплексности", f"{np.percentile(df['Complexity_score'], 90):.3f}" if total else "—")


def render_problem_table(df: pd.DataFrame, n: int = 30):
    cols = [
        "Проблема",
        "Тип_проблемы",
        "Частота_упоминаний",
        "Количество_субъектов",
        "Количество_действий",
        "Плотность_подграфа",
        "Complexity_score",
    ]
    st.dataframe(df.sort_values("Complexity_score", ascending=False).head(n)[cols], use_container_width=True, height=520)


def render_problem_card(df: pd.DataFrame, problem_name: str):
    row = df[df["Проблема"] == problem_name].sort_values("Complexity_score", ascending=False).head(1)
    if row.empty:
        st.info("Проблема не найдена в текущих фильтрах.")
        return
    r = row.iloc[0]
    left, right = st.columns([2, 1])
    with left:
        st.markdown(f"### {r['Проблема']}")
        st.write(f"**Тип:** {r['Тип_проблемы']}")
        st.write(f"**Complexity_score:** {r['Complexity_score']:.3f}")
        st.write(
            f"**Частота:** {int(r['Частота_упоминаний'])} · "
            f"**Субъекты:** {int(r['Количество_субъектов'])} · "
            f"**Действия:** {int(r['Количество_действий'])} · "
            f"**Плотность:** {float(r['Плотность_подграфа']):.3f}"
        )
        st.caption("Дальше сюда добавим: примеры обращений и объяснение факторов score.")
    with right:
        st.markdown("### Рекомендации (MVP)")
        for t in [
            "Если субъектов много → нужна координация нескольких служб.",
            "Если действий много → вероятно, проблема распадается на подпроцессы.",
            "Высокая плотность → тесно связанная система причин/следствий.",
        ]:
            st.write("• " + t)
